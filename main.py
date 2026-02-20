"""
Telecommunications Routing Audit Tool (TRAT)
-------------------------------------------
A robust, class-based utility designed to automate the verification of 
Number Portability (NP) routing data across a distributed node cluster.

Key Features:
- Sequential Node Failover (High Availability)
- Regular Expression Data Extraction
- Multi-format Reporting (TXT/CSV)
- Automated Data Sanitization
"""

import urllib.request
import os
import tkinter as tk
from tkinter import filedialog
import re
import time
from datetime import datetime
from collections import Counter
import csv

class RoutingAuditEngine:
    """
    Orchestrates the lifecycle of a routing audit, from file ingestion
    to multi-node API querying and final report generation.
    """

    def __init__(self):
        """
        Initializes the engine with generalized cluster configurations
        and a randomized carrier registry.
        """
        # Node Cluster: Defines the redundant API endpoints for failover logic
        self._NODES = ["10.25.100.50", "10.25.100.51", "10.25.110.50", "10.25.110.51"]
        self._PORT = "18092"
        self._API_ENDPOINT = "/api/v1/get_routing?id="
        
        # Internal Identifier: Used to distinguish 'Home' vs 'External' routing
        self._HOME_NETWORK_ID = "888000" 
        
        # Carrier Registry: Mapping table for prefix-based provider identification
        self._CARRIER_REGISTRY = {
            "1010": "Alpha_Telecom_Global",
            "1020": "Beta_Mobile_Networks",
            "2010": "Delta_MVNO_Services",
            "2020": "Epsilon_Fixed_Line",
            "3050": "Zeta_Cloud_Voice",
            "4090": "Omega_Infrastructure"
        }
        
        # State Management: Tracks health of the cluster during the session
        self.node_status_map = {ip: "PENDING" for ip in self._NODES}

    def _match_carrier(self, routing_id):
        """
        Extracts the carrier identity based on the Routing Number prefix.
        
        Args:
            routing_id (str): The full routing string returned by the server.
        Returns:
            str: Human-readable carrier name or unknown placeholder.
        """
        if not routing_id or len(routing_id) < 4:
            return "UNKNOWN_PROVIDER"
        prefix = routing_id[:4]
        return self._CARRIER_REGISTRY.get(prefix, f"Unregistered_Prefix_{prefix}")

    def _validate_input_format(self, raw_data):
        """
        Sanitizes raw input strings and validates against E.164-style requirements.
        
        Args:
            raw_data (str): Unfiltered string from CSV segment.
        Returns:
            tuple: (bool success_flag, str cleaned_value)
        """
        # Strip whitespace and common CSV delimiters
        clean_str = raw_data.strip().replace('"', '').replace("'", "")
        
        # Validation Logic: Requires 10-digit numeric string
        if len(clean_str) == 10 and clean_str.isdigit():
            return True, clean_str
        return False, clean_str

    def _parse_routing_id(self, response_body):
        """
        Parses the Routing ID from the HTTP response using Regular Expressions.
        Ensures resilience against varied whitespace or formatting in API responses.
        """
        pattern = r'RoutingID:\s*(\d+)'
        match = re.search(pattern, response_body, re.IGNORECASE)
        return match.group(1) if match else None

    def _fetch_with_redundancy(self, target_id):
        """
        Executes an HTTP GET request with a built-in failover mechanism.
        If the primary node is unreachable, it sequentially attempts backups.
        
        Args:
            target_id (str): The MSISDN to query.
        Returns:
            tuple: (str raw_response, str routing_id, str active_node_ip)
        """
        for node_ip in self._NODES:
            request_url = f"http://{node_ip}:{self._PORT}{self._API_ENDPOINT}{target_id}"
            try:
                # 2-second timeout: Critical for maintaining batch throughput
                with urllib.request.urlopen(request_url, timeout=2) as response:
                    content = response.read().decode('utf-8').strip()
                    extracted_rn = self._parse_routing_id(content)
                    
                    # Valid response must contain a parsable Routing ID
                    if extracted_rn:
                        self.node_status_map[node_ip] = "HEALTHY"
                        return content, extracted_rn, node_ip
            except Exception:
                # Mark node as unreachable and attempt the next in list
                self.node_status_map[node_ip] = "TIMEOUT/UNREACHABLE"
                continue
        
        return "CRITICAL_CONNECTION_FAILURE", "000000", "NONE"

    def execute_audit(self):
        """
        Entry point for the audit workflow. Handles UI, Ingestion, 
        Processing, and delegation of Export tasks.
        """
        print("-" * 60)
        print(" [SYSTEM] INITIALIZING ROUTING AUDIT ENGINE")
        print("-" * 60)

        # UI: Suppress main Tkinter window and trigger File Picker
        gui_root = tk.Tk()
        gui_root.withdraw()
        gui_root.attributes("-topmost", True)
        
        source_file = filedialog.askopenfilename(
            initialdir=os.path.expanduser("~"),
            title="Select Audit Source File",
            filetypes=(("CSV files", "*.csv"), ("all files", "*.*"))
        )
        
        if not source_file:
            print("[!] Process Terminated: No input file provided.")
            return

        # 1. INGESTION PHASE: Parse CSV and identify MSISDN targets
        work_queue = []
        try:
            with open(source_file, mode='r', encoding='utf-8-sig') as f:
                for line in f:
                    segments = line.split(';')
                    if not segments: continue
                    
                    # Column 0 is expected to be 'Direction' (Inbound/Outbound)
                    traffic_dir = segments[0].strip().lower()
                    
                    # Iterate through segments to find a valid MSISDN
                    for item in segments:
                        is_valid, clean_msisdn = self._validate_input_format(item)
                        if is_valid:
                            work_queue.append((traffic_dir, clean_msisdn))
                            break
        except Exception as err:
            print(f"[!] File Ingestion Error: {err}"); return

        # 2. EXECUTION PHASE: Query nodes and validate logic
        results = []
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"[*] Queue Size: {len(work_queue)} records. Processing...")

        for t_direction, msisdn in work_queue:
            raw_body, rn, source_node = self._fetch_with_redundancy(msisdn)
            carrier = self._match_carrier(rn)
            
            # Audit Logic: Verifies if the routing matches the intended direction
            audit_passed = False
            if "inbound" in t_direction and rn == self._HOME_NETWORK_ID:
                audit_passed = True
            elif "outbound" in t_direction and rn != self._HOME_NETWORK_ID and rn != "000000":
                audit_passed = True

            results.append({
                'run_time': datetime.now().strftime("%H:%M:%S"),
                'audit_status': "PASSED" if audit_passed else "FAILED",
                'type': t_direction.upper(),
                'id': msisdn,
                'routing_rn': rn,
                'entity': carrier,
                'source_node': source_node
            })
            # Respectful delay to prevent accidental DoS on API nodes
            time.sleep(0.05) 

        # 3. EXPORT PHASE: Finalize report generation
        self._export_data(source_file, results, run_id)

    def _export_data(self, original_path, data_set, suffix):
        """
        Generates comprehensive reports in both TXT and CSV formats.
        Utilizes OS-agnostic pathing for cross-platform compatibility.
        """
        dir_name = os.path.dirname(original_path)
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        
        report_txt = os.path.join(dir_name, f"{base_name}_REPORT_{suffix}.txt")
        report_csv = os.path.join(dir_name, f"{base_name}_DATA_{suffix}.csv")

        # Compile Statistics
        fails = [r for r in data_set if r['audit_status'] == "FAILED"]
        stats = Counter([r['entity'] for r in data_set])

        # Terminal Visualization
        print("\n" + "="*60)
        print(f" AUDIT COMPLETE | SUCCESS RATE: {((len(data_set)-len(fails))/len(data_set))*100:.1f}%")
        print(f" NODE HEALTH: {self.node_status_map}")
        print("="*60)

        # Write Machine-Readable Master Data
        with open(report_csv, "w", newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=data_set[0].keys())
            writer.writeheader()
            writer.writerows(data_set)

        # Write Human-Readable Executive Summary
        with open(report_txt, "w", encoding='utf-8') as f:
            f.write(f"ROUTING AUDIT SUMMARY - {suffix}\n")
            f.write(f"Status: COMPLETE | Total: {len(data_set)} | Failures: {len(fails)}\n")
            f.write("-" * 40 + "\nCluster Health:\n")
            for node, status in self.node_status_map.items():
                f.write(f"{node}: {status}\n")
            f.write("-" * 40 + "\nCarrier Distribution:\n")
            for carrier, count in stats.items():
                f.write(f"{carrier}: {count}\n")

        print(f"[SUCCESS] Reports generated in {dir_name}")
        input("\nAudit Complete. Press [ENTER] to exit...")

if __name__ == "__main__":
    # Execute the Audit Logic
    app = RoutingAuditEngine()
    app.execute_audit()
