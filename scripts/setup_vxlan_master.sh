# Setup VXLAN tunnels from master to worker
# I am not sure why VXLAN is needed here
# Prerequisite : OVS
# TODO : revise style like worker's one

# 1) Remove any existing port (safe to ignore errors)
sudo ovs-vsctl del-port n2br vxlan-oai-worker1-n2br 2>/dev/null || true

# 2) Add a new VXLAN port for worker1 on master
sudo ovs-vsctl add-port n2br vxlan-oai-worker1-n2br \
	-- set interface vxlan-oai-worker1-n2br type=vxlan \
	options:remote_ip=10.178.0.31 \
	options:key=100

# For bridge n3br
sudo ovs-vsctl del-port n3br vxlan-oai-worker1-n3br 2>/dev/null || true
sudo ovs-vsctl add-port n3br vxlan-oai-worker1-n3br \
	-- set interface vxlan-oai-worker1-n3br type=vxlan \
	options:remote_ip=10.178.0.31 \
	options:key=101

# For bridge n4br
sudo ovs-vsctl del-port n4br vxlan-oai-worker1-n4br 2>/dev/null || true
sudo ovs-vsctl add-port n4br vxlan-oai-worker1-n4br \
	-- set interface vxlan-oai-worker1-n4br type=vxlan \
	options:remote_ip=10.178.0.31 \
	options:key=102


################ Worker 1 done (10.178.0.31)

# 1) Remove any existing port (safe to ignore errors)
sudo ovs-vsctl del-port n2br vxlan-oai-worker2-n2br 2>/dev/null || true

# 2) Add a new VXLAN port for worker2 on master
sudo ovs-vsctl add-port n2br vxlan-oai-worker2-n2br \
	-- set interface vxlan-oai-worker2-n2br type=vxlan \
	options:remote_ip=10.178.0.32 \
	options:key=100

# For bridge n3br
sudo ovs-vsctl del-port n3br vxlan-oai-worker2-n3br 2>/dev/null || true
sudo ovs-vsctl add-port n3br vxlan-oai-worker2-n3br \
	-- set interface vxlan-oai-worker2-n3br type=vxlan \
	options:remote_ip=10.178.0.32 \
	options:key=101

# For bridge n4br
sudo ovs-vsctl del-port n4br vxlan-oai-worker2-n4br 2>/dev/null || true
sudo ovs-vsctl add-port n4br vxlan-oai-worker2-n4br \
	-- set interface vxlan-oai-worker2-n4br type=vxlan \
	options:remote_ip=10.178.0.32 \
	options:key=102

################ Worker 2 done (10.178.0.32)

# 1) Remove any existing port (safe to ignore errors)
sudo ovs-vsctl del-port n2br vxlan-oai-worker3-n2br 2>/dev/null || true

# 2) Add a new VXLAN port for worker3 on master
sudo ovs-vsctl add-port n2br vxlan-oai-worker3-n2br \
	-- set interface vxlan-oai-worker3-n2br type=vxlan \
	options:remote_ip=10.178.0.33 \
	options:key=100

# For bridge n3br
sudo ovs-vsctl del-port n3br vxlan-oai-worker3-n3br 2>/dev/null || true
sudo ovs-vsctl add-port n3br vxlan-oai-worker3-n3br \
	-- set interface vxlan-oai-worker3-n3br type=vxlan \
	options:remote_ip=10.178.0.33 \
	options:key=101

# For bridge n4br
sudo ovs-vsctl del-port n4br vxlan-oai-worker3-n4br 2>/dev/null || true
sudo ovs-vsctl add-port n4br vxlan-oai-worker3-n4br \
	-- set interface vxlan-oai-worker3-n4br type=vxlan \
	options:remote_ip=10.178.0.33 \
	options:key=102
