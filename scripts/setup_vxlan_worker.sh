# Setup VXLAN tunnel from worker to master

MASTER_IP="10.178.0.34"

echo "Setting up VXLAN ports pointing back to master at IP $MASTER_IP..."

# ------------------------------------------------------------------------------
# Bridge n2br: VNI key=100
# ------------------------------------------------------------------------------
sudo ovs-vsctl del-port n2br vxlan-oai-master-n2br 2>/dev/null || true
sudo ovs-vsctl add-port n2br vxlan-oai-master-n2br \
            -- set interface vxlan-oai-master-n2br type=vxlan \
                options:remote_ip=$MASTER_IP \
                    options:key=100

# ------------------------------------------------------------------------------
# Bridge n3br: VNI key=101
# ------------------------------------------------------------------------------
sudo ovs-vsctl del-port n3br vxlan-oai-master-n3br 2>/dev/null || true
sudo ovs-vsctl add-port n3br vxlan-oai-master-n3br \
            -- set interface vxlan-oai-master-n3br type=vxlan \
                options:remote_ip=$MASTER_IP \
                    options:key=101

# ------------------------------------------------------------------------------
# Bridge n4br: VNI key=102
# ------------------------------------------------------------------------------
sudo ovs-vsctl del-port n4br vxlan-oai-master-n4br 2>/dev/null || true
sudo ovs-vsctl add-port n4br vxlan-oai-master-n4br \
            -- set interface vxlan-oai-master-n4br type=vxlan \
                options:remote_ip=$MASTER_IP \
                    options:key=102

echo "All VXLAN ports have been set up on this worker node."
