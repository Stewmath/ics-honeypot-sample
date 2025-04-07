# Sets up the honeypot using docker and mininet. See readme for more details.

MININET_SWITCH="s1" # Name of the switch used in mininet_setup.py
DOCKER_BRIDGE_A="hp-bridge-a" # Bridge name, both internally for docker and as seen with "ip link"
DOCKER_BRIDGE_B="hp-bridge-b" # Bridge for another subnet, currently unused
SUBNET_A=10.0.2.0/24  # Subnet that the PLC devices occupy
SUBNET_B=10.2.0.0/16  # Currently unused subnet, makes topology seem more complex
GATEWAY_IP_A=10.0.2.1 # Bridge device takes this IP address, functions as a gateway
GATEWAY_IP_B=10.2.0.1
 
BOLD=$(tput bold)
ENDCOLOR=$(tput sgr0)
 
 
function header()
{
  echo
  echo -e "$BOLD$1...$ENDCOLOR"
}
 
# Call when script exits
function cleanup()
{
  header "Cleaning up"
 
  sudo docker network rm $DOCKER_BRIDGE_A
  sudo docker network rm $DOCKER_BRIDGE_B
  kill $mininet_pid
}
 
trap cleanup EXIT
 
 
header "Requesting superuser access"
sudo echo "Got superuser access" || exit 1
 
 
# Create a venv environment with pymodbus installed
if [[ ! -d venv ]]; then
  header "Creating python venv environment"
  python -m venv venv
  venv/bin/pip3 install pymodbus
fi
 
header 'Launching mininet'
sudo python3 mininet_setup.py 2>&1 >/dev/null &
mininet_pid=$!
 
sleep 3 # Wait for mininet to initialize
 
header 'Initializing docker networks'
sudo docker network create --driver=bridge --subnet=$SUBNET_A --gateway $GATEWAY_IP_A \
  -o com.docker.network.bridge.name=$DOCKER_BRIDGE_A \
  $DOCKER_BRIDGE_A
sudo docker network create --driver=bridge --subnet=$SUBNET_B --gateway $GATEWAY_IP_B \
  -o com.docker.network.bridge.name=$DOCKER_BRIDGE_B \
  $DOCKER_BRIDGE_B
 
# Link docker's bridge with mininet's master switch - allow them to communicate.
# All mininet devices will appear to be on the same subnet as the docker container.
header 'Linking docker to mininet'
sudo ip link set $MININET_SWITCH master $DOCKER_BRIDGE_A
 
header 'Building docker container'
sudo docker build -t honeypot docker/
 
# Run the container until we receive Ctrl+C
header 'Running docker container'
echo "Connect with: ssh ubuntu@localhost -p 2222"
sudo docker run -it --network=$DOCKER_BRIDGE_A --network=$DOCKER_BRIDGE_B -p 2222:22 honeypot
