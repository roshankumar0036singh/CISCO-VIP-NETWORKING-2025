

import ipaddress
import re
import networkx as nx
import logging
from typing import Dict, List, Any, Optional


class topology_builder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.icon_map = {
            "router": "wifi-router.png",
            "switch": "hub.png",
            "pc": "monitor.png",
            "laptop": "laptop.png"
        }

    def build_from_configs(self, configs: Dict[str, Dict]) -> nx.Graph:
        topo = nx.Graph()
        self._add_device_nodes(topo, configs)
        self._discover_ip_links(topo, configs)
        self._discover_ospf_links(topo, configs)
        self._discover_bgp_links(topo, configs)
        self._discover_desc_links(topo, configs)
        self._calculate_link_metrics(topo, configs)
        return topo

    def _add_device_nodes(self, topo: nx.Graph, configs: Dict[str, Dict]):
        for key, cfg in configs.items():
            p = cfg["parsed_config"]
            host = p.get("hostname", key)
            dt = p.get("device_type", "router").lower()
            label, icon = self._vip_label_icon(key, host, dt)
            bandwidth_summary = self._calculate_device_bandwidth(p)

            iface_details = []
            for iface in p.get("interfaces", []):
                ip = iface.get("ip_address") or "-"
                mask = iface.get("subnet_mask") or "-"
                desc = iface.get("description") or ""
                bw = iface.get("bandwidth_kbps", 0)
                status = iface.get("status", "unknown")
                duplex = iface.get("duplex") or "-"
                speed = iface.get("speed") or "-"
                detail = (
                    f"{iface['name']}: {ip}/{mask} Status: {status}, BW: {bw/1000:.1f} Mbps, "
                    f"Duplex: {duplex}, Speed: {speed}, Desc: {desc}"
                )
                iface_details.append(detail)

            ospf = p.get("routing", {}).get("ospf", {})
            ospf_info = ""
            if ospf.get("enabled"):
                ospf_info = (
                    f"<br>OSPF Config - Router ID: {ospf.get('router_id', 'n/a')}, "
                    f"Networks: {len(ospf.get('networks', []))}, "
                    f"Ref BW: {ospf.get('reference_bandwidth', 'default')}, "
                    f"Max Paths: {ospf.get('maximum_paths', 1)}<br>"
                )

            bgp = p.get("routing", {}).get("bgp", {})
            bgp_info = ""
            if bgp.get("enabled"):
                bgp_info = (
                    f"<br>BGP Config - AS: {bgp.get('as_number', 'n/a')}, "
                    f"Router ID: {bgp.get('router_id', 'n/a')}, "
                    f"Neighbors: {len(bgp.get('neighbors', []))}<br>"
                )

            vlan_info = ""
            vlan_ids = []
            if p.get("vlans"):
                for v in p.get("vlans", [])[:5]:
                    vlan_ids.append(str(v.get("id") or v.get("vlan_id") or "?"))
                if len(p.get("vlans", [])) > 5:
                    vlan_ids.append("...")
                vlan_info = "<br>VLANs: " + ", ".join(vlan_ids)

            title = (
                f"<b>Hostname:</b> {host}<br>"
                f"<b>Device Type:</b> {dt.title()}<br>"
                f"<b>Total Bandwidth:</b> {bandwidth_summary['total_mbps']:.1f} Mbps<br>"
                f"<b>Interfaces:</b> {len(p.get('interfaces', []))}<br>"
                + "<br>".join(iface_details)
                + ospf_info + bgp_info + vlan_info
            )

            topo.add_node(
                key,
                hostname=host,
                device_type=dt,
                label=label,
                device_icon=icon,
                title=title,
                bandwidth_summary=bandwidth_summary,
                version=p.get("version"),
            )

    def _calculate_device_bandwidth(self, parsed_config):
        interfaces = parsed_config.get("interfaces", [])
        total_bw = sum(iface.get("bandwidth_kbps", 0) for iface in interfaces if iface.get("status") == "up")
        active = len([iface for iface in interfaces if iface.get("status") == "up"])
        return {
            "total_kbps": total_bw,
            "total_mbps": total_bw / 1000,
            "active_count": active,
            "total_count": len(interfaces),
        }

    def _vip_label_icon(self, key, host, dt):
        key = key.lower()
        host = (host or "").lower()
        if "laptop" in key or "laptop" in host:
            return "laptop", "laptop"
        if key.startswith("pc") or "pc" in key:
            return "pc", "pc"
        if dt == "switch":
            if "1" in key:
                return "s1", "switch"
            if "2" in key:
                return "s2", "switch"
            if "3" in key:
                return "s3", "switch"
            return "switch", "switch"
        if dt == "router" or key.startswith("r"):
            return "router", "router"
        return "pc", "pc"

    def _discover_ip_links(self, topo, configs):
        subnet_map = {}
        for dev, cfg in configs.items():
            for iface in cfg["parsed_config"].get("interfaces", []):
                ip = iface.get("ip_address")
                mask = iface.get("subnet_mask")
                is_host = iface.get("is_host_segment", False)
                status = iface.get("status", "up")
                if not ip or ip.lower() == "dhcp" or not mask or status == "down":
                    continue
                try:
                    net = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
                except Exception:
                    continue
                subnet_key = str(net)
                subnet_map.setdefault(subnet_key, []).append((dev, iface, is_host))

        for subnet, devices in subnet_map.items():
            if len(devices) < 2:
                continue
            for i in range(len(devices)):
                for j in range(i + 1, len(devices)):
                    dev1, iface1, is_host1 = devices[i]
                    dev2, iface2, is_host2 = devices[j]
                    if is_host1 or is_host2:
                        continue
                    if not topo.has_edge(dev1, dev2):
                        bw = min(iface1.get("bandwidth_kbps", 0), iface2.get("bandwidth_kbps", 0))
                        cost = self._calculate_ospf_cost(bw)
                        title = f"Subnet: {subnet} between {iface1['name']} and {iface2['name']} - Bandwidth: {bw / 1000} Mbps, Cost: {cost}"
                        topo.add_edge(
                            dev1,
                            dev2,
                            link_type="subnet",
                            subnet=subnet,
                            bandwidth_kbps=bw,
                            bandwidth_mbps=bw / 1000,
                            cost=cost,
                            title=title,
                        )

    def _calculate_ospf_cost(self, bandwidth_kbps):
        reference_bw = 100000  # 100 Mbps in kbps
        if not bandwidth_kbps or bandwidth_kbps <= 0:
            return 65535
        cost = max(1, min(reference_bw // bandwidth_kbps, 65535))
        return cost

    def _discover_ospf_links(self, topo, configs):
        ospf_devices = [dev for dev, cfg in configs.items() if cfg["parsed_config"].get("routing", {}).get("ospf", {}).get("enabled", False)]
        for i in range(len(ospf_devices)):
            for j in range(i + 1, len(ospf_devices)):
                dev1 = ospf_devices[i]
                dev2 = ospf_devices[j]
                if topo.has_edge(dev1, dev2):
                    continue
                if self._have_shared_subnet(configs[dev1], configs[dev2]):
                    topo.add_edge(dev1, dev2, link_type="ospf", title="OSPF Link", cost=1, area="0")

    def _have_shared_subnet(self, cfg1, cfg2):
        nets1 = []
        nets2 = []
        try:
            for iface in cfg1["parsed_config"].get("interfaces", []):
                nets1.append(ipaddress.ip_network(f"{iface.get('ip_address')}/{iface.get('subnet_mask')}", strict=False))
            for iface in cfg2["parsed_config"].get("interfaces", []):
                nets2.append(ipaddress.ip_network(f"{iface.get('ip_address')}/{iface.get('subnet_mask')}", strict=False))
        except Exception:
            return False

        for net1 in nets1:
            for net2 in nets2:
                if net1.overlaps(net2):
                    return True
        return False

    def _discover_bgp_links(self, topo, configs):
        for dev, cfg in configs.items():
            bgp_cfg = cfg["parsed_config"].get("routing", {}).get("bgp", {})
            if not bgp_cfg.get("enabled", False):
                continue
            local_as = bgp_cfg.get("as_number")
            for nbr in bgp_cfg.get("neighbors", []):
                peer_ip = nbr.get("ip")
                remote_as = nbr.get("remote_as")
                for other_dev, other_cfg in configs.items():
                    if other_dev == dev:
                        continue
                    for iface in other_cfg["parsed_config"].get("interfaces", []):
                        if iface.get("ip_address") == peer_ip:
                            if not topo.has_edge(dev, other_dev):
                                topo.add_edge(
                                    dev,
                                    other_dev,
                                    link_type="bgp",
                                    title=f"BGP Link AS {local_as}→{remote_as}",
                                    peer_ip=peer_ip,
                                    local_as=local_as,
                                    remote_as=remote_as,
                                )

    def _discover_desc_links(self, topo, configs):
        patterns = [
            re.compile(r"\b(?:to|connected to|link to)\s+(\w+)", re.IGNORECASE),
            re.compile(r"\b(\w+)\s+(?:link|connection|interface)", re.IGNORECASE),
        ]
        for dev, cfg in configs.items():
            for iface in cfg["parsed_config"].get("interfaces", []):
                desc = iface.get("description", "")
                if not desc:
                    continue
                for pat in patterns:
                    m = pat.search(desc)
                    if m:
                        peer = m.group(1)
                        if peer in configs and not topo.has_edge(dev, peer):
                            topo.add_edge(dev, peer, link_type="desc", title=f"Desc Link: {iface['name']}→{peer}")
                            break

    def _calculate_link_metrics(self, topo, configs):
        import random
        for u, v, data in topo.edges(data=True):
            # Calculate alternative path count
            try:
                temp_graph = topo.copy()
                temp_graph.remove_edge(u, v)
                alt_paths = list(nx.all_simple_paths(temp_graph, u, v, cutoff=5))
                data["alternative_paths"] = len(alt_paths)
                data["is_critical"] = len(alt_paths) == 0
            except Exception:
                data["alternative_paths"] = 0
                data["is_critical"] = True

            # Simulate utilization
            bw = data.get("bandwidth_mbps", 0)
            link_type = data.get("link_type", "unknown")
            if link_type == "ospf" and bw >= 1000:
                util = random.uniform(20, 60)
            elif link_type == "subnet" and bw <= 100:
                util = random.uniform(10, 40)
            else:
                util = random.uniform(15, 50)
            data["utilization_percent"] = round(util, 1)

            # Classify utilization
            if util < 30:
                status = "low"
            elif util < 70:
                status = "normal"
            elif util < 90:
                status = "high"
            else:
                status = "critical"
            data["utilization_status"] = status

            # Determine priority
            dtype_u = configs.get(u, {}).get("parsed_config", {}).get("device_type", "unknown")
            dtype_v = configs.get(v, {}).get("parsed_config", {}).get("device_type", "unknown")

            if dtype_u == "router" and dtype_v == "router":
                priority = "critical" if bw >= 1000 else "high"
            elif "router" in (dtype_u, dtype_v) and "switch" in (dtype_u, dtype_v):
                priority = "high"
            elif dtype_u == "switch" and dtype_v == "switch":
                priority = "medium"
            else:
                priority = "low"
            data["priority"] = priority

