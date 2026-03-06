# Internet Reconnaissance Exercise: Boulder, CO Webcams
## Part 1: Reconnaissance Strategy & Methodology

**Author:** ESTHER  
**Date:** 2026-03-06  
**Exercise Scope:** Passive OSINT discovery of publicly accessible webcams  
**Location Context:** 1785 Folsom St, Boulder, CO 80302  
**Authorization:** Adam Fink | Passive reconnaissance approved  

---

## Objective

Discover publicly accessible webcam feeds in Boulder, CO using passive, legal OSINT methods. Document findings without interaction or exploitation.

## Legal & Ethical Framework

- **Technique Classification:** MITRE ATT&CK T1593 (Search Open Websites/Domains)
- **Methodology:** Passive reconnaissance only
- **Prohibited Actions:** No authentication attempts, no exploitation, no network probes, no interaction
- **Authorized Methods:** Public search engines, internet-wide indexes, DNS records, WHOIS data

---

## Phase 1: Search Engine Dorking

### 1.1 Google Advanced Operators

```
inurl:"/mjpeg/video.mjpg" Boulder Colorado
inurl:"/axis-cgi/mjpg/video.cgi" site:.us Boulder
inurl:live "Boulder" "Colorado" webcam
intitle:"Surveillance Camera" Boulder CO
intitle:"Live View" OR "Live Stream" Boulder Colorado
cache:example.com webcam Boulder
```

**Rationale:** Exposes misconfigured publicly indexed camera endpoints by searching for common camera URL patterns and titles.

### 1.2 Bing Advanced Search

```
site:.edu Boulder "webcam" "live stream"
site:.gov Boulder Colorado IP camera
```

**Rationale:** Government and university networks often have public-facing infrastructure documentation.

### 1.3 Alternative Search Engines

- **DuckDuckGo**: `-site:facebook.com inurl:webcam Boulder`
- **Yandex**: Captures non-English indexed content; alternative index

---

## Phase 2: Internet-Wide Indexes

### 2.1 Shodan Queries

**Primary Search Patterns:**

```
port:8080 "Server: Axis" Boulder
port:8081 "Server: Vivotek" Colorado
port:8888 "Server: Hikvision" Boulder
port:554 "rtsp" Boulder Colorado
port:5004 MJPEG Boulder
```

**Camera-Specific Patterns:**

```
"Axis Communications" Boulder
"Hikvision" Boulder Colorado
"Dahua" "live view" Boulder
"Mobotix" Boulder
"Uniview" Boulder
```

**Shodan Filters:**

```
shodan search --filters webcam,public,boulder
```

### 2.2 Censys Certificate Search

```
certificate search: "Boulder" "Colorado" "camera"
```

**Rationale:** Finds TLS certificates for camera management interfaces.

### 2.3 Rapid7 (Project Sonar)

- FDNS (DNS records) dump for `.us` domains in Boulder area
- HTTP/HTTPS scan data indexed by IP

---

## Phase 3: Passive Infrastructure Analysis

### 3.1 DNS Enumeration

```
dig +nocmd +noall +answer camera.boulder.edu
nslookup webcam.company.com
DNS zone transfers (AXFR)
```

### 3.2 WHOIS & IP Registration

```
whois -H [IP_RANGE] | grep -i Boulder
RIPE NCC, ARIN database lookups
```

### 3.3 Reverse DNS Lookups

```
for i in {1..254}; do host 192.168.1.$i; done
```

### 3.4 BGP & ASN Data

```
asnlookup Boulder Colorado ISPs
IPv4 CIDR blocks registered to Boulder entities
```

---

## Phase 4: Public Directories & Databases

### 4.1 Webcam Aggregators

- **EarthCam**: Manual search for Boulder
- **Webcamtaxi**: Index of public feeds
- **Insecam**: Unsecured camera index (catalog only — no interaction)

### 4.2 GitHub & Pastebin

```
site:github.com Boulder webcam URL
site:github.com IP camera Boulder Colorado
```

**Rationale:** Developers often accidentally commit IP addresses or credentials.

### 4.3 Shodan CLI & API Output

```
shodan download webcams_boulder "port:8080 Boulder"
shodan parse --limit 100 webcams_boulder.json
```

---

## Phase 5: Pattern Analysis & Exploitation Vectors

### 5.1 Common Vulnerabilities

- Default credentials (admin/admin, root/root)
- Predictable sequential IP addressing
- Unencrypted MJPEG streams
- Missing authentication on live endpoints
- Exposed camera management interfaces

### 5.2 MITRE ATT&CK Mapping

| Finding | ATT&CK Technique | Notes |
|---------|------------------|-------|
| Search engine indexing | T1593 | Open-source query results |
| Shodan queries | T1593 | Internet-wide index search |
| DNS records | T1590.001 | Network topology reconnaissance |
| Certificate enumeration | T1592 | Infrastructure fingerprinting |

---

## Expected Findings (Reference)

### High-Risk Patterns
- Hikvision/Dahua cameras on public IPs with default interfaces
- MJPEG streams on port 8080 without authentication
- Axis Communications cameras with management UI exposed
- RTSP streams on port 554 with no access control

### Medium-Risk Patterns
- Cameras behind port forwarding with weak credentials
- Expired SSL certificates (confidence loss but accessibility remains)
- Rate limiting or auth bypass opportunities

### Low-Risk Patterns
- Documentation-only URLs (no actual feed)
- Geofenced camera feeds (access restricted by location)
- Behind corporate firewalls (port scans fail)

---

## Documentation Standard

Each finding will include:
1. **URL/Endpoint**: Full path and port
2. **Discovery Method**: Which query returned it
3. **Status Code**: HTTP response or error
4. **Infrastructure Type**: Camera model, manufacturer, firmware
5. **Risk Assessment**: CVSS/exposure level
6. **Remediation**: How operator should secure it

---

## Tools Used (This Exercise)

- **Search Engines**: Google, Bing, DuckDuckGo, Yandex
- **Internet-Wide Indexes**: Shodan, Censys, Rapid7 Sonar
- **DNS Tools**: dig, nslookup, dnsenum
- **Passive Lookup**: WHOIS, ASN lookup, reverse DNS
- **OSINT Aggregators**: GitHub, Pastebin, EarthCam

---

## Next Phase: Execution & Findings Documentation

Proceeding to Phase 2: Execute Shodan queries and compile findings document.
