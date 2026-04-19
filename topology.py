from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class FirewallTopology(Topo):
    """Simple topology with 3 hosts and 1 switch"""
   
    def build(self):
        # Add switch
        s1 = self.addSwitch('s1')
       
        # Add hosts with specific IPs
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
       
        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)

def run():
    """Start the network"""
    topo = FirewallTopology()
   
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633),
        autoSetMacs=True
    )
   
    net.start()
    print("="*60)
    print("Network Started - Firewall Active")
    print("="*60)
    print("\nTest Commands:")
    print("  h1 ping -c 3 h2  (should be BLOCKED)")
    print("  h1 ping -c 3 h3  (should be ALLOWED)")
    print("  h2 ping -c 3 h3  (should be ALLOWED)")
    print("  pingall")
    print("="*60)
   
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
