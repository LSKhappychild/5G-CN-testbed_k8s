# deploy open5gs core network 

kc create ns open5gs

kc label ns open5gs istio-injection-

kc apply -f ../configs/mongodb-pv.yaml

cd ../open5gs

helm -n open5gs install -f values-5g.yaml open ./

kc apply -f ../configs/amf-nodeport.yaml

