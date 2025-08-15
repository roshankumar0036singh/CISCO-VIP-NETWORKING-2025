
import threading
import queue
import socket
import time
import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import networkx as nx

@dataclass
class NetworkPacket:
    """Metadata packet for IPC communication"""
    source_mac: str
    dest_mac: str
    source_ip: str
    dest_ip: str
    packet_type: str  # ARP, OSPF, BGP, DATA
    payload: Dict[str, Any]
    timestamp: float
    ttl: int = 64

class NetworkNode(threading.Thread):
    """Base class for network nodes with IPC capabilities"""
    
    def __init__(self, node_id: str, config: Dict[str, Any], topology: nx.Graph):
        super().__init__(daemon=True)
        self.node_id = node_id
        self.config = config
        self.topology = topology
        self.running = False
        self.paused = False
        
        # IPC queues for communication
        self.rx_queue = queue.Queue(maxsize=1000)
        self.tx_queue = queue.Queue(maxsize=1000)
        
        # Node state
        self.mac_address = self._generate_mac()
        self.ip_addresses = self._get_ip_addresses()
        self.arp_table = {}
        self.routing_table = {}
        self.statistics = {
            "packets_sent": 0,
            "packets_received": 0,
            "packets_dropped": 0,
            "uptime": 0,
            "last_update": time.time()
        }
        
        # Logging
        self.logger = logging.getLogger(f"Node-{node_id}")
        self.packet_log = []
        
        # Device-specific initialization
        self.device_type = config.get("parsed_config", {}).get("device_type", "unknown")
        self._initialize_device_specific()
    
    def _generate_mac(self) -> str:
        """Generate MAC address for the node"""
        import random
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))
    
    def _get_ip_addresses(self) -> List[str]:
        """Extract IP addresses from configuration"""
        ips = []
        for iface in self.config.get("parsed_config", {}).get("interfaces", []):
            ip = iface.get("ip_address")
            if ip and ip != "dhcp":
                ips.append(ip)
        return ips
    
    def _initialize_device_specific(self):
        """Initialize device-specific parameters"""
        if self.device_type == "router":
            self.ospf_neighbors = {}
            self.bgp_sessions = {}
        elif self.device_type == "switch":
            self.mac_table = {}
            self.vlan_table = {}
    
    def run(self):
        """Main thread execution"""
        self.running = True
        self.logger.info(f"Node {self.node_id} started")
        
        while self.running:
            if not self.paused:
                self._process_packets()
                self._periodic_tasks()
                self._update_statistics()
            time.sleep(0.1)
        
        self.logger.info(f"Node {self.node_id} stopped")
    
    def _process_packets(self):
        """Process incoming packets"""
        try:
            while not self.rx_queue.empty():
                packet = self.rx_queue.get_nowait()
                self._handle_packet(packet)
                self.statistics["packets_received"] += 1
        except queue.Empty:
            pass
    
    def _handle_packet(self, packet: NetworkPacket):
        """Handle received packet based on type"""
        self.packet_log.append({
            "timestamp": packet.timestamp,
            "type": "received",
            "packet": asdict(packet)
        })
        
        if packet.packet_type == "ARP":
            self._handle_arp(packet)
        elif packet.packet_type == "OSPF":
            self._handle_ospf(packet)
        elif packet.packet_type == "BGP":
            self._handle_bgp(packet)
        elif packet.packet_type == "DATA":
            self._handle_data(packet)
    
    def _handle_arp(self, packet: NetworkPacket):
        """Handle ARP packets"""
        if packet.payload.get("request"):
            target_ip = packet.payload.get("target_ip")
            if target_ip in self.ip_addresses:
                # Send ARP reply
                reply = NetworkPacket(
                    source_mac=self.mac_address,
                    dest_mac=packet.source_mac,
                    source_ip=target_ip,
                    dest_ip=packet.source_ip,
                    packet_type="ARP",
                    payload={"reply": True, "mac": self.mac_address},
                    timestamp=time.time()
                )
                self.send_packet(reply, packet.source_ip)
        
        # Update ARP table
        self.arp_table[packet.source_ip] = {
            "mac": packet.source_mac,
            "timestamp": time.time()
        }
    
    def _handle_ospf(self, packet: NetworkPacket):
        """Handle OSPF packets (router only)"""
        if self.device_type == "router":
            neighbor_id = packet.payload.get("router_id")
            if neighbor_id:
                self.ospf_neighbors[neighbor_id] = {
                    "ip": packet.source_ip,
                    "state": "full",
                    "last_hello": time.time()
                }
    
    def _handle_bgp(self, packet: NetworkPacket):
        """Handle BGP packets (router only)"""
        if self.device_type == "router":
            neighbor_as = packet.payload.get("as_number")
            if neighbor_as:
                self.bgp_sessions[packet.source_ip] = {
                    "as_number": neighbor_as,
                    "state": "established",
                    "last_keepalive": time.time()
                }
    
    def _handle_data(self, packet: NetworkPacket):
        """Handle data packets"""
        # Forward packet if not destined for this node
        if packet.dest_ip not in self.ip_addresses:
            self._forward_packet(packet)
    
    def _forward_packet(self, packet: NetworkPacket):
        """Forward packet to next hop"""
        next_hop = self._lookup_route(packet.dest_ip)
        if next_hop:
            packet.ttl -= 1
            if packet.ttl > 0:
                self.send_packet(packet, next_hop)
            else:
                self.statistics["packets_dropped"] += 1
    
    def _lookup_route(self, dest_ip: str) -> Optional[str]:
        """Look up next hop for destination IP"""
        # Simplified routing lookup
        for route, next_hop in self.routing_table.items():
            if dest_ip.startswith(route.split('/')[0][:7]):  # Simple prefix match
                return next_hop
        return None
    
    def _periodic_tasks(self):
        """Periodic maintenance tasks"""
        current_time = time.time()
        
        # Send periodic hello packets for routing protocols
        if self.device_type == "router" and current_time % 10 < 0.1:  # Every 10 seconds
            self._send_hello_packets()
        
        # Clean up ARP table
        if current_time % 30 < 0.1:  # Every 30 seconds
            self._cleanup_arp_table()
    
    def _send_hello_packets(self):
        """Send OSPF/BGP hello packets"""
        ospf_enabled = self.config.get("parsed_config", {}).get("routing", {}).get("ospf", {}).get("enabled", False)
        
        if ospf_enabled:
            for neighbor in self.topology.neighbors(self.node_id):
                hello_packet = NetworkPacket(
                    source_mac=self.mac_address,
                    dest_mac="ff:ff:ff:ff:ff:ff",
                    source_ip=self.ip_addresses[0] if self.ip_addresses else "0.0.0.0",
                    dest_ip="224.0.0.5",  # OSPF multicast
                    packet_type="OSPF",
                    payload={
                        "hello": True,
                        "router_id": self.node_id,
                        "area": "0.0.0.0"
                    },
                    timestamp=time.time()
                )
                self.send_packet(hello_packet, neighbor)
    
    def _cleanup_arp_table(self):
        """Remove stale ARP entries"""
        current_time = time.time()
        stale_entries = [ip for ip, entry in self.arp_table.items()
                        if current_time - entry["timestamp"] > 300]  # 5 minutes
        
        for ip in stale_entries:
            del self.arp_table[ip]
    
    def _update_statistics(self):
        """Update node statistics"""
        current_time = time.time()
        self.statistics["uptime"] = current_time - self.statistics["last_update"]
        self.statistics["last_update"] = current_time
    
    def send_packet(self, packet: NetworkPacket, destination_node: str):
        """Send packet to another node"""
        # This would be handled by the simulation engine
        # For now, just log the packet
        self.packet_log.append({
            "timestamp": packet.timestamp,
            "type": "sent",
            "destination": destination_node,
            "packet": asdict(packet)
        })
        self.statistics["packets_sent"] += 1
    
    def pause(self):
        """Pause node operation"""
        self.paused = True
        self.logger.info(f"Node {self.node_id} paused")
    
    def resume(self):
        """Resume node operation"""
        self.paused = False
        self.logger.info(f"Node {self.node_id} resumed")
    
    def stop(self):
        """Stop node operation"""
        self.running = False
        self.logger.info(f"Node {self.node_id} stopping")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get node statistics"""
        return {
            "node_id": self.node_id,
            "device_type": self.device_type,
            "statistics": self.statistics.copy(),
            "arp_table_size": len(self.arp_table),
            "routing_table_size": len(self.routing_table),
            "packet_log_size": len(self.packet_log)
        }

class SimulationEngine:
    """Main simulation engine coordinator"""
    
    def __init__(self, configs: Dict[str, Any], topology: nx.Graph):
        self.configs = configs
        self.topology = topology
        self.nodes: Dict[str, NetworkNode] = {}
        self.running = False
        self.paused = False
        self.logger = logging.getLogger("SimulationEngine")
        
        # IPC infrastructure
        self.message_queues = {}
        self.ipc_server = None
        
        self._initialize_nodes()
        self._setup_ipc()
    
    def _initialize_nodes(self):
        """Initialize all network nodes"""
        for node_id, config in self.configs.items():
            node = NetworkNode(node_id, config, self.topology)
            self.nodes[node_id] = node
            self.message_queues[node_id] = queue.Queue(maxsize=10000)
    
    def _setup_ipc(self):
        """Set up IPC infrastructure"""
        # Create IPC server for external communication
        try:
            self.ipc_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ipc_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ipc_server.bind(('localhost', 0))  # Let OS choose port
            self.ipc_server.listen(5)
            
            port = self.ipc_server.getsockname()[1]
            self.logger.info(f"IPC server listening on port {port}")
        except Exception as e:
            self.logger.error(f"Failed to setup IPC server: {e}")
    
    def start_simulation(self):
        """Start the network simulation"""
        self.running = True
        self.logger.info("Starting network simulation")
        
        # Start all nodes
        for node in self.nodes.values():
            node.start()
        
        # Start IPC handler
        if self.ipc_server:
            threading.Thread(target=self._handle_ipc, daemon=True).start()
        
        # Start packet routing thread
        threading.Thread(target=self._route_packets, daemon=True).start()
    
    def _handle_ipc(self):
        """Handle external IPC connections"""
        while self.running:
            try:
                client_socket, addr = self.ipc_server.accept()
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except Exception as e:
                if self.running:
                    self.logger.error(f"IPC error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, addr):
        """Handle individual IPC client"""
        try:
            with client_socket:
                while self.running:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Process IPC command
                    try:
                        command = json.loads(data.decode())
                        response = self._process_ipc_command(command)
                        client_socket.send(json.dumps(response).encode())
                    except json.JSONDecodeError:
                        client_socket.send(b'{"error": "Invalid JSON"}')
        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
    
    def _process_ipc_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process IPC command"""
        cmd_type = command.get("type")
        
        if cmd_type == "get_statistics":
            return {
                "statistics": {node_id: node.get_statistics() 
                             for node_id, node in self.nodes.items()}
            }
        elif cmd_type == "pause_node":
            node_id = command.get("node_id")
            if node_id in self.nodes:
                self.nodes[node_id].pause()
                return {"result": "paused"}
        elif cmd_type == "resume_node":
            node_id = command.get("node_id")
            if node_id in self.nodes:
                self.nodes[node_id].resume()
                return {"result": "resumed"}
        
        return {"error": "Unknown command"}
    
    def _route_packets(self):
        """Route packets between nodes"""
        while self.running:
            if not self.paused:
                # Simple packet routing between connected nodes
                for node_id, node in self.nodes.items():
                    try:
                        while not node.tx_queue.empty():
                            packet = node.tx_queue.get_nowait()
                            # Route to appropriate neighbor
                            self._deliver_packet(packet, node_id)
                    except queue.Empty:
                        pass
            time.sleep(0.01)
    
    def _deliver_packet(self, packet: NetworkPacket, sender_id: str):
        """Deliver packet to appropriate node"""
        # Find destination based on topology
        for neighbor in self.topology.neighbors(sender_id):
            try:
                self.nodes[neighbor].rx_queue.put_nowait(packet)
            except queue.Full:
                # Drop packet if queue is full
                self.nodes[sender_id].statistics["packets_dropped"] += 1
    
    def pause_simulation(self):
        """Pause the simulation"""
        self.paused = True
        for node in self.nodes.values():
            node.pause()
        self.logger.info("Simulation paused")
    
    def resume_simulation(self):
        """Resume the simulation"""
        self.paused = False
        for node in self.nodes.values():
            node.resume()
        self.logger.info("Simulation resumed")
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        for node in self.nodes.values():
            node.stop()
        
        if self.ipc_server:
            self.ipc_server.close()
        
        self.logger.info("Simulation stopped")
    
    def inject_link_failure(self, node1: str, node2: str):
        """Simulate link failure between two nodes"""
        if self.topology.has_edge(node1, node2):
            self.topology.remove_edge(node1, node2)
            self.logger.info(f"Link failure injected: {node1} <-> {node2}")
            
            # Notify affected nodes
            if node1 in self.nodes:
                failure_packet = NetworkPacket(
                    source_mac="00:00:00:00:00:00",
                    dest_mac=self.nodes[node1].mac_address,
                    source_ip="0.0.0.0",
                    dest_ip=self.nodes[node1].ip_addresses[0] if self.nodes[node1].ip_addresses else "0.0.0.0",
                    packet_type="LINK_FAILURE",
                    payload={"failed_neighbor": node2},
                    timestamp=time.time()
                )
                self.nodes[node1].rx_queue.put(failure_packet)
    
    def restore_link(self, node1: str, node2: str):
        """Restore failed link"""
        if not self.topology.has_edge(node1, node2):
            self.topology.add_edge(node1, node2)
            self.logger.info(f"Link restored: {node1} <-> {node2}")
    
    def get_simulation_statistics(self) -> Dict[str, Any]:
        """Get overall simulation statistics"""
        stats = {
            "running": self.running,
            "paused": self.paused,
            "total_nodes": len(self.nodes),
            "total_links": self.topology.number_of_edges(),
            "node_statistics": {}
        }
        
        for node_id, node in self.nodes.items():
            stats["node_statistics"][node_id] = node.get_statistics()
        
        return stats
