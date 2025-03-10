# NOTE : CIDR is set to 10.244.0.0/16
# using flannel as CNI

# Run below manually in each node
# sudo cat > /etc/containerd/config.toml <<EOF
# [plugins."io.containerd.grpc.v1.cri"]
# systemd_cgroup = true
# EOF

sudo systemctl restart containerd
sleep 10

sudo kubeadm init --pod-network-cidr=10.244.0.0/16

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml