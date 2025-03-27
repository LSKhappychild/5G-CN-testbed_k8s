# Setup iptables. off swapping

sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT
sudo swapoff -a
sudo ufw disable

# delete existing flannel cni

sudo ip link set flannel.1 down
sudo ip link del flannel.1

sudo ip link set cni0 down
sudo ip link del cni0

sudo rm $HOME/.kube/config
sudo modprobe br_netfilter
sudo sysctl net.bridge.bridge-nf-call-iptables=1
sudo systemctl enable docker

sudo kubeadm reset

sudo rm -rf /etc/cni/net.d