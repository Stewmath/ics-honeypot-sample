## About
 
This is a basic honeypot meant to imitate an ICS environment. It simulates one Linux machine which
can be connected to over SSH, which communicates with two simulated PLC devices (a temperature
sensor and a valve reporting a liquid's flow rate) on the same subnet, communicating with modbus.
 
## Setup
 
### Required tools on host machine
 
- Mininet
- OpenVSwitch (ensure the service is running)
- Docker
- Python3
 
### A sample attack
 
Start by running "./setup.sh", which sets up everything needed for the honeypot to function. The
docker container will then run a python program which communicates with two simulated PLC devices
using the modbus protocol. SSH runs on port 22 (2222 on the host), and passwordless login is
possible with the "ubuntu" user.

An SSH connection can be opened in another terminal while it is running. The following is a sample
attack that starts by connecting over SSH:
 
```console
$ ssh ubuntu@localhost -p 2222
ubuntu@56f661ebb517:~$ ls -a
.  ..  .bash_history  .bash_logout  .bashrc  .cache  .profile  plc-log.txt  plc_logger.py
ubuntu@56f661ebb517:~$ cat plc-log.txt
2025-04-06 23:18:44,373 - Connecting to PLC at 10.0.2.5...
2025-04-06 23:18:44,488 - Connecting to PLC at 10.0.2.8...
2025-04-06 23:18:44,609 - Temp: 22.76; Flow: 5.11
2025-04-06 23:18:49,617 - Temp: 22.56; Flow: 5.50
2025-04-06 23:18:54,627 - Temp: 22.96; Flow: 5.57
2025-04-06 23:18:59,636 - Temp: 22.98; Flow: 5.49
ubuntu@5ae33a29c8f8:~$ ip route
default via 10.0.2.1 dev eth0
10.0.2.0/24 dev eth0 proto kernel scope link src 10.0.2.2
10.2.0.0/16 dev eth1 proto kernel scope link src 10.2.0.2
ubuntu@56f661ebb517:~$ nmap --script=modbus-discover.nse -p 502 10.0.2.0/24
Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-04-06 23:17 UTC
Nmap scan report for 10.0.2.1
Host is up (0.00035s latency).
 
PORT    STATE  SERVICE
502/tcp closed mbap
 
Nmap scan report for 56f661ebb517 (10.0.2.2)
Host is up (0.00026s latency).
 
PORT    STATE  SERVICE
502/tcp closed mbap
 
Nmap scan report for 10.0.2.5
Host is up (0.032s latency).
 
PORT    STATE SERVICE
502/tcp open  modbus
| modbus-discover:
|   sid 0x1:
|     Slave ID data: Siemens-SM\xFF
|_    Device identification: Siemens SM
 
Nmap scan report for 10.0.2.8
Host is up (0.044s latency).
 
PORT    STATE SERVICE
502/tcp open  modbus
| modbus-discover:
|   sid 0x1:
|     Slave ID data: Siemens-SM\xFF
|_    Device identification: Siemens SM
 
Nmap done: 256 IP addresses (4 hosts up) scanned in 3.24 seconds
```
 
## Docker and Mininet
 
Docker is ideal for creating a sandboxed, configurable, and reproducible environment that can be
made realistic enough to fool an attacker - which is why it is used for the node running the SSH
server. On the other hand, it is a bit overkill for PLC devices which (based on my limited research)
do not run anything like Linux, and may not even have the concept of an interactive shell.
 
For this reason, Mininet is used to create network nodes corresponding to PLC devices; for each
node, a simple python script can simulate the modbus protocol. Mininet does not provide full
sandboxing, only separate network namespaces, which is all we need for this purpose - saving system
resources compared to using Docker.
 
Docker and Mininet nodes can communicate with each other by connecting the master mininet "switch"
to docker's bridge interface. The subnets are configured to be the same on both networks, giving
the appearance that they are on the same local network.
 
## Files
 
### mininet\_setup.py
 
This script configures mininet with two nodes (for the PLC devices) and a switch connecting them
together. It executes the "plc\_server.py" script in each of the nodes to simulate the two PLC
devices.
 
### plc\_server.py
 
This script runs in the mininet nodes, and simulates one of two types of PLCs - a temperature
sensor, and a valve which measures flow rate. Each has a single input register which reports the
temperature or flow rate, respectively, as an 8.8 fixed-point value. The measurements are programmed
to fluctuate within a range of values for some degree of realism.
 
### docker/plc\_logger.py
 
This runs in the docker container, and communicates with the two simulated PLC devices at two
separate IP addresses. It logs the output to the file "plc-log.txt". The attacker would observe both
of these files in the "ubuntu" home directory upon logging into the unprotected SSH server.
 
### setup.sh
 
Uses all of the above scripts to set up the honeypot.
 
## Discussion
 
### Improving realism of the honeypot
 
The following ideas were implemented:
- Added a bash history file: I used chatgpt to create a .bash\_history file after giving it some
  context about the environment, giving the appearance that this machine has been used before.
- Added a second subnet: In addition to the 10.0.2.0/24 subnet where the PLC devices are, I added
  a second network interface connected to the subnet 10.2.0.0/16, which could connect to a broader
  corporate network. There are no other devices connected to it right now, but it does give the
  illusion of a more complex network topology at a glance.
 
Some more areas for improvement:
- The "ip link" command shows that the interface name is "eth0@if936", which is evidence of
  a virtualized network interface. It may be necessary to use one of docker's alternative network
  modes to work around this.
- Could add a custom DNS server, common in corporate environments.
- In a real environment, this kind of system would probably have some SCADA-related tools installed,
  rather than using a python script to interact with the PLCs. I don't know much about
  industry-standard tools in this area, but I would make it a priority to learn more about the tools
  that these types of systems would typically use, in order to imitate them.
 
### Scalability
 
The PLC nodes could be scaled quite easily by adding new lines to the mininet\_setup.py script for
new nodes. Mininet itself is quite lightweight as it is not a sandbox; it merely creates new network
namespaces for each node. I expect it should scale well.
 
On the other hand, if we want to create more linux devices that can be SSH'd into, my script for
setting up the docker image is a bit cumbersome. I would look into tools such as docker-compose
which can help to manage networks of docker images to simplify things.

Depending on the scale, though, a single server may not be enough to believably simulate many docker
containers - in which case the challenge would become coordinating many simulated machines across
many real host machines. I understand that tools like Kubernetes and Docker Swarm are designed for
this, though I don't have experience with them.
