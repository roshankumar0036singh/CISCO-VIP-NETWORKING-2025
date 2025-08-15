
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import ipaddress

class CiscoConfigParser:
    def __init__(self):
        self.interface_types = {
            'gigabitethernet': 'GigabitEthernet',
            'fastethernet': 'FastEthernet', 
            'ethernet': 'Ethernet',
            'serial': 'Serial',
            'loopback': 'Loopback',
            'vlan': 'VLAN',
            'tunnel': 'Tunnel',
            'portchannel': 'Port-Channel'
        }

    def parse_config(self, config_text: str) -> dict:
        """Parse configuration with enhanced validation"""
        parsed = {
            "hostname": None,
            "device_type": "router",
            "interfaces": [],
            "vlans": [],
            "routing": {
                "ospf": {
                    "enabled": False,
                    "router_id": None,
                    "networks": [],
                    "passive_ints": [],
                    "reference_bandwidth": None,
                    "maximum_paths": 1,
                    "areas": {}
                },
                "bgp": {
                    "enabled": False,
                    "as_number": None,
                    "router_id": None,
                    "neighbors": [],
                    "networks": []
                },
                "static_routes": []
            },
            "spanning_tree": {
                "mode": None,
                "priorities": {},
                "root_bridge": False
            },
            "access_lists": [],
            "version": None,
            "gateway_of_last_resort": None,
            "mtu_settings": {},
            "load_balancing": {
                "enabled": False,
                "method": None
            }
        }

        curr_iface = None
        in_ospf = False
        in_bgp = False
        in_vlan = False
        current_vlan = None

        for line in config_text.splitlines():
            l = line.strip()
            if not l or l.startswith("!"):
                continue

            # Basic device info
            if l.lower().startswith("version "):
                parsed["version"] = self._safe_get(l.split(), 1)
                continue
                
            if l.lower().startswith("hostname "):
                parsed["hostname"] = self._safe_get(l.split(), 1)
                continue

            # Interface configuration
            if l.lower().startswith("interface "):
                iface_name = self._normalize_interface_name(l[10:].strip())
                curr_iface = {
                    "name": iface_name,
                    "ip_address": None,
                    "subnet_mask": None,
                    "description": "",
                    "bandwidth_kbps": self._default_bandwidth(iface_name),
                    "mtu": 1500,
                    "duplex": "auto",
                    "speed": "auto",
                    "status": "up",
                    "switchport_mode": None,
                    "access_vlan": None,
                    "trunk_vlans": [],
                    "native_vlan": None,
                    "spanning_tree_cost": None,
                    "load_interval": 300,
                    "traffic_shaping": None
                }
                parsed["interfaces"].append(curr_iface)
                continue

            if curr_iface:
                # IP configuration
                if m := re.match(r"ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)", l, re.I):
                    curr_iface["ip_address"] = m.group(1)
                    curr_iface["subnet_mask"] = m.group(2)
                    continue

                # Interface parameters
                if l.lower().startswith("description "):
                    curr_iface["description"] = l[12:].strip()
                if l.lower().startswith("bandwidth "):
                    try:
                        curr_iface["bandwidth_kbps"] = int(self._safe_get(l.split(), 1))
                    except (TypeError, ValueError):
                        pass
                if l.lower().startswith("mtu "):
                    try:
                        curr_iface["mtu"] = int(self._safe_get(l.split(), 1))
                    except (TypeError, ValueError):
                        pass
                if l.lower() == "shutdown":
                    curr_iface["status"] = "down"
                if l.lower() == "no shutdown":
                    curr_iface["status"] = "up"

            # OSPF Configuration
            if l.lower().startswith("router ospf"):
                parsed["routing"]["ospf"]["enabled"] = True
                in_ospf = True
                in_bgp = False
                continue

            if in_ospf:
                if l.lower().startswith("router-id "):
                    parsed["routing"]["ospf"]["router_id"] = self._safe_get(l.split(), 1)
                if l.lower().startswith("network "):
                    parts = l.split()
                    if len(parts) >= 5 and parts[3].lower() == "area":
                        parsed["routing"]["ospf"]["networks"].append({
                            "ip": parts[1],
                            "wildcard": parts[2], 
                            "area": parts[3]
                        })
                if l.lower().startswith("auto-cost reference-bandwidth "):
                    try:
                        parsed["routing"]["ospf"]["reference_bandwidth"] = int(self._safe_get(l.split(), 2))
                    except (TypeError, ValueError):
                        pass

            # BGP Configuration  
            if l.lower().startswith("router bgp"):
                parsed["routing"]["bgp"]["enabled"] = True
                try:
                    parsed["routing"]["bgp"]["as_number"] = int(self._safe_get(l.split(), 2))
                except (TypeError, ValueError):
                    pass
                in_bgp = True
                in_ospf = False
                continue

            if in_bgp:
                if l.lower().startswith("neighbor "):
                    parts = l.split()
                    if len(parts) >= 4 and parts[2].lower() == "remote-as":
                        parsed["routing"]["bgp"]["neighbors"].append({
                            "ip": parts[1],
                            "remote_as": parts[4]
                        })

            # VLAN Configuration
            if l.lower().startswith("vlan "):
                vlan_id = self._safe_get(l.split(), 1)
                if vlan_id and vlan_id.isdigit():
                    current_vlan = {
                        "id": int(vlan_id),
                        "name": f"VLAN{vlan_id}",
                        "state": "active"
                    }
                    parsed["vlans"].append(current_vlan)
                    in_vlan = True

            # Gateway of last resort
            if l.lower().startswith("ip route 0.0.0.0 0.0.0.0"):
                parsed["gateway_of_last_resort"] = self._safe_get(l.split(), 4)

        # Determine device type
        if any(iface.get("switchport_mode") for iface in parsed["interfaces"]):
            parsed["device_type"] = "switch"
        elif parsed["routing"]["ospf"]["enabled"] or parsed["routing"]["bgp"]["enabled"]:
            parsed["device_type"] = "router"
        else:
            parsed["device_type"] = "pc"

        return {"parsed_config": parsed}

    def _safe_get(self, lst: List, idx: int, default=None):
        return lst[idx] if len(lst) > idx else default

    def _normalize_interface_name(self, name: str) -> str:
        name = name.strip()
        for abbrev, full in self.interface_types.items():
            if name.lower().startswith(abbrev):
                return name.replace(name.split("/")[0], full, 1)
        return name

    def _default_bandwidth(self, iface_name: str) -> int:
        name = iface_name.lower()
        if "gigabitethernet" in name:
            return 1000000  # 1 Gbps
        elif "fastethernet" in name:
            return 100000   # 100 Mbps  
        elif "serial" in name:
            return 1544     # T1
        elif "loopback" in name:
            return 8000000  # 8 Gbps
        return 10000        # 10 Mbps default

    def parse_config_file(self, file_path: Path) -> dict:
        try:
            text = Path(file_path).read_text(encoding="utf-8")
            return self.parse_config(text)
        except Exception as e:
            return {"parsed_config": {"hostname": f"error_{file_path.stem}", "interfaces": [], "routing": {}}}
