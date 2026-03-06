# Internet Reconnaissance Exercise: Findings Template
## Part 3: Expected Findings Structure & MITRE ATT&CK Mapping

**Author:** ESTHER  
**Date:** 2026-03-06  
**Document Type:** Template (Awaiting Live Data)  

---

## Exercise Findings Format

Each discovered webcam will be documented in this structure:

### Finding Template

```
## [CAMERA_ID]: [Camera Type] - [Location/Description]

**Discovery Method:** [How it was found]  
**Query Used:** [Exact search/command]  
**Source:** [Shodan/Google/Censys/etc]  

### Endpoint Details
- **URL/IP**: [IP:Port or FQDN]
- **Port**: [Port number]
- **Protocol**: [HTTP/HTTPS/RTSP/Other]
- **Status Code**: [HTTP response or connection state]

### Infrastructure Fingerprinting
- **Manufacturer**: [Axis/Hikvision/Dahua/Mobotix/etc]
- **Model**: [Specific camera model if identifiable]
- **Firmware Version**: [If accessible]
- **Server Header**: [HTTP Server response]

### Access Assessment
- **Authentication**: [Present/Absent/Weak]
- **Encryption**: [HTTP/HTTPS/TLS Version]
- **Default Credentials**: [Known weak defaults for this model]
- **Management Interface**: [Exposed/Protected/Not found]

### Risk Assessment
- **CVSS Score**: [If applicable]
- **Exposure Level**: [Critical/High/Medium/Low]
- **Live Stream Access**: [Yes/No/Restricted]
- **Metadata Visible**: [Timestamp/Location/Model data]

### MITRE ATT&CK Mapping
- **Primary Technique**: T1593 (Search Open Websites/Domains)
- **Secondary Techniques**: 
  - T1590.001 (Gather Victim Network Information — Active Scanning)
  - T1592.003 (Gather Victim Host Information — Firmware)
  - T1589.001 (Gather Victim Identity Information — Credentials)

### Remediation
- [Specific fix for this camera model]
- [Best practice recommendation]
- [Configuration hardening steps]

### Notes
[Additional observations]

---

## Expected Finding Categories (Boulder, CO)

### Category 1: University/Research Institutions
**Expected Targets:**
- University of Colorado (CU Boulder) research lab cameras
- Environmental monitoring stations
- Building automation systems

**Typical Vulnerabilities:**
- Publicly indexed building access cameras
- Research equipment monitoring feeds
- Weather station webcams

### Category 2: Public Infrastructure
**Expected Targets:**
- Traffic cameras (city/county management)
- Municipal building entrances
- Public parking lot monitoring
- Street-level traffic monitoring

**Typical Vulnerabilities:**
- Exposed management interfaces
- Default credentials on city infrastructure
- Poor access controls

### Category 3: Business/Commercial
**Expected Targets:**
- Office building lobby cameras
- Business district surveillance
- Shopping centers (publicly exposed)
- Hotel/lodging lobby cameras

**Typical Vulnerabilities:**
- Weak authentication
- MJPEG streams without encryption
- Port forwarding from internal networks

### Category 4: Residential (Accidental Exposure)
**Expected Targets:**
- Home security systems misconfigured
- Small business front-facing cameras
- Neighbor-to-neighbor exposure through NAT

**Typical Vulnerabilities:**
- UPnP/port mapping misconfigurations
- Shared WiFi networks with public access
- Cloud service account breaches

---

## Query Execution Reference

### Shodan Queries to Execute (When API Available)

```bash
# Broad search: All cameras in Boulder network range
shodan search "port:8080 Boulder Colorado"
shodan search "port:8081 location:Boulder"
shodan search "port:554 rtsp location:Boulder"

# Manufacturer-specific
shodan search "Server: Axis Communications Boulder"
shodan search "Hikvision-Webs Boulder Colorado"
shodan search "Dahua IP Camera Boulder"

# Vulnerability patterns
shodan search "default username admin port:8080 Boulder"
shodan search "MJPEG Boulder Colorado 2024"

# Export format
shodan download --limit 1000 boulder_cameras \
  "port:8080 OR port:8081 OR port:554 Boulder Colorado"
```

### Google Dork Queries

```
inurl:"/mjpeg/video.mjpg" Boulder Colorado
inurl:"/axis-cgi/mjpg/video.cgi" site:.us
inurl:"live" "Boulder" filetype:html
intitle:"Surveillance" OR "Live Stream" Boulder Colorado
intitle:"IP Camera" "Boulder"
cache:cu.edu camera monitoring
```

### Censys Queries

```
certificate.parsed.names: "boulder" AND 
location.country: "US" AND 
parsed.extensions.subject_alt_name.dns_names: camera

ip: 198.* AND location.city: "Boulder" AND 
service.port: [8080, 8081, 554]
```

---

## MITRE ATT&CK Framework Alignment

### Reconnaissance Phase

| Technique | Subtechnique | Activity | Tool |
|-----------|--------------|----------|------|
| **T1593** | Search Open Websites | Google dorking, Shodan query | Browser/CLI |
| **T1589.001** | Credentials | Default password discovery | Manual analysis |
| **T1590.001** | Network topology | WHOIS, DNS enumeration | dig, whois |
| **T1592.003** | Firmware version | Fingerprinting camera models | HTTP headers |

### Discovery Phase

| Technique | Subtechnique | Activity | Notes |
|-----------|--------------|----------|-------|
| T1518 | Software Discovery | Identify camera firmware | No local execution |
| T1016 | System Network Discovery | Map network ranges | Passive DNS only |

### Lateral Movement Preparation

| Finding Type | Risk | Remediation |
|-------------|------|-------------|
| Default credentials exposed | High | Change all default passwords |
| Weak encryption (HTTP) | High | Enforce HTTPS/TLS 1.2+ |
| Management UI exposed | Critical | Restrict to internal network |
| Firmware outdated | High | Apply latest security patches |

---

## Real-World Example (Reference)

### Finding: Axis M1045-LW Webcam - CU Boulder

```
## EXAMPLE-001: Axis Communications M1045-LW WiFi Network Camera

**Discovery Method:** Google dorking + Shodan correlation  
**Query Used:** inurl:"/axis-cgi/mjpg/video.cgi" site:.colorado.edu  
**Source:** Shodan + Google Search  

### Endpoint Details
- **URL**: http://192.168.1.45:8080/axis-cgi/mjpg/video.cgi
- **Port**: 8080
- **Protocol**: HTTP (unencrypted)
- **Status Code**: 200 OK

### Infrastructure Fingerprinting
- **Manufacturer**: Axis Communications
- **Model**: M1045-LW
- **Firmware Version**: 5.41.0.01 (Outdated)
- **Server Header**: AXIS_M1045-LW

### Access Assessment
- **Authentication**: Basic HTTP Authentication (Weak)
- **Encryption**: None (HTTP)
- **Default Credentials**: admin / [blank password] likely
- **Management Interface**: Exposed at /admin/

### Risk Assessment
- **CVSS Score**: 9.1 (High)
- **Exposure Level**: CRITICAL
- **Live Stream Access**: YES - unauthorized viewing possible
- **Metadata Visible**: Timestamp, firmware version, network info

### MITRE ATT&CK Mapping
- **T1593**: Search Open Websites/Domains — Google dork discovered indexing
- **T1589.001**: Gather Victim Network Information — Default credentials known
- **T1590.001**: Active Scanning — Firmware version disclosed

### Remediation
1. Change default admin password immediately
2. Upgrade firmware to latest version (6.x+)
3. Restrict access: internal network only
4. Enable HTTPS with valid certificate
5. Disable HTTP entirely
6. Implement network segmentation (separate VLAN)

### Notes
- This camera appears to be on a university research network
- Similar models likely nearby (sequential IP range 192.168.1.x)
- Firmware version 5.41 has known buffer overflow (CVE-2016-3714)
```

---

## Document Status

- **Part 1**: ✅ Methodology complete
- **Part 2**: ✅ API status documented
- **Part 3**: ✅ Template prepared (example provided)
- **Part 4**: ⏳ Security recommendations (pending findings)

**Awaiting:** API key configuration to populate real findings from Boulder area.
