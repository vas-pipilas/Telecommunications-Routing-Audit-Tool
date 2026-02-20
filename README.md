# 📡 Telecommunications Routing Audit Tool (TRAT) v1.0.0

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Build](https://img.shields.io/badge/build-stable-green.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**TRAT** is a production-grade, class-based Python utility engineered to automate the verification of **Number Portability (NP)** and **Flexible Number Routing (FNR)** data. Designed for network engineers and billing analysts, it validates routing integrity across distributed API node clusters.

---

## 🚀 Key Features

* **🛡️ High Availability (HA) Failover**: Implements a sequential round-robin strategy. If a primary node times out, the engine automatically attempts backup nodes.
* **🔍 Regex Data Extraction**: Uses advanced regular expressions to parse routing identifiers, ensuring resilience against varied API response formats.
* **📊 Multi-Format Reporting**: Generates human-readable Executive Summaries (`.txt`) and machine-readable Master Data (`.csv`) for Excel analysis.
* **🧹 Smart Sanitization**: Automated cleaning of MSISDN inputs (stripping quotes, spaces, and handling Greek-specific E.164 formats).
* **🖥️ Cross-Platform GUI**: Utilizes `tkinter` for native file selection across Windows, macOS, and Linux.

---

## 🛠️ System Architecture



The tool follows a **Modular Clean Architecture**:
1.  **Ingestion**: Parses semicolon-delimited CSVs and validates number integrity.
2.  **Processing**: Executes throttled HTTP GET requests with built-in retry logic.
3.  **Audit Logic**: Compares server-side Routing Numbers (RN) against local business logic (Inbound vs. Outbound routing).
4.  **Reporting**: Aggregates carrier statistics and node health metrics.

---

## 📖 How To Run

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed. This tool uses the standard library, so **no external pip installations are required** for the basic script!

### 2. Prepare Your Input File
Your source CSV should be semicolon-separated (`;`) and follow this general structure:
| Direction | MSISDN |
| :--- | :--- |
| inbound | 6930000000 |
| outbound | 6940000000 |

### 3. Execution
Navigate to the script directory and run:
```bash
python routing_audit_tool.py
