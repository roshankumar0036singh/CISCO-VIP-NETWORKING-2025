# CISCO-VIP-NETWORKING-2025
# 🛰️ Auto Topology Generation & Network Simulation Tool

**Cisco Virtual Internship Program 2025 – Networking Problem Statement**  
A powerful automation tool to **parse network configurations**, **generate topologies**, **validate setups**, and **simulate network performance & failures**.

---

## 📖 Overview

This project automates the end-to-end process of **network topology creation and simulation**.  
It parses router, switch, and endpoint configurations, constructs a hierarchical topology, validates configuration compliance with industry best practices, and tests performance through detailed simulations.

The solution is designed to meet all **Cisco Internship Tool Requirements** and provides an optimized framework for modern network design, troubleshooting, and scalability analysis.

---

## ✨ Key Features

### 🔹 Auto Topology Generation
- Parses `.txt` configuration files for routers, switches, and PCs.
- Extracts:
  - Interface details (IPv4 addressing, MTU, bandwidth)
  - Routing protocols (OSPF, BGP)
  - VLAN configurations
  - Link relationships
- Builds an accurate **hierarchical network topology**.
- Generates visual layout from extracted data.

### 🔹 Configuration Validation & Optimization
- Detects:
  - Missing configuration components
  - Duplicate IP addresses in subnet
  - VLAN inconsistencies
  - Incorrect gateway assignments
  - MTU mismatches
  - Network loops
- Suggests:
  - Routing protocol changes (e.g., OSPF → BGP for scalability)
  - Node aggregation opportunities

### 🔹 Load Management & Traffic Awareness
- Analyzes bandwidth usage from configs.
- Estimates traffic loads per application type.
- Flags overloaded links & suggests balancing.
- Provides fallback paths for low-priority traffic.

### 🔹 Simulation & Fault Injection
**Day-1 Simulation Includes:**
- Device bring-up
- ARP table population
- OSPF/BGP neighbor discovery
- MTU mismatch impact testing

**Day-2 Simulation Includes:**
- Link failure injection & recovery
- Routing table reconvergence
- Compliance checks (31 tests in current run)
- Performance degradation analysis

### 🔹 Advanced Simulation Engine
- Multithreaded architecture (each network element runs in parallel).
- IPC communication using TCP/FIFO sockets.
- Pause and Resume simulation on demand.
- Per-node logging for complete visibility.

---

## 📁 Repository Structure
📦 AutoTopology-Network-Sim
┣ 📂 Config/ # Input configuration files
┃ ┣ R1.txt
┃ ┣ S1.txt
┃ ┗ ...
┣ 📂 simulation_engine/ # Simulation core logic
┣ 📂 topology_generator/ # Parser and graph builder
┣ 📂 validation_module/ # Rules and optimization checks
┣ 📂 reports/ # Generated analysis & results
┣ main.py # Entry point
┣ requirements.txt # Python dependencies
┗ README.md # Documentation

text

---

## 🔧 Installation

**Requirements:**
- Python 3.9+
- pip package manager

**Clone Repository:**
git clone https://github.com/YOUR_USERNAME/AutoTopology-Network-Sim.git
cd AutoTopology-Network-Sim

text

**Install Dependencies:**
pip install -r requirements.txt

text

---

## 🚀 Usage

### 1️⃣ Prepare Configuration Files
Place device configs in the `Config/` directory.  
Sample configs are available here:  
[Google Drive - Input Configs](https://drive.google.com/drive/folders/1IpQ6TzIeMt7BoVMD8mypGwCoBCGKeIBG?usp=drive_link)

---

### 2️⃣ Generate Network Topology
python main.py --generate-topology

text
**Outputs:**
- `reports/network_topology_<timestamp>.html` (Interactive Graph)
- JSON topology data

---

### 3️⃣ Validate Configurations
python main.py --validate-config

text

---

### 4️⃣ Run Simulations

**Day-1 Simulation:**
python main.py --simulate --day 1

text

**Day-2 Simulation (Fault Tests):**
python main.py --simulate --day 2

text

---

### 5️⃣ Pause / Resume Simulation
python main.py --pause
python main.py --resume

text

---

## 📊 Example Output

- **Network Bring-Up**
  - ✔ All devices up and stable
  - ✔ ARP tables populated
  - ✔ OSPF/BGP neighbors formed

- **Day-2 Tests**
  - Total tests: 31
  - Pass: 85
  - Fail: 10
  - Warnings: 5
  - Example Fault Injection:
    - Broken link R1 ↔ R2 → Network uptime maintained
    - Broken link R1 ↔ S1 → Automatic path adaptation

- **Reports Generated:**
  - JSON detailed analysis
  - Interactive HTML topology
  - Per-node simulation logs

---

## ✅ Cisco Internship Compliance

✔ Hierarchical topology creation  
✔ Bandwidth analysis/capacity verification  
✔ Load-balancing strategy recommendation  
✔ Missing component detection  
✔ Configuration checks & duplicate IP detection  
✔ VLAN & gateway validation  
✔ Routing protocol recommendations  
✔ MTU mismatch and network loop detection  
✔ Day-1 & Day-2 scenario execution  
✔ Fault injection testing & recovery analysis  
✔ Pause/Resume live simulation  
✔ Multithreaded architecture with IPC  

---

---

## 🚀 Usage

### 1️⃣ Prepare Configuration Files
Place device configs in the `Config/` directory.  
Sample configs are available here:  
[Google Drive - Input Configs](https://drive.google.com/drive/folders/1IpQ6TzIeMt7BoVMD8mypGwCoBCGKeIBG?usp=drive_link)

---

### 2️⃣ Generate Network Topology
**Outputs:**
- `reports/network_topology_<timestamp>.html` (Interactive Graph)
- JSON topology data

---

### 3️⃣ Validate Configurations

---

### 4️⃣ Run Simulations

**Day-1 Simulation:**

**Day-2 Simulation (Fault Tests):**

---

### 5️⃣ Pause / Resume Simulation

---

## 📊 Example Output

- **Network Bring-Up**
  - ✔ All devices up and stable
  - ✔ ARP tables populated
  - ✔ OSPF/BGP neighbors formed

- **Day-2 Tests**
  - Total tests: 31
  - Pass: 85
  - Fail: 10
  - Warnings: 5
  - Example Fault Injection:
    - Broken link R1 ↔ R2 → Network uptime maintained
    - Broken link R1 ↔ S1 → Automatic path adaptation

- **Reports Generated:**
  - JSON detailed analysis
  - Interactive HTML topology
  - Per-node simulation logs

---


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Description"`
4. Push branch: `git push origin feature-name`
5. Create a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** - see LICENSE file for details.

---

## 📬 Contact

**Developer:** Roshan Singh 
**Email:** roshankumar00036@gmail.com  
 

---




