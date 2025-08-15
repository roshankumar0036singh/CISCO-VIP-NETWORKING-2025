

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import networkx as nx
import random


class Day2NetworkTester:
    """Comprehensive Day 2 testing for network topology validation"""

    def __init__(self, topology_graph, parsed_configs):
        self.topology = topology_graph
        self.configs = parsed_configs
        self.logger = logging.getLogger(__name__)
        self.test_results: Dict[str, Any] = {}
        self.baseline_metrics: Dict[str, Any] = {}

    def _check_best_practices(self) -> List[str]:
        """Check configuration best practices; no arguments expected."""
        self.logger.info("Checking configuration best practices")
        issues: List[str] = []

        # Duplicate IP detection
        ip_registry = set()
        for device, cfg in self.configs.items():
            for iface in cfg["parsed_config"]["interfaces"]:
                ip = iface.get("ip_address")
                if ip and ip != "dhcp":
                    if ip in ip_registry:
                        issues.append(f"Duplicate IP address detected: {ip} on {device}")
                    else:
                        ip_registry.add(ip)

        # TODO: VLAN label validation, default gateway sanity, MTU mismatch, loop detection, etc.
        return issues

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Execute all Day 2 testing scenarios"""

        connectivity = self._run_connectivity_tests()
        performance = self._run_performance_tests()
        config_validation = self._validate_configurations()
        redundancy = self._test_redundancy()
        security = self._validate_security()
        protocols = self._validate_protocols()
        capacity = self._analyze_capacity()
        baseline = self._compare_baseline()

        # Compose suite (kept keys identical to your current structure)
        test_suite = {
            "connectivity_tests": connectivity,
            "performance_tests": performance,
            "configuration_validation": config_validation,
            "redundancy_tests": redundancy,
            "security_validation": security,
            "protocol_validation": protocols,
            "capacity_planning": capacity,
            "baseline_comparison": baseline,
        }

        # Generate comprehensive test report
        report = self._generate_test_report(test_suite)
        return report

    # ---------------- Connectivity ----------------

    def _run_connectivity_tests(self) -> Dict[str, Any]:
        """Test network connectivity between all devices"""
        connectivity_results: Dict[str, Any] = {
            "reachability_matrix": {},
            "latency_measurements": {},
            "packet_loss_rates": {},
            "path_analysis": {},
        }

        devices = list(self.topology.nodes())
        for src in devices:
            connectivity_results["reachability_matrix"][src] = {}
            connectivity_results["latency_measurements"][src] = {}
            connectivity_results["packet_loss_rates"][src] = {}
            for dst in devices:
                if src == dst:
                    continue
                reachable = self._test_device_connectivity(src, dst)
                latency = self._measure_latency(src, dst)
                loss_rate = self._measure_packet_loss(src, dst)
                connectivity_results["reachability_matrix"][src][dst] = reachable
                connectivity_results["latency_measurements"][src][dst] = latency
                connectivity_results["packet_loss_rates"][src][dst] = loss_rate

        return connectivity_results

    def _test_device_connectivity(self, source: str, destination: str) -> bool:
        """Simulate connectivity test between two devices"""
        try:
            path = nx.shortest_path(self.topology, source, destination)
            return len(path) > 1
        except Exception:
            return False

    def _measure_latency(self, source: str, destination: str) -> float:
        """Simulate latency measurement"""
        base_latency = 1.0  # 1ms base
        if self._test_device_connectivity(source, destination):
            try:
                path_length = len(nx.shortest_path(self.topology, source, destination))
                return base_latency + (path_length - 1) * random.uniform(0.2, 1.5)
            except Exception:
                return 999.0
        return 999.0

    def _measure_packet_loss(self, source: str, destination: str) -> float:
        """Simulate packet loss measurement"""
        if self._test_device_connectivity(source, destination):
            return random.uniform(0.0, 0.1)  # 0–0.1%
        return 100.0  # unreachable

    # ---------------- Performance ----------------

    def _run_performance_tests(self) -> Dict[str, Any]:
        """Test network performance metrics"""
        performance_metrics: Dict[str, Any] = {
            "throughput_tests": {},
            "bandwidth_utilization": {},
            "interface_statistics": {},
            "cpu_memory_usage": {},
            "queue_depths": {},
        }

        for device in self.topology.nodes():
            performance_metrics["throughput_tests"][device] = self._measure_throughput(device)
            performance_metrics["bandwidth_utilization"][device] = self._measure_bandwidth_util(device)
            performance_metrics["interface_statistics"][device] = self._collect_interface_stats(device)
            performance_metrics["cpu_memory_usage"][device] = self._collect_system_stats(device)
            performance_metrics["queue_depths"][device] = self._measure_queue_depths(device)

        return performance_metrics

    def _measure_throughput(self, device: str) -> Dict[str, float]:
        """Simulate throughput measurements"""
        device_data = self.topology.nodes[device]
        device_type = device_data.get("device_type", "unknown")
        base = {
            "router": 1000.0,   # 1 Gbps
            "switch": 10000.0,  # 10 Gbps
            "pc": 100.0,        # 100 Mbps
            "laptop": 100.0,    # 100 Mbps
        }
        max_tp = base.get(device_type, 100.0)
        cur_tp = max_tp * random.uniform(0.3, 0.8)
        return {
            "max_throughput_mbps": max_tp,
            "current_throughput_mbps": cur_tp,
            "utilization_percent": (cur_tp / max_tp) * 100.0,
        }

    def _measure_bandwidth_util(self, device: str) -> Dict[str, float]:
        """Simulate bandwidth utilization"""
        return {
            "inbound_util_percent": random.uniform(20, 80),
            "outbound_util_percent": random.uniform(20, 80),
            "peak_util_percent": random.uniform(80, 95),
        }

    def _collect_interface_stats(self, device: str) -> Dict[str, Any]:
        """Simulate interface statistics collection"""
        config = self.configs.get(device, {}).get("parsed_config", {})
        interfaces = config.get("interfaces", [])
        stats: Dict[str, Any] = {}
        for iface in interfaces:
            stats[iface["name"]] = {
                "rx_packets": random.randint(1_000_000, 10_000_000),
                "tx_packets": random.randint(1_000_000, 10_000_000),
                "rx_bytes": random.randint(100_000_000, 1_000_000_000),
                "tx_bytes": random.randint(100_000_000, 1_000_000_000),
                "rx_errors": random.randint(0, 100),
                "tx_errors": random.randint(0, 100),
                "status": "up" if random.random() > 0.1 else "down",
            }
        return stats

    def _collect_system_stats(self, device: str) -> Dict[str, float]:
        """Simulate system resource statistics"""
        return {
            "cpu_utilization_percent": random.uniform(10, 80),
            "memory_utilization_percent": random.uniform(30, 70),
            "temperature_celsius": random.uniform(35, 65),
            "power_consumption_watts": random.uniform(50, 200),
        }

    def _measure_queue_depths(self, device: str) -> Dict[str, int]:
        """Simulate queue depth measurements"""
        return {
            "input_queue_depth": random.randint(0, 100),
            "output_queue_depth": random.randint(0, 100),
            "priority_queue_depth": random.randint(0, 50),
        }

    # ---------------- Validation ----------------

    def _validate_configurations(self) -> Dict[str, Any]:
        """Validate device configurations against best practices"""
        validation_results: Dict[str, Any] = {
            "configuration_compliance": {},
            "security_settings": {},
            "routing_consistency": {},
            "vlan_consistency": {},  # placeholder for future VLAN checks
            "best_practices_check": {},
        }

        for device, config in self.configs.items():
            parsed = config["parsed_config"]
            validation_results["configuration_compliance"][device] = self._check_config_compliance(parsed)
            validation_results["security_settings"][device] = self._validate_security_config(parsed)
            validation_results["routing_consistency"][device] = self._check_routing_consistency(parsed)
            # IMPORTANT: call with NO arguments (fix for your error)
            validation_results["best_practices_check"][device] = self._check_best_practices()

        return validation_results

    def _check_config_compliance(self, config: Dict) -> Dict[str, bool]:
        """Check configuration compliance (basic)"""
        return {
            "hostname_configured": bool(config.get("hostname")),
            "interfaces_configured": len(config.get("interfaces", [])) > 0,
            "routing_configured": bool(config.get("routing")),
            "security_configured": True,  # simplified
        }

    def _validate_security_config(self, config: Dict) -> Dict[str, bool]:
        """Validate security configuration (basic placeholders)"""
        return {
            "access_lists_configured": True,
            "authentication_enabled": True,
            "encryption_enabled": True,
            "logging_configured": True,
        }

    def _check_routing_consistency(self, config: Dict) -> Dict[str, Any]:
        """Check routing configuration consistency (basic flags)"""
        routing = config.get("routing", {})
        return {
            "ospf_consistent": routing.get("ospf", {}).get("enabled", False),
            "bgp_consistent": routing.get("bgp", {}).get("enabled", False),
            "static_routes_valid": True,
        }

    # ---------------- Redundancy ----------------

    def _test_redundancy(self) -> Dict[str, Any]:
        """Test network redundancy and failover capabilities (simulated)"""
        redundancy_results: Dict[str, Any] = {
            "path_redundancy": {},
            "failover_tests": {},
            "recovery_times": {},
            "backup_paths": {},
        }

        devices = list(self.topology.nodes())
        for i in range(len(devices)):
            for j in range(i + 1, len(devices)):
                src, dst = devices[i], devices[j]
                primary, backups = self._find_paths(src, dst)
                redundancy_results["path_redundancy"][f"{src}-{dst}"] = {
                    "primary_path": primary,
                    "backup_paths": backups,
                    "path_count": (1 if primary else 0) + len(backups),
                }

        # Simulated failover for bridges/critical edges
        for (u, v) in self._identify_critical_links():
            redundancy_results["failover_tests"][f"{u}-{v}"] = self._simulate_link_failure((u, v))

        return redundancy_results

    def _find_paths(self, src: str, dst: str) -> (List[str], List[List[str]]): # type: ignore
        """Find primary and backup paths (simulated via k-shortest)"""
        try:
            primary = nx.shortest_path(self.topology, src, dst)
        except Exception:
            return [], []
        # simulate up to 2 alternative simple paths
        backups: List[List[str]] = []
        try:
            all_paths = list(nx.all_simple_paths(self.topology, src, dst, cutoff=6))
            for p in all_paths:
                if p != primary and len(backups) < 2:
                    backups.append(p)
        except Exception:
            pass
        return primary, backups

    def _identify_critical_links(self) -> List[tuple]:
        """Identify potential critical links via bridge detection"""
        crit = []
        try:
            bridges = list(nx.bridges(self.topology))
            crit.extend(bridges)
        except Exception:
            pass
        return crit

    def _simulate_link_failure(self, link: tuple) -> Dict[str, Any]:
        """Simulate a single link failure and report connectivity impact"""
        u, v = link
        impact = {"link": f"{u}-{v}", "affected_pairs": 0}
        if not self.topology.has_edge(u, v):
            return impact
        try:
            self.topology.remove_edge(u, v)
            # Count disconnected pairs quickly (sampled)
            nodes = list(self.topology.nodes())
            samples = 0
            disconnected = 0
            for i in range(min(10, len(nodes))):
                for j in range(i + 1, min(i + 6, len(nodes))):
                    samples += 1
                    src, dst = nodes[i], nodes[j]
                    if not nx.has_path(self.topology, src, dst):
                        disconnected += 1
            impact["affected_pairs"] = disconnected
        finally:
            # restore
            self.topology.add_edge(u, v)
        return impact

    # ---------------- Security ----------------

    def _validate_security(self) -> Dict[str, Any]:
        """Validate network security configurations (simulated)"""
        security_results: Dict[str, Any] = {
            "access_control": {},
            "authentication": {},
            "encryption": {},
            "vulnerability_assessment": {},
        }

        for device, config in self.configs.items():
            parsed = config["parsed_config"]
            device_type = parsed.get("device_type", "unknown")
            security_results["access_control"][device] = {"acl_ok": True}
            security_results["authentication"][device] = {"aaa_ok": True}
            security_results["encryption"][device] = {"ssh_ok": True}
            security_results["vulnerability_assessment"][device] = {"risk": "low" if device_type != "pc" else "medium"}

        return security_results

    # ---------------- Protocols ----------------

    def _validate_protocols(self) -> Dict[str, Any]:
        """Validate routing and switching protocols (simulated)"""
        protocol_results: Dict[str, Any] = {
            "ospf_validation": {},
            "bgp_validation": {},
            "spanning_tree": {},
            "protocol_convergence": {},
        }

        # OSPF
        ospf_devices = [d for d, cfg in self.configs.items()
                        if cfg["parsed_config"].get("routing", {}).get("ospf", {}).get("enabled")]
        for d in ospf_devices:
            protocol_results["ospf_validation"][d] = {"neighbors_up": True}

        # BGP
        bgp_devices = [d for d, cfg in self.configs.items()
                       if cfg["parsed_config"].get("routing", {}).get("bgp", {}).get("enabled")]
        for d in bgp_devices:
            protocol_results["bgp_validation"][d] = {"sessions_up": True}

        return protocol_results

    # ---------------- Capacity ----------------

    def _analyze_capacity(self) -> Dict[str, Any]:
        """Analyze network capacity and growth planning (simulated)"""
        capacity_analysis: Dict[str, Any] = {
            "current_utilization": {},
            "projected_growth": {},
            "bottleneck_analysis": {},
            "scaling_recommendations": {},
        }

        for device in self.topology.nodes():
            capacity_analysis["current_utilization"][device] = {
                "avg_util_percent": random.uniform(20, 60)
            }
            capacity_analysis["bottleneck_analysis"][device] = {"bottleneck": False}
            capacity_analysis["scaling_recommendations"][device] = ["Monitor utilization trend"]

        return capacity_analysis

    # ---------------- Baseline ----------------

    def _compare_baseline(self) -> Dict[str, Any]:
        """Compare current metrics against baseline (simulated)"""
        if not self.baseline_metrics:
            return {"status": "No baseline available"}
        current = self._collect_current_metrics()
        return {
            "performance_delta": self._calculate_delta(self.baseline_metrics, current),
            "configuration_drift": self._detect_config_drift(),
            "topology_changes": self._detect_topology_changes(),
            "alerts": [],
        }

    def _collect_current_metrics(self) -> Dict[str, Any]:
        return {"dummy": 1}

    def _calculate_delta(self, base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        return {"delta": "placeholder"}

    def _detect_config_drift(self) -> Dict[str, Any]:
        return {"drift": False}

    def _detect_topology_changes(self) -> Dict[str, Any]:
        return {"changes": 0}

    # ---------------- Reporting ----------------

    def _generate_test_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        return {
            "test_execution_time": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": sum(len(v) if isinstance(v, dict) else 1 for v in test_results.values()),
                "passed_tests": self._count_passed_tests(test_results),
                "failed_tests": self._count_failed_tests(test_results),
                "warnings": self._count_warnings(test_results),
            },
            "detailed_results": test_results,
            "recommendations": self._generate_recommendations(test_results),
            "next_test_schedule": (datetime.now() + timedelta(hours=24)).isoformat(),
        }

    def _count_passed_tests(self, results: Dict[str, Any]) -> int:
        return 85  # placeholder

    def _count_failed_tests(self, results: Dict[str, Any]) -> int:
        return 10  # placeholder

    def _count_warnings(self, results: Dict[str, Any]) -> int:
        return 5  # placeholder

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        return [
            "Consider upgrading bandwidth on high-utilization links",
            "Implement additional redundancy for critical paths",
            "Review security configurations for compliance",
            "Optimize OSPF areas for better convergence",
            "Schedule regular configuration backups",
            "Monitor temperature on high-usage devices",
            "Consider load balancing for traffic distribution",
        ]

    # ---------------- Persistence ----------------

    def save_test_results(self, output_dir: Path) -> Path:
        """Save test results to file"""
        output_dir.mkdir(exist_ok=True, parents=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"day2_test_results_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, default=str)
        self.logger.info(f"Test results saved to {results_file}")
        return results_file
