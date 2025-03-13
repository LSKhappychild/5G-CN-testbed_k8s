# deploy open5gs core network 

kc create ns open5gs

cd ~/opensource-5g-core-service-mesh/helm-chart

helm -n open5gs install -f values.yaml open ./

