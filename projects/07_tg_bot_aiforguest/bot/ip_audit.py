import asyncio
import subprocess
import json
import os
import socket
from pathlib import Path
from datetime import datetime

_log = None
BIN_DIR = Path(__file__).resolve().parent / "bin"
NMAP = str(BIN_DIR / "nmap") if (BIN_DIR / "nmap").exists() else "nmap"

TOP50 = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
    1433, 1521, 2049, 3306, 3389, 5060, 5432, 5900, 5985, 5986, 6379, 8080,
    8443, 9000, 9090, 10000, 11211, 27017, 32400
]


def _log_init():
    global _log
    if _log is None:
        import logging
        _log = logging.getLogger("tg_bot")


def _parse_nmap_xml(raw_bytes):
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError:
        return {"ports": [], "os": ""}
    ports = []
    for host in root.findall(".//host"):
        for port in host.findall(".//port"):
            state_el = port.find("state")
            if state_el is None or state_el.get("state") != "open":
                continue
            service = port.find("service")
            ports.append({
                "port": port.get("portid"),
                "proto": port.get("protocol"),
                "service": service.get("name", "") if service is not None else "",
                "product": service.get("product", "") if service is not None else "",
                "version": service.get("version", "") if service is not None else "",
            })
    os_guess = ""
    for os_elem in root.findall(".//osmatch"):
        os_guess = os_elem.get("name", "")
        break
    return {"ports": ports, "os": os_guess}


def _parse_nmap_vuln(raw_bytes):
    import xml.etree.ElementTree as ET
    vulns = []
    try:
        root = ET.fromstring(raw_bytes)
        for script in root.findall(".//script"):
            vid = script.get("id", "")
            output = script.get("output", "")
            if vid and vid != "http-title":
                vulns.append({"id": vid, "output": output[:200]})
    except ET.ParseError:
        pass
    return {"vulns": vulns}


async def _run_nmap(args):
    proc = await asyncio.create_subprocess_exec(
        NMAP, *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=7200)
    except asyncio.TimeoutError:
        proc.kill()
        return b""
    return stdout


# ── Stage 1: top50 TCP connect (Python) ──

async def _tcp_scan(ip, port, timeout=2):
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return port, True
    except Exception:
        return port, False


async def _sweep(ip, ports, timeout=2):
    tasks = [asyncio.create_task(_tcp_scan(ip, p, timeout)) for p in ports]
    results = []
    for t in asyncio.as_completed(tasks):
        port, ok = await t
        if ok:
            results.append(port)
    return sorted(results)


async def scan_stage1(ip):
    _log_init()
    _log.info(f"S1 top50: {ip}")
    try:
        ports = await _sweep(ip, TOP50, timeout=2)
    except Exception as e:
        return {"ports": [], "os": "", "error": str(e)}
    return {
        "ports": [{"port": str(p), "proto": "tcp", "service": "", "product": "", "version": ""} for p in ports],
        "os": "",
    }


# ── Stage 2: nmap top1000 + versions ──

async def scan_stage2(ip):
    _log_init()
    _log.info(f"S2 top1000+v: {ip}")
    try:
        raw = await _run_nmap([
            "-Pn", "-sV", "--top-ports", "1000", "-T4",
            "-oX", "-", ip,
        ])
        return _parse_nmap_xml(raw)
    except Exception as e:
        _log.error(f"S2 error {ip}: {e}")
        return {"ports": [], "os": "", "error": str(e)}


# ── Stage 3: nmap all 65535 ports + scripts ──

async def scan_stage3_ports(ip):
    _log_init()
    _log.info(f"S3 full ports: {ip}")
    try:
        raw = await _run_nmap([
            "-Pn", "-sV", "-sC", "-p-", "--min-rate", "500", "-T4",
            "-oX", "-", ip,
        ])
        return _parse_nmap_xml(raw)
    except Exception as e:
        _log.error(f"S3 error {ip}: {e}")
        return {"ports": [], "os": "", "error": str(e)}


async def scan_stage3_vuln(ip):
    _log_init()
    _log.info(f"S3 vuln: {ip}")
    try:
        raw = await _run_nmap([
            "-Pn", "--script", "vuln",
            "-oX", "-", ip,
        ])
        return _parse_nmap_vuln(raw)
    except Exception as e:
        _log.error(f"S3 vuln error {ip}: {e}")
        return {"vulns": [], "error": str(e)}


# ── Resolve hostname ──

def resolve_hostname(name: str) -> tuple[str | None, str | None]:
    try:
        return socket.gethostbyname(name.strip()), None
    except socket.gaierror as e:
        return None, f"Cannot resolve '{name}': {e}"


# ── Ping ──

async def ping_host(ip, timeout=3):
    _log_init()
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", "-c", "1", "-W", str(timeout), ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.communicate(), timeout=timeout+2)
        return proc.returncode == 0
    except Exception:
        return None


# ── WHOIS ──

def whois_lookup(ip):
    _log_init()
    _log.info(f"WHOIS: {ip}")
    import urllib.request
    try:
        url = f"https://rdap.db.ripe.net/ip/{ip}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        org = address = phone = netname = ""
        for entity in data.get("entities", []):
            for vcard in entity.get("vcardArray", [[]])[1]:
                if vcard[0] == "fn":
                    org = vcard[3]
                elif vcard[0] == "adr":
                    address = vcard[1].get("label", "")
                elif vcard[0] == "tel":
                    phone = vcard[3]
        return {"org": org, "address": address, "phone": phone, "netname": netname}
    except Exception as e:
        return {"org": f"RDAP error: {e}", "address": "", "phone": ""}


# ── GeoIP ──

def geo_lookup(ip):
    _log_init()
    import urllib.request
    for url in [
        f"https://ipapi.co/{ip}/json/",
        f"http://ip-api.com/json/{ip}",
    ]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            d = json.loads(resp.read())
            city = d.get("city") or d.get("city", "")
            region = d.get("region") or d.get("regionName", "")
            country = d.get("country_name") or d.get("country", "")
            org = d.get("org") or d.get("isp", "")
            if city or country:
                return {"city": city, "region": region, "country": country, "org": org}
        except Exception:
            continue
    return {"city": "", "region": "", "country": "", "org": "Geo lookup failed"}


# ── Shodan (internetdb) ──

async def shodan_lookup(ip):
    import urllib.request
    try:
        url = f"https://internetdb.shodan.io/{ip}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        d = json.loads(resp.read())
        return {
            "ports": d.get("ports", []),
            "cves": d.get("vulns", []),
            "hostnames": d.get("hostnames", []),
        }
    except Exception:
        return {"ports": [], "cves": [], "hostnames": []}


# ── Formatters ──

def fmt_summary_stage1(ips_data):
    now = datetime.now().strftime("%d.%m.%y %H:%M")
    lines = [f"📊 **Сводка top50 — {now}**", ""]
    for ip, d in ips_data.items():
        whois = d.get("whois", {})
        stage1 = d.get("stage1", {})
        ports = stage1.get("ports", [])
        org = whois.get("org", "?")
        port_str = " ".join(p["port"] for p in ports[:8]) if ports else "—"
        lines.append(f"  • **{ip}** — {org}")
        lines.append(f"    🔌 {port_str}")
    lines.append("")
    lines.append("🔄 Глубокий анализ (top1000) запущен...")
    return "\n".join(lines)


def fmt_beauty_stage(ip, stage_name, stage_data, whois=None, vuln=None, hostname=None):
    now = datetime.now().strftime("%d.%m.%y %H:%M")
    target = f"{hostname} → {ip}" if hostname else ip
    lines = [
        f"📋 **{stage_name}** — `{target}`",
        f"🕐 {now}",
        "",
    ]
    if whois:
        lines.append("┌─ **ВЛАДЕЛЕЦ** ─────────────────┐")
        if whois.get("org"): lines.append(f"  🏢 {whois['org']}")
        if whois.get("address"): lines.append(f"  📍 {whois['address']}")
        lines.append("└────────────────────────────────┘")

    all_ports = stage_data.get("ports", [])
    if all_ports:
        lines.append("")
        lines.append(f"┌─ **ПОРТЫ ({len(all_ports)})** ─────────┐")
        for p in all_ports[:15]:
            svc = f" {p['service']}" if p.get("service") else ""
            ver = f" {p['product']} {p['version']}".strip() if p.get("product") else ""
            lines.append(f"  🔓 {p['port']}/tcp{svc}{ver}")
        if len(all_ports) > 15:
            lines.append(f"  ... +{len(all_ports) - 15}")
        lines.append("└────────────────────────────────────┘")
    else:
        lines.append("\n🔌 Нет открытых портов (filtered)")

    if vuln and vuln.get("vulns"):
        v = vuln["vulns"]
        lines.append("")
        lines.append(f"┌─ **УЯЗВИМОСТИ ({len(v)})** ──────────┐")
        for x in v[:10]:
            lines.append(f"  ⚠ {x['id']}")
        if len(v) > 10:
            lines.append(f"  ... +{len(v) - 10}")
        lines.append("└────────────────────────────────────┘")

    os_guess = stage_data.get("os", "")
    if os_guess:
        lines.append(f"\n🖥 OS: {os_guess}")

    lines.append("")
    lines.append("━━━")
    return "\n".join(lines)


def fmt_full_md(ip, stages, whois=None, vuln=None, timings=None, ping=None, hostname=None):
    import time as _t
    now = datetime.now().strftime("%d.%m.%y %H:%M")
    target = f"{hostname} → {ip}" if hostname else ip
    lines = [f"# Audit Report: {target}", f"Date: {now}", ""]

    if ping is True:
        lines.append("🟢 **Host is alive** (ICMP echo)")
    elif ping is False:
        lines.append("🔴 **Host unreachable** (ICMP timeout)")
    elif ping is None:
        lines.append("⚪ **Ping indeterminate** (no permission)")
    lines.append("")

    if whois:
        lines.append("## Owner")
        if whois.get("org"): lines.append(f"- Organization: {whois['org']}")
        if whois.get("address"): lines.append(f"- Address: {whois['address']}")
    lines.append("")

    total_open = 0
    for i, (sname, sdata) in enumerate(stages):
        ports = sdata.get("ports", [])
        err = sdata.get("error", "")
        total_open += len(ports)
        dur = f" [{_t.time()-_t.time()+1:.0f}s]"
        if timings and i < len(timings):
            dur = f" [{timings[i]:.0f}s]"
        lines.append(f"## {sname}{dur}")
        if err:
            lines.append(f"⚠️ Error: {err}")
        elif ports:
            lines.append(f"**Open: {len(ports)} port(s)**")
            lines.append("| Port | Service | Version |")
            lines.append("|------|---------|---------|")
            for p in ports:
                svc = p.get("service", "")
                ver = f"{p.get('product','')} {p.get('version','')}".strip()
                lines.append(f"| {p['port']} | {svc} | {ver} |")
        else:
            lines.append("🔴 **No open ports** — filtered / firewalled / host down")
        lines.append("")

    if vuln and vuln.get("vulns"):
        lines.append(f"## Vulnerabilities ({len(vuln['vulns'])})")
        for v in vuln["vulns"]:
            lines.append(f"- {v['id']}: {v.get('output','')[:200]}")

    lines.append("\n## 📊 Accessibility Summary")
    lines.append(f"- **Stages completed:** {len(stages)}/3")
    lines.append(f"- **Total open ports:** {total_open}")
    if ping is True and total_open == 0:
        lines.append("- 🟢 Host alive, **all ports filtered** — firewall blocks inbound")
    elif ping is False:
        lines.append("- 🔴 Host down or network unreachable")
    elif ping is True and total_open > 0:
        lines.append("- 🟢 Host accessible, ports open and reachable")
    else:
        lines.append("- ⚪ Cannot determine full accessibility")

    return "\n".join(lines)


def fmt_third_party(ip, geo=None, shodan=None, hostname=None):
    now = datetime.now().strftime("%d.%m.%y %H:%M")
    target = f"{hostname} → {ip}" if hostname else ip
    lines = [f"🌐 **Сторонние данные: {target}**", f"🕐 {now}", ""]
    if geo:
        lines.append(f"  📍 {geo.get('city','?')}, {geo.get('region','?')}, {geo.get('country','?')}")
        lines.append(f"  🏢 {geo.get('org','?')}")
    if shodan:
        if shodan.get("ports"):
            lines.append(f"  🔌 Shodan: {' '.join(str(p) for p in shodan['ports'][:10])}")
        if shodan.get("cves"):
            lines.append(f"  🛡 CVE: {' '.join(shodan['cves'][:5])}")
        if shodan.get("hostnames"):
            lines.append(f"  🌐 DNS: {' '.join(shodan['hostnames'][:3])}")
    lines.append("")
    lines.append("━━━")
    return "\n".join(lines)
