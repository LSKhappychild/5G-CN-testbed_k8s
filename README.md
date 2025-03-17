```markdown
# 5G-CN Testbed on Kubernetes

This document describes the testbed setup for deploying a **5G Core Network** on Kubernetes. The deployment integrates **Open5GS**, **Istio**, dashboards (such as Kiali and Grafana), and traffic simulators like **PacketRusher** or **UERANSIM**.

---

## Goal

- **Deploy Open5GS** as the 5G Core Network.
- Use **Istio** for service mesh and traffic management.
- Visualize network status with dashboards (e.g., **Kiali** and **Grafana**).
- Test control plane procedures with simulators (**PacketRusher** or **UERANSIM**).

---

## References

- [5G Cloud-Native Simulation with Open5GS](https://luthfi.dev/posts/5g-cloud-native-simulation-with-open5gs/)
- [AIDY-F2N/OAI-UERANSIM](https://github.com/AIDY-F2N/OAI-UERANSIM)

---

## Prerequisites and Environment Setup

### Container Runtime

- Ensure your CRI runtime is set up correctly.
- If you encounter errors creating a new CRI runtime, check `/etc/containerd/config.toml` and make sure **CRI v1** is enabled.

### Istio Installation

- Install Istio using the provided configuration file:
  ```bash
  kubectl apply -f ./configs/istio-install.yaml
  ```

---

## 1. Storage and MongoDB Setup

### Manual PV Creation (for MongoDB)

Instead of using ROOK-CEPH, create a PersistentVolume (PV) manually.

1. Apply your MongoDB PV manifest:
   ```bash
   kubectl apply -f ./configs/mongodb-py.yaml
   ```
2. Verify that:
   - The `nodeAffinity` section is correctly configured.
   - The `hostPath` (or other storage driver settings) are set as needed.
3. Ensure that MongoDB’s PersistentVolumeClaim (PVC) properly binds to the created PV.

---

## 2. Open5GS WebUI

- **Default Port**: 3000
- To access the WebUI, forward the port:
  ```bash
  kubectl port-forward <open5gs-webui-pod> -n open5gs 3000:3000
  ```
- Alternatively, set up an SSH tunnel:
  ```bash
  ssh -NfL 3000:localhost:3000 <VM-ip>
  ```
- Access the WebUI at: [http://localhost:3000](http://localhost:3000)

---

## 3. Kiali Dashboard

- **Default Port**: 20001 (via Istio)
- Launch the Kiali dashboard with:
  ```bash
  istioctl dashboard kiali
  ```
- Access it at: [http://localhost:20001](http://localhost:20001)

---

## 4. MongoDB Administration for Open5GS

### Inserting an Admin Account

1. Enter the MongoDB pod:
   ```bash
   kubectl exec -it <mongodb-pod> -- bash
   ```
2. Start the Mongo shell:
   ```bash
   mongo
   ```
3. Switch to the `open5gs` database:
   ```js
   use open5gs
   ```
4. Insert an admin record:
   ```js
   db.accounts.insertOne({
     "salt": "f5c15fa72622d62b6b790aa8569b9339729801ab8bda5d13997b5db6bfc1d997",
     "hash": "402223057db5194899d2e082aeb0802f6794622e1cbc47529c419e5a603f2cc592074b4f3323b239ffa594c8b756d5c70a4e1f6ecd3f9f0d2d7328c4cf8b1b766514effff0350a90b89e21eac54cd4497a169c0c7554a0e2cd9b672e5414c323f76b8559bc768cba11cad2ea3ae704fb36abc8abc2619231ff84ded60063c6e1554a9777a4a464ef9cfdfa90ecfdacc9844e0e3b2f91b59d9ff024aec4ea1f51b703a31cda9afb1cc2c719a09cee4f9852ba3cf9f07159b1ccf8133924f74df770b1a391c19e8d67ffdcbbef4084a3277e93f55ac60d80338172b2a7b3f29cfe8a36738681794f7ccbe9bc98f8cdeded02f8a4cd0d4b54e1d6ba3d11792ee0ae8801213691848e9c5338e39485816bb0f734b775ac89f454ef90992003511aa8cceed58a3ac2c3814f14afaaed39cbaf4e2719d7213f81665564eec02f60ede838212555873ef742f6666cc66883dcb8281715d5c762fb236d72b770257e7e8d86c122bb69028a34cf1ed93bb973b440fa89a23604cd3fefe85fbd7f55c9b71acf6ad167228c79513f5cfe899a2e2cc498feb6d2d2f07354a17ba74cecfbda3e87d57b147e17dcc7f4c52b802a8e77f28d255a6712dcdc1519e6ac9ec593270bfcf4c395e2531a271a841b1adefb8516a07136b0de47c7fd534601b16f0f7a98f1dbd31795feb97da59e1d23c08461cf37d6f2877d0f2e437f07e25015960f63",
     "username": "admin",
     "roles": ["admin"],
     "__V": 0
   })
   ```
- **Default Login Credentials**:  
  Username: `admin`  
  Password: `1423`

### Managing Subscriber Data

- Use the scripts in the `./dbcontrol` directory to manage the subscriber database.
- For example, run `create_ues.py` to generate a `subscribers.yaml` file and load it into MongoDB.

---

## 5. UERANSIM Configuration

When integrating **UERANSIM**:

1. **Match Configurations**:  
   Ensure that the PLMN (MCC, MNC), slice (SST, SD), and TAC settings in UERANSIM match those in your Open5GS configuration.  
   Check these files:
   - `opensource-5g-core-service-mesh/helm-chart/values.yaml`
   - `openverso-charts/charts/ueransim-gnb/values.yaml`

2. **Verify NGAP Requests**:  
   Run `tcpdump` inside the AMF pod (ensure you have root privileges or proper capabilities) to inspect the gNB’s NGAP requests.

3. **Update on Redeployment**:  
   - Update the **AMF IP** in the UERANSIM gNB configuration if it changes.
   - Adjust the UE configuration's `gnbSearchList` accordingly.

> **Note**: Do not confuse the Open5GS side UE/gNB with those in UERANSIM—they are separate entities.

---

## 6. PacketRusher Configuration

Since PacketRusher does not support Docker, run it **outside** the Kubernetes cluster.

1. **Expose the AMF**:
   - Create a NodePort service for the AMF:
     ```bash
     kubectl apply -f ./configs/amf_nodeport.yaml
     ```
2. **Configure PacketRusher**:
   - In the PacketRusher `config.yaml`, update:
     - **gNB’s N2/N3 IP**: Set to the Node IP where PacketRusher runs.
     - **AMF IP/Port**: Set to the Node IP and NodePort where the AMF is exposed.
     - **PLMN and Slice Information**: Ensure they match the core network configuration.
     - **UE SIM Credentials**: (OPc, key, IMSI) must correspond to the data in MongoDB.

---

## 7. Open5GS Helm Chart Configuration

Use the latest Gradiant Open5GS Helm chart:
```bash
helm pull oci://registry-1.docker.io/gradiant/open5gs --version 2.2.6
```
- This chart deploys **Open5GS 2.7.2**.
- Adjust the `values.yaml` file for:
  - **AMF Configuration**: Set parameters such as MCC, MNC, TAC, SST, etc.
  - **NRF and SCP Settings**: Configure according to your desired architecture.
  - **Security Context**: To run `tcpdump` inside the AMF pod, set:
    ```yaml
    containerSecurityContext:
      enabled: true
      runAsUser: 0
      runAsNonRoot: false
    ```

---

## 8. SCP vs. NRF

- **NRF (Network Repository Function)**:
  - Responsible for the registration and discovery of network functions (NFs).
  - Answers queries like "Where is the AUSF?" or "Which SMF is available?"

- **SCP (Service Communication Proxy)**:
  - Acts as a proxy for NF communications.
  - Provides load balancing, security, and topology hiding.
  - If your configuration sets:
    ```yaml
    sbi:
      client:
        nrf:
          enabled: false
        scp:
          enabled: true
    ```
    then the AMF will contact the SCP for function discovery instead of contacting the NRF directly.

---

## 9. Redeployment Summary

Each time you redeploy the 5G Core testbed:

1. **Verify AMF Exposure**:  
   Check the AMF IP or NodePort if it is exposed externally.

2. **Update gNB Configurations**:  
   Update the gNB configuration in PacketRusher or UERANSIM (AMF IP, PLMN, etc.) as needed.

3. **Check Subscriber Data**:  
   Ensure that subscriber data in MongoDB is up-to-date.

4. **Confirm Istio Settings**:  
   Verify any changes in Istio sidecar injection or networking settings.

5. **Review Open5GS Configurations**:  
   Double-check the values for AMF, NRF/SCP, and related settings.

---

## 10. Troubleshooting Tips

- **tcpdump in AMF Pod**:  
  Requires root privileges or appropriate Linux capabilities (e.g., NET_RAW, NET_ADMIN).

- **MongoDB Storage**:  
  Verify that your PV, PVC, and node affinity settings are correct.

- **Istio Sidecar Injection**:  
  May affect non-HTTP protocols (such as NGAP); adjust configurations if necessary.

- **Dashboard Access**:  
  Use port-forwarding or NodePort services to access the WebUI (port 3000) and Kiali (port 20001).

- **Configuration Consistency**:  
  Ensure that all components (Open5GS, UERANSIM, PacketRusher) share the same PLMN, slice, and network parameters.

---

*End of Documentation*
```