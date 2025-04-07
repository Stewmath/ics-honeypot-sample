#!/usr/bin/python3
#
# This configures the network configuration of the PLC devices and the scripts running them. It
# bridges with the docker container so that they appear on the same subnet.
 
import sys, time
 
from mininet.clean import Cleanup
from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, Node
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
 
 
 
def honeypot_host(net, sw, name: str, ip: str):
    h = net.addHost(name, ip=ip)
    net.addLink(h, sw)
    return h
 
def run():
    setLogLevel('info')
 
    net = Mininet(controller=Controller, switch=OVSSwitch, link=TCLink)
 
    c1 = net.addController('c1')
    s1 = net.addSwitch('s1')
 
    # Hosts that impersonate PLC devices
    h1 = honeypot_host(net, s1, 'h1', '10.0.2.5/24')
    h2 = honeypot_host(net, s1, 'h2', '10.0.2.8/24')
 
    net.start()
 
    # Run the programs imitating the PLC devices
    h1.popen('./run_in_venv.sh python3 plc_server.py tempsensor')
    h2.popen('./run_in_venv.sh python3 plc_server.py valve')
 
    # Uncomment to open CLI for testing
    #CLI(net)
 
    # Infinite loop - run mininet until script is closed.
    while True:
        time.sleep(1)
 
    net.stop()
 
 
if __name__ == '__main__':
    # Clean up any artifacts from previous runs
    Cleanup.cleanup()
 
    run()
