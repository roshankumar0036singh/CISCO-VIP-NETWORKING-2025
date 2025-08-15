

import time
import threading
from typing import Dict, Any
import networkx as nx

class Day1Simulator:
    def __init__(self, topology: nx.Graph, configs: Dict[str, Any]):
        self.topo = topology
        self.configs = configs
        self.arp_tables = {dev: {} for dev in topology.nodes()}
        self.ospf_neighbors = {}
        self.bgp_neighbors = {}

    def bring_up_interfaces(self):
        for dev, cfg in self.configs.items():
            for iface in cfg["parsed_config"]["interfaces"]:
                iface["status"] = "up"
        print("✅ All interfaces set to up")

    def wait_stabilization(self, seconds=60):
        print(f"⏳ Waiting {seconds}s for Day 1 network stabilization…")
        time.sleep(seconds)
        print("✅ Stabilization complete")

    def populate_arp(self):
        for dev in self.topo.nodes():
            # build ARP entries for directly connected neighbors
            neighbors = list(self.topo.neighbors(dev))
            self.arp_tables[dev] = {nbr: f"00:11:22:{hash(nbr)%100:02d}:{hash(dev)%100:02d}:AA" 
                                     for nbr in neighbors}
        print("✅ ARP tables populated")

    def trigger_ospf(self):
        # Simulate OSPF adjacencies on each subnet edge
        for u, v, data in self.topo.edges(data=True):
            if data.get("link_type")=="subnet" and "ospf" in data.get("title","").lower():
                self.ospf_neighbors.setdefault(u,[]).append(v)
                self.ospf_neighbors.setdefault(v,[]).append(u)
        print("✅ OSPF adjacencies formed:", self.ospf_neighbors)

    def trigger_bgp(self):
        # Simulate BGP sessions on each bgp edge
        for u, v, data in self.topo.edges(data=True):
            if data.get("link_type")=="bgp":
                self.bgp_neighbors.setdefault(u,[]).append(v)
                self.bgp_neighbors.setdefault(v,[]).append(u)
        print("✅ BGP sessions established:", self.bgp_neighbors)

    def validate_neighbors(self):
        failures = []
        for dev in self.configs:
            exp_ospf = [
                nbr for nbr in self.topo.neighbors(dev)
                if self.topo[dev][nbr].get("link_type") == "ospf"
            ]
            got = self.ospf_neighbors.get(dev, [])
        for nbr in exp_ospf:
            if nbr not in got:
                failures.append(f"OSPF: {dev} failed to form neighbor with {nbr}")
        if failures:
            print("❌ Day 1 neighbor validation failures:")
            for f in failures:
                print(" ", f)
        else:
            print("✅ Day 1 neighbor validation passed")
    

    def run(self):
        self.bring_up_interfaces()
        self.wait_stabilization()
        self.populate_arp()
        self.trigger_ospf()
        self.trigger_bgp()
        self.validate_neighbors()
