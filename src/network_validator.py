
import ipaddress
import logging
from typing import Dict, List, Any, Set, Tuple
import networkx as nx

class NetworkValidator:
    def __init__(self, configs: Dict[str, Any], topology: nx.Graph):
        self.configs = configs
        self.topology = topology
        self.logger = logging.getLogger(__name__)
        
    def validate_all(self) -> Dict[str, List[str]]:
        """Run all validation checks"""
        issues = {
            "missing_components": self._check_missing_components(),
            "duplicate_ips": self._check_duplicate_ips(),
            "vlan_issues": self._check_vlan_consistency(),
            "gateway_issues": self._check_gateway_addresses(),
            "routing_recommendations": self._check_routing_protocol_recommendations(),
            "mtu_mismatches": self._check_mtu_mismatches(),
            "network_loops": self._detect_network_loops(),
            "aggregation_opportunities": self._find_aggregation_opportunities()
        }
        return issues
    
    def _check_missing_components(self) -> List[str]:
        """Detect missing switch configuration files for endpoints"""
        issues = []
        
        # Check for PCs without associated switch configs
        pc_devices = [d for d, cfg in self.configs.items() 
                     if cfg["parsed_config"].get("device_type") == "pc"]
        
        switches = [d for d, cfg in self.configs.items()
                   if cfg["parsed_config"].get("device_type") == "switch"]
        
        for pc in pc_devices:
            # Check if PC has a path to a switch
            connected_to_switch = False
            for switch in switches:
                if self.topology.has_edge(pc, switch):
                    connected_to_switch = True
                    break
            
            if not connected_to_switch:
                issues.append(f"PC {pc} appears to be missing associated switch configuration")
        
        return issues
    
    def _check_duplicate_ips(self) -> List[str]:
        """Check for duplicate IP addresses within same VLAN/subnet"""
        issues = []
        ip_vlan_map = {}
        
        for device, cfg in self.configs.items():
            for iface in cfg["parsed_config"]["interfaces"]:
                ip = iface.get("ip_address")
                vlan = iface.get("access_vlan", "default")
                
                if ip and ip != "dhcp":
                    key = f"{ip}_{vlan}"
                    if key in ip_vlan_map:
                        issues.append(f"Duplicate IP {ip} in VLAN {vlan}: devices {ip_vlan_map[key]} and {device}")
                    else:
                        ip_vlan_map[key] = device
        
        return issues
    
    def _check_vlan_consistency(self) -> List[str]:
        """Check for incorrect VLAN labels and consistency"""
        issues = []
        vlan_definitions = {}
        
        for device, cfg in self.configs.items():
            # Collect VLAN definitions
            for vlan in cfg["parsed_config"].get("vlans", []):
                vlan_id = vlan.get("id")
                vlan_name = vlan.get("name")
                
                if vlan_id in vlan_definitions:
                    if vlan_definitions[vlan_id] != vlan_name:
                        issues.append(f"VLAN {vlan_id} has inconsistent names: '{vlan_definitions[vlan_id]}' vs '{vlan_name}'")
                else:
                    vlan_definitions[vlan_id] = vlan_name
            
            # Check interface VLAN assignments
            for iface in cfg["parsed_config"]["interfaces"]:
                access_vlan = iface.get("access_vlan")
                if access_vlan and access_vlan not in vlan_definitions:
                    issues.append(f"Interface {iface['name']} on {device} references undefined VLAN {access_vlan}")
        
        return issues
    
    def _check_gateway_addresses(self) -> List[str]:
        """Check for incorrect gateway addresses on routers"""
        issues = []
        
        for device, cfg in self.configs.items():
            if cfg["parsed_config"].get("device_type") == "router":
                gateway = cfg["parsed_config"].get("gateway_of_last_resort")
                device_subnets = []
                
                # Get all subnets this router is connected to
                for iface in cfg["parsed_config"]["interfaces"]:
                    ip = iface.get("ip_address")
                    mask = iface.get("subnet_mask")
                    if ip and mask and ip != "dhcp":
                        try:
                            network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                            device_subnets.append(network)
                        except:
                            pass
                
                # Check if gateway is reachable
                if gateway:
                    try:
                        gateway_ip = ipaddress.IPv4Address(gateway)
                        gateway_reachable = any(gateway_ip in subnet for subnet in device_subnets)
                        
                        if not gateway_reachable:
                            issues.append(f"Router {device} has unreachable gateway {gateway}")
                    except:
                        issues.append(f"Router {device} has invalid gateway address format: {gateway}")
        
        return issues
    
    def _check_routing_protocol_recommendations(self) -> List[str]:
        """Recommend BGP vs OSPF based on network characteristics"""
        recommendations = []
        
        # Count AS numbers and network size
        as_numbers = set()
        total_routers = 0
        
        for device, cfg in self.configs.items():
            if cfg["parsed_config"].get("device_type") == "router":
                total_routers += 1
                bgp_as = cfg["parsed_config"]["routing"]["bgp"].get("as_number")
                if bgp_as:
                    as_numbers.add(bgp_as)
        
        # Recommendations based on network characteristics
        if len(as_numbers) > 1:
            # Multiple AS numbers - BGP recommended
            ospf_routers = [d for d, cfg in self.configs.items() 
                          if cfg["parsed_config"]["routing"]["ospf"]["enabled"]]
            if ospf_routers:
                recommendations.append("Consider using BGP instead of OSPF for inter-AS routing between different autonomous systems")
        
        if total_routers > 50:
            recommendations.append("Large network detected - consider BGP for better scalability")
        
        return recommendations
    
    def _check_mtu_mismatches(self) -> List[str]:
        """Check for MTU mismatches on connected interfaces"""
        issues = []
        
        for u, v in self.topology.edges():
            u_config = self.configs.get(u, {}).get("parsed_config", {})
            v_config = self.configs.get(v, {}).get("parsed_config", {})
            
            u_interfaces = u_config.get("interfaces", [])
            v_interfaces = v_config.get("interfaces", [])
            
            # Find connecting interfaces (simplified)
            for u_iface in u_interfaces:
                for v_iface in v_interfaces:
                    u_mtu = u_iface.get("mtu", 1500)
                    v_mtu = v_iface.get("mtu", 1500)
                    
                    if abs(u_mtu - v_mtu) > 0:
                        issues.append(f"MTU mismatch between {u}:{u_iface['name']} (MTU {u_mtu}) and {v}:{v_iface['name']} (MTU {v_mtu})")
        
        return issues
    
    def _detect_network_loops(self) -> List[str]:
        """Detect potential network loops"""
        issues = []
        
        # Check for cycles in the topology
        try:
            cycles = list(nx.simple_cycles(self.topology))
            for cycle in cycles[:5]:  # Limit to first 5 cycles
                if len(cycle) > 2:
                    issues.append(f"Potential network loop detected: {' -> '.join(cycle)} -> {cycle[0]}")
        except:
            # For undirected graphs, check for redundant paths that might cause loops
            bridges = list(nx.bridges(self.topology))
            total_edges = self.topology.number_of_edges()
            bridge_count = len(bridges)
            
            if bridge_count < total_edges - 1:
                issues.append(f"Network has {total_edges - bridge_count - 1} potential loops - ensure STP is configured")
        
        return issues
    
    def _find_aggregation_opportunities(self) -> List[str]:
        """Find opportunities to optimize network by reducing nodes"""
        opportunities = []
        
        # Find nodes that could be aggregated (simple heuristic)
        for node in self.topology.nodes():
            neighbors = list(self.topology.neighbors(node))
            node_config = self.configs.get(node, {}).get("parsed_config", {})
            
            # If a switch has only one connection and low utilization, consider aggregation
            if (node_config.get("device_type") == "switch" and 
                len(neighbors) <= 2):
                opportunities.append(f"Switch {node} with {len(neighbors)} connections could potentially be aggregated")
            
            # If router has minimal routing and few connections
            if (node_config.get("device_type") == "router" and 
                len(neighbors) <= 2 and
                not node_config["routing"]["ospf"]["enabled"] and
                not node_config["routing"]["bgp"]["enabled"]):
                opportunities.append(f"Router {node} with minimal routing could be simplified or aggregated")
        
        return opportunities
