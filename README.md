# 5G-CN-testbed_k8s
testbed setup for 5G Core Network deployment over 8s

## GOAL : open5gs + istio + some dashboard + UERANSIM

# DETAILS

# based on guideline here : https://luthfi.dev/posts/5g-cloud-native-simulation-with-open5gs/
# and also look at : https://github.com/AIDY-F2N/OAI-UERANSIM

# if you have error in creating new CRI runtime, check /etc/containerd/config.toml and enable cri v1

# Instead of ROOK-CEPH, just create PV manually
    - kc apply -f ./configs/mongodb-py.yaml (yaml inside configs)

# WebUI on port 3000, forwarding needed : 
    - kubectl port-forward <pod> -n open5gs 3000:3000
    - ssh -NfL 3000:localhost:3000 {VM ip}

# Kiali on port 20001, using istioctl dashboard kiali
# Enter inside mongoDB pod, append admin account info in db as below

'''
 db.accounts.insertOne({
... "salt": "f5c15fa72622d62b6b790aa8569b9339729801ab8bda5d13997b5db6bfc1d997",
... "hash": "402223057db5194899d2e082aeb0802f6794622e1cbc47529c419e5a603f2cc592074b4f3323b239ffa594c8b756d5c70a4e1f6ecd3f9f0d2d7328c4cf8b1b766514effff0350a90b89e21eac54cd4497a169c0c7554a0e2cd9b672e5414c323f76b8559bc768cba11cad2ea3ae704fb36abc8abc2619231ff84ded60063c6e1554a9777a4a464ef9cfdfa90ecfdacc9844e0e3b2f91b59d9ff024aec4ea1f51b703a31cda9afb1cc2c719a09cee4f9852ba3cf9f07159b1ccf8133924f74df770b1a391c19e8d67ffdcbbef4084a3277e93f55ac60d80338172b2a7b3f29cfe8a36738681794f7ccbe9bc98f8cdeded02f8a4cd0d4b54e1d6ba3d11792ee0ae8801213691848e9c5338e39485816bb0f734b775ac89f454ef90992003511aa8cceed58a3ac2c3814f14afaaed39cbaf4e2719d7213f81665564eec02f60ede838212555873ef742f6666cc66883dcb8281715d5c762fb236d72b770257e7e8d86c122bb69028a34cf1ed93bb973b440fa89a23604cd3fefe85fbd7f55c9b71acf6ad167228c79513f5cfe899a2e2cc498feb6d2d2f07354a17ba74cecfbda3e87d57b147e17dcc7f4c52b802a8e77f28d255a6712dcdc1519e6ac9ec593270bfcf4c395e2531a271a841b1adefb8516a07136b0de47c7fd534601b16f0f7a98f1dbd31795feb97da59e1d23c08461cf37d6f2877d0f2e437f07e25015960f63",
... "username": "admin",
... "roles": ["admin"],
... "__V": 0,
... })
'''
    - admin / 1423 by default

## UERANSIM configuration ##
# for matching configuration, run tcpdump inside AMF pod and check gNB's NGAP request to be clear
    - all configuration (SST, MCC, ..etc) in opensource-5g-core-service-mesh/helm-chart/values.yaml and openverso-charts/charts/ueransim-gnb/values.yaml should match
![Image](https://github.com/user-attachments/assets/23fe3e30-2c5d-46a7-a86c-63136c510d5a)

# Note that you should change AMF IP value in ueransim gnb configuration time by time
    - TODO : make sh script for this.

# Don't confuse open5gs side UE/gNB with UERANSIM side UE/gNB

# Everytime you rollout the deployment, following configuration should be revised
    - gNB's configuration -> amfConfig's address field
    - UE's configuration -> gnbSearchList field


## PacketRusher configuration ##
# github repo says docker is not supported, so run outside k8s cluster
# setup nodeport, using kc apply -f ./configs/amf_nodeport.yaml
# for packetrusher config.yaml, change gNB's N2/3 ip to node's ip running packetrusher, and node that running AMF's pod
# match forwarding port's number designated in amf_nodeport.yaml