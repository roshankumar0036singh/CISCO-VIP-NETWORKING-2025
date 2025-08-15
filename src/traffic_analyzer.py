
import logging
from typing import Dict, List, Any, Tuple
import networkx as nx
import random

class TrafficAnalyzer:
    def __init__(self, configs: Dict[str, Any], topology: nx.Graph):
        self.configs = configs
        self.topology = topology
        self.logger = logging.getLogger(__name__)
        
        # Application traffic profiles
        self.app_profiles = {
            "web_server": {"peak_mbps": 100, "regular_mbps": 20, "priority": "medium"},
            "database": {"peak_mbps": 500, "regular_mbps": 50, "priority": "high"}, 
            "file_server": {"peak_mbps": 1000, "regular_mbps": 100, "priority": "medium"},
            "video_streaming": {"peak_mbps": 50, "regular_mbps": 25, "priority": "low"},
            "voip": {"peak_mbps": 10, "regular_mbps": 5, "priority": "critical"}
        }
    
    def analyze_capacity(self) -> Dict[str, Any]:
        """Analyze network capacity vs traffic load"""
        results = {
            "link_utilization": {},
            "bottlenecks": [],
            "load_balancing_recommendations": [],
            "endpoint_traffic": {},
            "capacity_warnings": []
        }
        
        # Simulate traffic loads for endpoints
        endpoint_loads = self._simulate_endpoint_traffic()
        results["endpoint_traffic"] = endpoint_loads
        
        # Calculate link utilization
        link_utilization = self._calculate_link_utilization(endpoint_loads)
        results["link_utilization"] = link_utilization
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(link_utilization)
        results["bottlenecks"] = bottlenecks
        
        # Generate load balancing recommendations
        recommendations = self._generate_load_balancing_recommendations(bottlenecks)
        results["load_balancing_recommendations"] = recommendations
        
        return results
    
    def _simulate_endpoint_traffic(self) -> Dict[str, Dict[str, float]]:
        """Simulate traffic loads for different endpoint types"""
        endpoint_traffic = {}
        
        for device, config in self.configs.items():
            device_type = config["parsed_config"].get("device_type", "unknown")
            
            if device_type == "pc":
                # Simulate different application loads
                apps = random.sample(list(self.app_profiles.keys()), random.randint(1, 3))
                total_peak = 0
                total_regular = 0
                
                for app in apps:
                    profile = self.app_profiles[app]
                    total_peak += profile["peak_mbps"] * random.uniform(0.7, 1.0)
                    total_regular += profile["regular_mbps"] * random.uniform(0.8, 1.0)
                
                endpoint_traffic[device] = {
                    "peak_load_mbps": total_peak,
                    "regular_load_mbps": total_regular,
                    "applications": apps
                }
            
            elif device_type in ["router", "switch"]:
                # Infrastructure devices - calculate based on connected endpoints
                endpoint_traffic[device] = {
                    "peak_load_mbps": 0,
                    "regular_load_mbps": 0,
                    "applications": ["infrastructure"]
                }
        
        return endpoint_traffic
    
    def _calculate_link_utilization(self, endpoint_loads: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Calculate utilization for each link based on traffic patterns"""
        link_utilization = {}
        
        for u, v, edge_data in self.topology.edges(data=True):
            # Get link capacity
            link_capacity = edge_data.get("bandwidth_mbps", 100)  # Default 100 Mbps
            
            # Estimate traffic crossing this link
            estimated_traffic = self._estimate_link_traffic(u, v, endpoint_loads)
            
            utilization_regular = (estimated_traffic["regular"] / link_capacity) * 100
            utilization_peak = (estimated_traffic["peak"] / link_capacity) * 100
            
            link_utilization[f"{u}-{v}"] = {
                "capacity_mbps": link_capacity,
                "regular_traffic_mbps": estimated_traffic["regular"],
                "peak_traffic_mbps": estimated_traffic["peak"], 
                "regular_utilization_percent": min(utilization_regular, 100),
                "peak_utilization_percent": min(utilization_peak, 100),
                "link_type": edge_data.get("link_type", "unknown")
            }
        
        return link_utilization
    
    def _estimate_link_traffic(self, u: str, v: str, endpoint_loads: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Estimate traffic crossing a specific link"""
        # Simplified traffic estimation based on shortest paths
        total_regular = 0
        total_peak = 0
        
        # Find all endpoint pairs that might use this link
        endpoints = [d for d in self.configs.keys() 
                    if self.configs[d]["parsed_config"].get("device_type") == "pc"]
        
        for src in endpoints:
            for dst in endpoints:
                if src != dst:
                    try:
                        path = nx.shortest_path(self.topology, src, dst)
                        # Check if this link is in the path
                        for i in range(len(path) - 1):
                            if (path[i] == u and path[i+1] == v) or (path[i] == v and path[i+1] == u):
                                # This link carries traffic from src to dst
                                src_load = endpoint_loads.get(src, {})
                                # Assume 10% of endpoint traffic goes to each other endpoint
                                total_regular += src_load.get("regular_load_mbps", 0) * 0.1
                                total_peak += src_load.get("peak_load_mbps", 0) * 0.1
                                break
                    except nx.NetworkXNoPath:
                        pass
        
        return {"regular": total_regular, "peak": total_peak}
    
    def _identify_bottlenecks(self, link_utilization: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Identify network bottlenecks"""
        bottlenecks = []
        
        for link, util_data in link_utilization.items():
            peak_util = util_data["peak_utilization_percent"]
            regular_util = util_data["regular_utilization_percent"]
            
            if peak_util > 80:  # High utilization threshold
                bottlenecks.append({
                    "link": link,
                    "peak_utilization": peak_util,
                    "capacity_mbps": util_data["capacity_mbps"],
                    "severity": "critical" if peak_util > 95 else "high",
                    "recommendation": f"Link {link} is heavily utilized ({peak_util:.1f}%)"
                })
            elif regular_util > 60:
                bottlenecks.append({
                    "link": link,
                    "regular_utilization": regular_util,
                    "capacity_mbps": util_data["capacity_mbps"], 
                    "severity": "medium",
                    "recommendation": f"Link {link} shows consistent high utilization ({regular_util:.1f}%)"
                })
        
        return bottlenecks
    
    def _generate_load_balancing_recommendations(self, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Generate load balancing strategy recommendations"""
        recommendations = []
        
        for bottleneck in bottlenecks:
            link = bottleneck["link"]
            u, v = link.split("-")
            
            # Find alternative paths
            try:
                # Remove the bottleneck link temporarily
                if self.topology.has_edge(u, v):
                    self.topology.remove_edge(u, v)
                    
                    # Check if alternative paths exist
                    if nx.has_path(self.topology, u, v):
                        alt_paths = list(nx.all_simple_paths(self.topology, u, v, cutoff=6))
                        if len(alt_paths) > 0:
                            recommendations.append(
                                f"Activate alternative paths for {link} to distribute load. "
                                f"Found {len(alt_paths)} alternative routes."
                            )
                            recommendations.append(
                                f"Consider implementing ECMP (Equal-Cost Multi-Path) routing for {link}"
                            )
                        else:
                            recommendations.append(
                                f"Upgrade bandwidth capacity for critical link {link} - no alternative paths available"
                            )
                    
                    # Restore the link
                    self.topology.add_edge(u, v)
                    
            except Exception:
                recommendations.append(f"Investigate load balancing options for {link}")
            
            # Priority-based recommendations
            if bottleneck["severity"] == "critical":
                recommendations.append(
                    f"URGENT: Implement traffic shaping on {link} to prioritize critical applications"
                )
                recommendations.append(
                    f"Consider moving lower-priority traffic to secondary paths for {link}"
                )
        
        return recommendations
