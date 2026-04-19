"""
SDN Firewall Controller for POX
Implements rule-based packet filtering with logging
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
import time

log = core.getLogger()

# Firewall Rules Configuration
FIREWALL_RULES = [
    {"rule_id": 1, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.2", "action": "block", "description": "Block h1 to h2"},
    {"rule_id": 2, "src_ip": "10.0.0.1", "dst_ip": "10.0.0.3", "action": "allow", "description": "Allow h1 to h3"},
    {"rule_id": 3, "src_ip": "10.0.0.2", "dst_ip": "10.0.0.3", "action": "allow", "description": "Allow h2 to h3"},
]

class FirewallController(object):
    def __init__(self):
        core.openflow.addListeners(self)
        self.mac_to_port = {}
        self.blocked_count = 0
        self.allowed_count = 0
       
        # Log file setup
        self.log_file = open('/tmp/firewall.log', 'w')
        self.log_file.write("=== SDN Firewall Log ===\n")
        self.log_file.write(f"Started at: {time.ctime()}\n\n")
       
        log.info("Firewall Controller initialized")
        log.info(f"Loaded {len(FIREWALL_RULES)} firewall rules")
       
        # Print rules
        for rule in FIREWALL_RULES:
            log.info(f"Rule {rule['rule_id']}: {rule['src_ip']} -> {rule['dst_ip']} = {rule['action'].upper()}")

    def _handle_ConnectionUp(self, event):
        """Handle new switch connection"""
        log.info(f"Switch {event.dpid} connected")
        self.log_file.write(f"Switch {event.dpid} connected at {time.ctime()}\n")
        self.log_file.flush()

    def check_firewall_rules(self, src_ip, dst_ip):
        """Check if packet matches any firewall rule"""
        for rule in FIREWALL_RULES:
            if rule["src_ip"] == str(src_ip) and rule["dst_ip"] == str(dst_ip):
                return rule["action"], rule["description"]
        return "allow", "Default allow"

    def _handle_PacketIn(self, event):
        """Handle incoming packets"""
        packet = event.parsed
       
        if not packet.parsed:
            log.warning("Incomplete packet")
            return

        # Learn MAC addresses
        dpid = event.dpid
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}
       
        self.mac_to_port[dpid][packet.src] = event.port

        # Handle IP packets
        if packet.type == ethernet.IP_TYPE:
            ip_packet = packet.payload
            src_ip = ip_packet.srcip
            dst_ip = ip_packet.dstip
           
            # Check firewall rules
            action, reason = self.check_firewall_rules(src_ip, dst_ip)
           
            if action == "block":
                # BLOCK the packet
                self.blocked_count += 1
                log_msg = f"BLOCKED: {src_ip} -> {dst_ip} | Reason: {reason}"
                log.warning(log_msg)
               
                # Write to log file
                self.log_file.write(f"{time.ctime()} | {log_msg}\n")
                self.log_file.flush()
               
                # Install drop rule on switch
                msg = of.ofp_flow_mod()
                msg.match.dl_type = 0x0800  # IP
                msg.match.nw_src = src_ip
                msg.match.nw_dst = dst_ip
                msg.idle_timeout = 30
                msg.hard_timeout = 60
                msg.priority = 10
                # No actions = DROP
                event.connection.send(msg)
               
                print(f"[FIREWALL] ❌ BLOCKED: {src_ip} -> {dst_ip}")
                return  # Don't forward the packet
               
            else:
                # ALLOW the packet
                self.allowed_count += 1
                log_msg = f"ALLOWED: {src_ip} -> {dst_ip}"
                log.info(log_msg)
               
                # Write to log file
                self.log_file.write(f"{time.ctime()} | {log_msg}\n")
                self.log_file.flush()
               
                print(f"[FIREWALL] ✓ ALLOWED: {src_ip} -> {dst_ip}")

        # Forward the packet (normal switching)
        if packet.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][packet.dst]
        else:
            out_port = of.OFPP_FLOOD

        # Create packet_out message
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.in_port = event.port
        msg.actions.append(of.ofp_action_output(port=out_port))
        event.connection.send(msg)

    def print_stats(self):
        """Print firewall statistics"""
        print(f"\n{'='*50}")
        print(f"Firewall Statistics")
        print(f"{'='*50}")
        print(f"Allowed Packets: {self.allowed_count}")
        print(f"Blocked Packets: {self.blocked_count}")
        print(f"{'='*50}\n")

def launch():
    """Launch the firewall controller"""
    core.registerNew(FirewallController)
    log.info("Firewall controller launched successfully")
