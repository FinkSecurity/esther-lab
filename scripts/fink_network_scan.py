#!/usr/bin/env python3
"""
Fink Security — Home Network Security Scanner
=============================================
Run this script on a computer connected to your home network.
It will scan your network for devices, open ports, and vulnerabilities,
then securely send the results to Fink Security for analysis.

Requirements: Python 3.8+
Recommended: pip install scapy python-nmap requests (for full scan mode)

Usage:
  sudo python3 fink_network_scan.py

Fink Security — https://finksecurity.com
"""

import os
import sys
import json
import uuid
import socket
import struct
import platform
import subprocess
import ipaddress
import threading
import datetime
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Detect optional dependencies ──────────────────────────────────────────────
try:
    import scapy.all as scapy
    HAS_SCAPY = True
except ImportError:
    HAS_SCAPY = False

try:
    import nmap
    HAS_NMAP = True
except ImportError:
    HAS_NMAP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Config ────────────────────────────────────────────────────────────────────
REPORT_ENDPOINT = "https://api.finksecurity.com/report-ingest"
SCAN_TIMEOUT    = 1.0       # seconds per port
MAX_WORKERS     = 50        # concurrent port scan threads
COMMON_PORTS    = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445,
    993, 995, 1080, 1433, 1723, 3306, 3389, 5900, 5985, 8080,
    8443, 8888, 9090, 27017, 32400, 49152
]

# MITRE ATT&CK mappings for common findings
MITRE_MAP = {
    21:    {"technique": "T1021.004", "name": "Remote Services: FTP", "tactic": "Lateral Movement", "risk": "HIGH"},
    22:    {"technique": "T1021.004", "name": "Remote Services: SSH", "tactic": "Lateral Movement", "risk": "MEDIUM"},
    23:    {"technique": "T1021.004", "name": "Remote Services: Telnet (unencrypted)", "tactic": "Lateral Movement", "risk": "CRITICAL"},
    25:    {"technique": "T1071.003", "name": "Application Layer Protocol: Mail", "tactic": "Command and Control", "risk": "MEDIUM"},
    53:    {"technique": "T1071.004", "name": "Application Layer Protocol: DNS", "tactic": "Command and Control", "risk": "LOW"},
    80:    {"technique": "T1190",     "name": "Exploit Public-Facing Application (HTTP)", "tactic": "Initial Access", "risk": "MEDIUM"},
    135:   {"technique": "T1021.003", "name": "Remote Services: DCOM (Windows)", "tactic": "Lateral Movement", "risk": "HIGH"},
    139:   {"technique": "T1021.002", "name": "Remote Services: SMB/NetBIOS", "tactic": "Lateral Movement", "risk": "HIGH"},
    443:   {"technique": "T1190",     "name": "Exploit Public-Facing Application (HTTPS)", "tactic": "Initial Access", "risk": "LOW"},
    445:   {"technique": "T1021.002", "name": "Remote Services: SMB (EternalBlue-class)", "tactic": "Lateral Movement", "risk": "CRITICAL"},
    1433:  {"technique": "T1190",     "name": "Exploit Public-Facing Application: MSSQL", "tactic": "Initial Access", "risk": "CRITICAL"},
    3306:  {"technique": "T1190",     "name": "Exploit Public-Facing Application: MySQL", "tactic": "Initial Access", "risk": "HIGH"},
    3389:  {"technique": "T1021.001", "name": "Remote Services: RDP", "tactic": "Lateral Movement", "risk": "CRITICAL"},
    5900:  {"technique": "T1021.005", "name": "Remote Services: VNC", "tactic": "Lateral Movement", "risk": "CRITICAL"},
    5985:  {"technique": "T1021.006", "name": "Remote Services: WinRM", "tactic": "Lateral Movement", "risk": "HIGH"},
    8080:  {"technique": "T1190",     "name": "Exploit Public-Facing Application (Alt HTTP)", "tactic": "Initial Access", "risk": "MEDIUM"},
    27017: {"technique": "T1190",     "name": "Exploit Public-Facing Application: MongoDB", "tactic": "Initial Access", "risk": "CRITICAL"},
}

RISK_ADVICE = {
    "CRITICAL": "Immediate action required. This service should be disabled or firewalled from your network.",
    "HIGH":     "Close attention needed. Ensure this service is up to date and access is restricted.",
    "MEDIUM":   "Monitor this service. Ensure strong credentials and keep software updated.",
    "LOW":      "Low risk but worth noting. Verify this service is intentional.",
}

# ── Banner ────────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════════════╗
║           FINK SECURITY — HOME NETWORK SCANNER               ║
║                   https://finksecurity.com                   ║
╚══════════════════════════════════════════════════════════════╝
"""

def print_banner():
    print(BANNER)
    print(f"  Platform : {platform.system()} {platform.release()}")
    print(f"  Python   : {sys.version.split()[0]}")
    print(f"  Scapy    : {'✓ installed (full scan)' if HAS_SCAPY else '✗ not found (basic scan)'}")
    print(f"  Nmap     : {'✓ installed (deep scan)' if HAS_NMAP else '✗ not found (basic scan)'}")
    print()


# ── Privilege check ───────────────────────────────────────────────────────────
def check_privileges():
    if platform.system() == "Windows":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("[!] This script requires Administrator privileges.")
            print("    Right-click and select 'Run as Administrator'.")
            sys.exit(1)
    else:
        if os.geteuid() != 0:
            print("[!] This script requires root privileges.")
            print("    Please run: sudo python3 fink_network_scan.py")
            sys.exit(1)


# ── Scan mode selection ───────────────────────────────────────────────────────
def select_scan_mode():
    print("  SCAN MODE")
    print("  ─────────────────────────────────────────────────────")
    print("  [1] Full Scan  — requires: pip install scapy python-nmap requests")
    print("      Uses ARP sweep, raw socket probing, nmap service detection.")
    print("      Most thorough — recommended.")
    print()
    print("  [2] Basic Scan — no additional installs needed")
    print("      Uses TCP connect, ICMP ping, stdlib only.")
    print("      Good coverage, slightly less depth.")
    print()

    if HAS_SCAPY and HAS_NMAP:
        print("  [auto] Full scan dependencies detected — defaulting to Full Scan.")
        print("  [!]  Full scan takes 2-5 minutes depending on network size.")
        print()
        return "full"

    choice = input("  Select mode [1/2]: ").strip()
    if choice == "1":
        print("  [!]  Full scan takes 2-5 minutes depending on network size.")
        print()
        missing = []
        if not HAS_SCAPY:    missing.append("scapy")
        if not HAS_NMAP:     missing.append("python-nmap")
        if not HAS_REQUESTS: missing.append("requests")
        if missing:
            print(f"\n  Installing missing packages: {' '.join(missing)}")
            # Try standard install first, fall back to --break-system-packages for macOS/Homebrew
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install"] + missing,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "--break-system-packages"] + missing,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError:
                    print("\n  [!] Auto-install failed. Please run manually:")
                    print(f"      pip install --break-system-packages {' '.join(missing)}")
                    print("      Then re-run: sudo python3 fink_network_scan.py")
                    sys.exit(1)
            print("  Installation complete. Please re-run the script.")
            sys.exit(0)
        return "full"
    return "basic"


# ── Network detection ─────────────────────────────────────────────────────────
def get_local_network():
    """Detect local IP and derive /24 network."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()

    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return local_ip, str(network)


def get_gateway():
    """Attempt to detect default gateway."""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output("ipconfig", text=True)
            for line in result.splitlines():
                if "Default Gateway" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        gw = parts[1].strip()
                        if gw:
                            return gw
        elif platform.system() == "Darwin":
            # macOS — use netstat
            result = subprocess.check_output(["netstat", "-rn"], text=True)
            for line in result.splitlines():
                if line.startswith("default") or line.startswith("0.0.0.0"):
                    parts = line.split()
                    if len(parts) >= 2:
                        gw = parts[1]
                        # Filter out link-local and non-IP entries
                        try:
                            ipaddress.IPv4Address(gw)
                            return gw
                        except Exception:
                            continue
        else:
            result = subprocess.check_output(["ip", "route"], text=True)
            for line in result.splitlines():
                if line.startswith("default"):
                    return line.split()[2]
    except Exception:
        pass
    return "unknown"


# ── Host discovery ────────────────────────────────────────────────────────────
def arp_sweep(network: str) -> list:
    """Full mode: ARP sweep using scapy."""
    print(f"  [*] ARP sweep: {network}")
    import scapy.all as scapy
    arp = scapy.ARP(pdst=network)
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result = scapy.srp(packet, timeout=2, verbose=False)[0]

    hosts = []
    for _, received in result:
        hosts.append({
            "ip":  received.psrc,
            "mac": received.hwsrc,
            "vendor": lookup_vendor(received.hwsrc),
            "device_type": classify_device(received.hwsrc, received.psrc),
        })
    return hosts


def ping_sweep(network: str) -> list:
    """Basic mode: TCP connect sweep."""
    print(f"  [*] Ping sweep: {network}")
    net = ipaddress.IPv4Network(network, strict=False)
    hosts = []
    lock = threading.Lock()

    def probe(ip):
        ip_str = str(ip)
        # Try TCP connect on port 80 and 443
        for port in [80, 443, 22, 445]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((ip_str, port)) == 0:
                    s.close()
                    with lock:
                        hosts.append({
                            "ip": ip_str,
                            "mac": "unknown",
                            "vendor": "unknown",
                            "device_type": "unknown",
                        })
                    return
                s.close()
            except Exception:
                pass

    with ThreadPoolExecutor(max_workers=100) as ex:
        ex.map(probe, net.hosts())

    return hosts


def lookup_vendor(mac: str) -> str:
    """Basic OUI lookup from MAC prefix."""
    oui_map = {
        "00:50:56": "VMware",
        "00:0c:29": "VMware",
        "b8:27:eb": "Raspberry Pi",
        "dc:a6:32": "Raspberry Pi",
        "00:1a:11": "Google (Nest/Home)",
        "f4:f5:d8": "Google (Nest/Home)",
        "74:da:38": "Amazon (Echo/Fire)",
        "fc:65:de": "Amazon (Echo/Fire)",
        "18:b4:30": "Nest Labs",
        "00:17:88": "Philips Hue",
        "ec:fa:bc": "Apple",
        "f0:18:98": "Apple",
        "3c:22:fb": "Apple",
        "00:25:00": "Apple",
        "00:1e:52": "Apple",
        "28:cf:e9": "Apple",
        "ac:bc:32": "Apple",
        "00:e0:4c": "Realtek",
        "00:1d:60": "Ubiquiti",
        "04:18:d6": "Ubiquiti",
        "e4:95:6e": "Asus",
        "50:eb:f6": "Asus",
        "c8:3a:35": "TP-Link",
        "50:c7:bf": "TP-Link",
        "10:fe:ed": "TP-Link",
        "b0:be:76": "Netgear",
        "a0:40:a0": "Netgear",
        "20:e5:2a": "Xiaomi",
        "f8:a2:d6": "Xiaomi",
    }
    prefix = mac[:8].lower().replace("-", ":")
    return oui_map.get(prefix, "unknown")


def classify_device(mac: str, ip: str) -> str:
    """Guess device type from MAC vendor."""
    vendor = lookup_vendor(mac).lower()
    if "apple" in vendor:          return "Apple device (Mac/iPhone/iPad)"
    if "raspberry" in vendor:      return "Raspberry Pi (single-board computer)"
    if "google" in vendor:         return "Google smart home device"
    if "amazon" in vendor:         return "Amazon Echo/Fire device"
    if "philips" in vendor:        return "Smart lighting (Philips Hue)"
    if "nest" in vendor:           return "Nest smart home device"
    if "ubiquiti" in vendor:       return "Network equipment (Ubiquiti)"
    if "tp-link" in vendor:        return "Network device (TP-Link)"
    if "netgear" in vendor:        return "Network device (Netgear)"
    if "asus" in vendor:           return "Network/computing device (Asus)"
    if "xiaomi" in vendor:         return "Xiaomi IoT device"
    if "vmware" in vendor:         return "Virtual machine"
    return "Unknown device"


def get_hostname(ip: str) -> str:
    result = ["unknown"]
    def _resolve():
        try:
            result[0] = socket.gethostbyaddr(ip)[0]
        except Exception:
            pass
    t = threading.Thread(target=_resolve, daemon=True)
    t.start()
    t.join(timeout=1.5)
    return result[0]


# ── Port scanning ─────────────────────────────────────────────────────────────
def scan_ports_basic(ip: str, ports: list) -> list:
    """TCP connect port scan."""
    open_ports = []
    lock = threading.Lock()

    def probe(port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(SCAN_TIMEOUT)
            if s.connect_ex((ip, port)) == 0:
                banner = grab_banner(s, port)
                s.close()
                with lock:
                    open_ports.append({"port": port, "banner": banner})
            else:
                s.close()
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        ex.map(probe, ports)

    return sorted(open_ports, key=lambda x: x["port"])


def grab_banner(sock, port: int) -> str:
    """Attempt to grab service banner."""
    try:
        if port in [80, 8080, 8443, 8888]:
            sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        else:
            sock.send(b"\r\n")
        sock.settimeout(0.5)
        return sock.recv(256).decode("utf-8", errors="ignore").strip()[:100]
    except Exception:
        return ""


def scan_ports_nmap(ip: str) -> list:
    """Full mode: nmap service version scan."""
    import nmap as nm
    scanner = nm.PortScanner()
    scanner.scan(ip, arguments=f"-sV -p {','.join(map(str, COMMON_PORTS))} --open -T4")
    open_ports = []
    if ip in scanner.all_hosts():
        for proto in scanner[ip].all_protocols():
            for port in scanner[ip][proto]:
                state = scanner[ip][proto][port]["state"]
                if state == "open":
                    open_ports.append({
                        "port":    port,
                        "service": scanner[ip][proto][port].get("name", "unknown"),
                        "version": scanner[ip][proto][port].get("version", ""),
                        "product": scanner[ip][proto][port].get("product", ""),
                        "banner":  "",
                    })
    return sorted(open_ports, key=lambda x: x["port"])


# ── Vulnerability analysis ────────────────────────────────────────────────────
def analyze_findings(hosts: list) -> dict:
    """Map open ports to MITRE ATT&CK and generate risk assessment."""
    findings = []
    risk_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for host in hosts:
        for port_info in host.get("open_ports", []):
            port = port_info["port"]
            if port in MITRE_MAP:
                mitre = MITRE_MAP[port]
                risk_summary[mitre["risk"]] += 1
                findings.append({
                    "host":       host["ip"],
                    "hostname":   host.get("hostname", "unknown"),
                    "device":     host.get("device_type", "unknown"),
                    "port":       port,
                    "service":    port_info.get("service", port_info.get("banner", "unknown")),
                    "mitre_id":   mitre["technique"],
                    "mitre_name": mitre["name"],
                    "tactic":     mitre["tactic"],
                    "risk":       mitre["risk"],
                    "advice":     RISK_ADVICE[mitre["risk"]],
                })

    findings.sort(key=lambda x: ["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(x["risk"]))
    return {"findings": findings, "risk_summary": risk_summary}


# ── System info ───────────────────────────────────────────────────────────────
def get_system_info() -> dict:
    info = {
        "os":       platform.system(),
        "version":  platform.version(),
        "hostname": socket.gethostname(),
        "arch":     platform.machine(),
    }

    # Check firewall status
    try:
        if platform.system() == "Linux":
            result = subprocess.check_output(["ufw", "status"], text=True, stderr=subprocess.DEVNULL)
            info["firewall"] = "ufw: " + result.splitlines()[0]
        elif platform.system() == "Darwin":
            result = subprocess.check_output(
                ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                text=True, stderr=subprocess.DEVNULL
            )
            info["firewall"] = result.strip()
        elif platform.system() == "Windows":
            result = subprocess.check_output(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                text=True, stderr=subprocess.DEVNULL
            )
            info["firewall"] = result.strip()[:200]
    except Exception:
        info["firewall"] = "unable to determine"

    # Check for open sharing services on this machine
    info["open_shares"] = []
    try:
        if platform.system() != "Windows":
            result = subprocess.check_output(["ss", "-tlnp"], text=True, stderr=subprocess.DEVNULL)
            info["open_shares"] = [l.strip() for l in result.splitlines() if "LISTEN" in l][:20]
    except Exception:
        pass

    return info


# ── Report builder ────────────────────────────────────────────────────────────
def build_report(scan_id, scan_mode, local_ip, gateway, network,
                 hosts, analysis, system_info, job_id) -> dict:
    return {
        "report_version": "1.0",
        "scan_id":        scan_id,
        "job_id":         job_id,
        "scan_mode":      scan_mode,
        "timestamp":      datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "network": {
            "local_ip":    local_ip,
            "gateway":     gateway,
            "subnet":      network,
            "hosts_found": len(hosts),
        },
        "system_info": system_info,
        "hosts":        hosts,
        "analysis":     analysis,
        "scan_meta": {
            "ports_checked": len(COMMON_PORTS),
            "scan_duration": "",
        }
    }


def save_report_local(report: dict) -> str:
    """Save JSON report to desktop."""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.expanduser("~")
    filename = f"fink-network-scan-{report['scan_id'][:8]}.json"
    path = os.path.join(desktop, filename)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    return path


def send_report(report: dict, job_id: str) -> bool:
    """POST report to Fink Security API."""
    if not HAS_REQUESTS:
        try:
            import urllib.request
            data = json.dumps({"job_id": job_id, "report": report}).encode()
            req = urllib.request.Request(
                REPORT_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=15)
            return True
        except Exception as e:
            print(f"  [!] Send failed: {e}")
            return False
    else:
        import requests
        try:
            r = requests.post(
                REPORT_ENDPOINT,
                json={"job_id": job_id, "report": report},
                timeout=15
            )
            return r.status_code == 200
        except Exception as e:
            print(f"  [!] Send failed: {e}")
            return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print_banner()
    check_privileges()

    # Get job_id from environment or argument (passed by handler.py in task)
    job_id = os.environ.get("FINK_JOB_ID", "manual-" + str(uuid.uuid4())[:8])
    scan_id = str(uuid.uuid4())

    # Scan mode selection
    scan_mode = select_scan_mode()
    print()

    # Network detection
    local_ip, network = get_local_network()
    gateway = get_gateway()
    print(f"  [*] Local IP  : {local_ip}")
    print(f"  [*] Gateway   : {gateway}")
    print(f"  [*] Network   : {network}")
    print()

    # System info
    print("  [*] Collecting system information...")
    system_info = get_system_info()

    # Host discovery
    print()
    import time
    t_start = time.time()

    if scan_mode == "full" and HAS_SCAPY:
        hosts = arp_sweep(network)
    else:
        hosts = ping_sweep(network)

    # Always include local machine
    local_found = any(h["ip"] == local_ip for h in hosts)
    if not local_found:
        hosts.append({
            "ip": local_ip,
            "mac": "local",
            "vendor": platform.node(),
            "device_type": f"This computer ({platform.system()})",
        })

    print(f"  [+] Found {len(hosts)} hosts\n")

    # Port scanning + hostname resolution
    print("  [*] Scanning ports and resolving hostnames...")
    for i, host in enumerate(hosts):
        ip = host["ip"]
        print(f"  [{i+1}/{len(hosts)}] {ip}", end=" ", flush=True)
        host["hostname"] = get_hostname(ip)

        if scan_mode == "full" and HAS_NMAP:
            host["open_ports"] = scan_ports_nmap(ip)
        else:
            host["open_ports"] = scan_ports_basic(ip, COMMON_PORTS)

        print(f"— {len(host['open_ports'])} open ports")

    # Analysis
    print("\n  [*] Analyzing findings and mapping to MITRE ATT&CK...")
    analysis = analyze_findings(hosts)

    # Duration
    duration = round(time.time() - t_start, 1)

    # Build report
    report = build_report(scan_id, scan_mode, local_ip, gateway,
                          network, hosts, analysis, system_info, job_id)
    report["scan_meta"]["scan_duration"] = f"{duration}s"

    # Save locally
    local_path = save_report_local(report)
    print(f"\n  [+] Report saved: {local_path}")

    # Send to Fink Security
    print("  [*] Sending report to Fink Security for analysis...")
    success = send_report(report, job_id)

    if success:
        print("  [+] Report received. ESTHER will begin analysis shortly.")
        print("      You'll receive your full security assessment by email.")
    else:
        print("  [!] Could not send report automatically.")
        print(f"      Please email {local_path} to hello@finksecurity.com")
        print(f"      with subject: Network Scan Report — {job_id}")

    # Print summary to terminal
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                     SCAN SUMMARY                            ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Hosts discovered : {len(hosts):<41}║")
    print(f"║  Scan duration    : {duration}s{'':<40}║")
    rs = analysis["risk_summary"]
    print(f"║  CRITICAL findings: {rs['CRITICAL']:<41}║")
    print(f"║  HIGH findings    : {rs['HIGH']:<41}║")
    print(f"║  MEDIUM findings  : {rs['MEDIUM']:<41}║")
    print(f"║  LOW findings     : {rs['LOW']:<41}║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if rs["CRITICAL"] > 0:
        print("  ⚠  CRITICAL issues found. Review your full report immediately.")
    elif rs["HIGH"] > 0:
        print("  ⚠  HIGH risk issues found. Review your report soon.")
    else:
        print("  ✓  No critical issues detected. Full report on the way.")
    print()


if __name__ == "__main__":
    main()
