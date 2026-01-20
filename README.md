# 🛡️ WAF Security Dashboard

Professional client-side Web Application Firewall with real-time monitoring.

## Features

- ✅ SQL Injection Detection & Prevention
- ✅ XSS Attack Protection  
- ✅ Rate Limiting
- ✅ Brute Force Protection
- ✅ Real-time Dashboard
- ✅ Live Threat Analytics
- ✅ Export Logs (JSON/CSV)

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run (Windows)
```bash
run.bat
```

### 2. Run (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### 3. Configure Browser Proxy
Set your browser proxy to: `127.0.0.1:8080`

### 4. Access Dashboard
Open: http://127.0.0.1:5000

## Manual Start

**Terminal 1 - Proxy:**
```bash
mitmdump -s proxy.py
```

**Terminal 2 - Dashboard:**
```bash
cd dashboard
python app.py
```

## Testing

**Test SQL Injection:**
```bash
curl --proxy http://127.0.0.1:8080 "http://example.com?id=1' OR '1'='1"
```

**Test XSS:**
```bash
curl --proxy http://127.0.0.1:8080 "http://example.com?msg=<script>alert(1)</script>"
```

## Configuration

Edit `waf_config.json` or use dashboard UI to toggle protections.

## License
MIT