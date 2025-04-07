FROM ubuntu:noble-20250127
 
# Install needed tools
RUN apt update
RUN apt -y install nmap iproute2 iputils-ping python3 python3-pip openssh-server openssh-client
RUN pip install --break-system-packages pymodbus
 
# Make default "ubuntu" user passwordless
RUN passwd -d ubuntu
 
COPY plc_logger.py /home/ubuntu/
COPY bash_history /home/ubuntu/.bash_history
 
# SSH config - allow logging in with empty passwords
RUN echo "PermitEmptyPasswords yes" >> /etc/ssh/sshd_config
 
CMD service ssh start \
      && su ubuntu -c "python3 /home/ubuntu/plc_logger.py >> /home/ubuntu/plc-log.txt"
