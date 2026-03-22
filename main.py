"""

Un outil de scan professionnel, structuré, rapide, avec analyse avancée des réseaux + dashboard CLI + enrichissement CVE (API publique)
👉 sans fonctions offensives illégales (pas de bruteforce / exploitation)

🚀 🔥 CE QUE TU VOUS ALLEZ AVOIR : 

✅ Scan ultra rapide (threads)
✅ Multi-IP / CIDR
✅ Détection services + risques
✅ Enrichissement CVE (API NVD)
✅ OSINT IP
✅ Score vulnérabilité
✅ Export JSON / CSV / PDF
✅ Interface CLI stylée
✅ Code modulaire propre

⚠️ AVANT DE COMMENCER

Installe dépendances :

pkg install nmap curl
pip install reportlab requests

Innstallation :
git clone https://github.com/KAD78/KaB_Scan.git
cd KaB_Scan
python main.py


"""


import socket
import subprocess
import shutil
import json
import csv
import ipaddress
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ----------------------------
# UI COLORS
# ----------------------------
class C:
    R = '\033[91m'
    G = '\033[92m'
    Y = '\033[93m'
    B = '\033[94m'
    C = '\033[96m'
    X = '\033[0m'


# ----------------------------
# TOOL CHECK
# ----------------------------
def tool(name):
    return shutil.which(name) is not None


# ----------------------------
# FAST PORT SCAN
# ----------------------------
def scan_port(ip, port):
    try:
        s = socket.socket()
        s.settimeout(0.3)
        if s.connect_ex((ip, port)) == 0:
            return port
    except:
        pass
    return None


def scan_ports(ip):
    print(f"{C.C}[+] Scan rapide {ip}{C.X}")
    open_ports = []

    with ThreadPoolExecutor(max_workers=150) as executor:
        results = executor.map(lambda p: scan_port(ip, p), range(1, 1001))

    for r in results:
        if r:
            print(f"{C.G}[OPEN]{C.X} {ip}:{r}")
            open_ports.append(r)

    return open_ports


# ----------------------------
# NMAP VULN SCAN
# ----------------------------
def nmap_scan(ip):
    if not tool("nmap"):
        print(f"{C.R}[!] Nmap absent{C.X}")
        return ""

    print(f"{C.C}[+] Nmap scan {ip}{C.X}")

    try:
        r = subprocess.run(
            ["nmap", "-sV", "--script=vuln", "-Pn", ip],
            capture_output=True,
            text=True
        )
        print(r.stdout)
        return r.stdout
    except:
        return ""


# ----------------------------
# OSINT IP
# ----------------------------
def osint(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = r.json()

        print(f"{C.B}Pays:{C.X} {data.get('country')}")
        print(f"{C.B}ISP:{C.X} {data.get('isp')}")

        return data
    except:
        return {}


# ----------------------------
# CVE LOOKUP (NVD API)
# ----------------------------
def cve_lookup(service):
    try:
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={service}"
        r = requests.get(url, timeout=5)
        data = r.json()

        vulns = []

        for item in data.get("vulnerabilities", [])[:3]:
            cve = item["cve"]["id"]
            vulns.append(cve)

        return vulns
    except:
        return []


# ----------------------------
# ANALYSIS
# ----------------------------
def analyze(ip, ports):
    print(f"{C.C}[+] Analyse {ip}{C.X}")

    findings = []

    if 23 in ports:
        findings.append("TELNET ouvert (critique)")

    if 22 in ports:
        findings.append("SSH exposé")

    if len(ports) > 15:
        findings.append("Beaucoup de ports ouverts")

    for f in findings:
        print(f"{C.Y}[!] {f}{C.X}")

    return findings


# ----------------------------
# SCORE
# ----------------------------
def score_ports(ports):
    weights = {21:2, 22:1, 23:3, 80:1, 443:1, 3306:3}
    return sum(weights.get(p, 0) for p in ports)


# ----------------------------
# EXPORTS
# ----------------------------
def export(ip, ports, score, findings):
    data = {
        "ip": ip,
        "ports": ports,
        "score": score,
        "findings": findings,
        "date": str(datetime.now())
    }

    # JSON
    with open(f"{ip}.json", "w") as f:
        json.dump(data, f, indent=4)

    # CSV
    with open(f"{ip}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["IP", "Port"])
        for p in ports:
            w.writerow([ip, p])

    # PDF
    doc = SimpleDocTemplate(f"{ip}.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph(f"Scan Report - {ip}", styles["Title"]))
    content.append(Paragraph(f"Score: {score}", styles["Normal"]))

    for fnd in findings:
        content.append(Paragraph(f"- {fnd}", styles["Normal"]))

    for p in ports:
        content.append(Paragraph(f"Port ouvert: {p}", styles["Normal"]))

    doc.build(content)

    print(f"{C.G}[+] Export complet OK{C.X}")


# ----------------------------
# CIDR SUPPORT
# ----------------------------
def expand(target):
    try:
        net = ipaddress.ip_network(target, strict=False)
        return [str(ip) for ip in net.hosts()]
    except:
        return [target]


# ----------------------------
# MAIN
# ----------------------------
def main():
    print(f"""{C.G}
███████╗ ██████╗ █████╗ ███╗   ██╗
██╔════╝██╔════╝██╔══██╗████╗  ██║
███████╗██║     ███████║██╔██╗ ██║
╚════██║██║     ██╔══██║██║╚██╗██║
███████║╚██████╗██║  ██║██║ ╚████║
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
{C.X}
""")

    target = input("Target (IP ou CIDR): ")
    targets = expand(target)

    for ip in targets:
        print(f"\n{C.B}===== {ip} ====={C.X}")

        ports = scan_ports(ip)
        findings = analyze(ip, ports)
        score = score_ports(ports)

        print(f"{C.Y}Score: {score}{C.X}")

        nmap_scan(ip)
        osint(ip)

        # Exemple CVE lookup simple
        if ports:
            print(f"{C.C}[+] CVE possibles:{C.X}")
            cves = cve_lookup("http")
            for c in cves:
                print(f" - {c}")

        export(ip, ports, score, findings)

    print(f"\n{C.G}[✓] Scan terminé{C.X}")


if __name__ == "__main__":
    main()
  
