from mitmproxy import http
from urllib.parse import unquote
import re, time, json, os
from datetime import datetime

try:
    import colorama
    colorama.init()
except:
    pass

RED="\033[91m"; GREEN="\033[92m"; YELLOW="\033[93m"; RESET="\033[0m"
def log_red(m): print(f"{RED}{m}{RESET}")
def log_green(m): print(f"{GREEN}{m}{RESET}")
def log_yellow(m): print(f"{YELLOW}{m}{RESET}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "waf_logs.json")
CONFIG_FILE = os.path.join(BASE_DIR, "waf_config.json")

BLOCK_THRESHOLD=5
LOGIN_LIMIT=5; LOGIN_WINDOW=30
RATE_LIMIT=50; RATE_WINDOW=10; BLOCK_TIME=120

login_attempts={}
request_counts={}
blocked_ips={}

TRUSTED_IPS = {"127.0.0.1", "::1"}

# Domains that should be whitelisted (not intercepted)
WHITELIST_DOMAINS = {
    "unpkg.com",
    "cdn.tailwindcss.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "127.0.0.1",
    "localhost"
}

SQLI_PATTERNS=[
    r"(\bor\b|\band\b)\s+\d+=\d+",
    r"'\s*or\s*'1'='1",
    r"union\s+select",
    r"select\s+.*\s+from",
    r"insert\s+into",
    r"drop\s+table",
    r"--;",
    r"#"
]

XSS_PATTERNS=[
    r"<script.*?>",
    r"</script>",
    r"onerror\s*=",
    r"onload\s*=",
    r"javascript:"
]

SENSITIVE_ENDPOINTS=["login","signin","auth","userinfo.php"]
STATIC_EXTENSIONS = (".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg")

def load_config():
    defaults={
        "enable_xss":True,
        "enable_sqli":True,
        "enable_rate_limit":True,
        "enable_bruteforce":True
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults
    try:
        with open(CONFIG_FILE,"r",encoding="utf-8") as f:
            cfg=json.load(f)
            return {**defaults, **cfg}
    except:
        return defaults

def normalize_payload(d):
    if not d:
        return ""
    if isinstance(d,str):
        return unquote(d.lower())
    return unquote(" ".join(f"{k}={v}" for k,v in d.items()).lower())

def score_payload(p):
    s=0; a=[]
    for r in SQLI_PATTERNS:
        if re.search(r,p,re.I):
            s+=3; a.append("SQLi")
    for r in XSS_PATTERNS:
        if re.search(r,p,re.I):
            s+=3; a.append("XSS")
    return s,list(set(a))

def cleanup(lst,w):
    n=time.time()
    return [t for t in lst if n-t<=w]

def log_event(flow,attack,action,payload):
    entry={
        "time":datetime.utcnow().isoformat(),
        "ip":flow.client_conn.address[0],
        "method":flow.request.method,
        "url":flow.request.pretty_url,
        "attack":attack,
        "action":action,
        "payload":payload[:200]
    }
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(entry)+"\n")

def request(flow: http.HTTPFlow):
    cfg=load_config()
    ip=flow.client_conn.address[0]
    now=time.time()
    url=flow.request.pretty_url.lower()

    if ip in TRUSTED_IPS:
        log_event(flow,"None","ALLOWED","")
        return

    if "127.0.0.1:5000" in url or "localhost:5000" in url:
        return

    # Check if domain is whitelisted
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    if domain in WHITELIST_DOMAINS or any(domain.endswith('.' + wd) for wd in WHITELIST_DOMAINS):
        return

    if ip in blocked_ips and now < blocked_ips[ip]:
        log_red(f"[IP-BLOCKED] {ip}")
        flow.response=http.Response.make(403,b"IP blocked",{})
        return

    if (
        cfg["enable_rate_limit"]
        and not url.endswith(STATIC_EXTENSIONS)
        and flow.request.method in ("GET","POST")
    ):
        request_counts.setdefault(ip,[])
        request_counts[ip]=cleanup(request_counts[ip],RATE_WINDOW)
        request_counts[ip].append(now)

        if len(request_counts[ip]) > RATE_LIMIT:
            if ip not in TRUSTED_IPS:
                blocked_ips[ip]=now+BLOCK_TIME
            log_red(f"[RATE-LIMIT] {ip}")
            log_event(flow,"RateLimit","BLOCKED","")
            flow.response=http.Response.make(403,b"Rate limit exceeded",{})
            return

    if cfg["enable_bruteforce"] and any(e in url for e in SENSITIVE_ENDPOINTS):
        login_attempts.setdefault(ip,[])
        login_attempts[ip]=cleanup(login_attempts[ip],LOGIN_WINDOW)
        login_attempts[ip].append(now)

        if len(login_attempts[ip]) > LOGIN_LIMIT:
            if ip not in TRUSTED_IPS:
                blocked_ips[ip]=now+BLOCK_TIME
            log_red(f"[BRUTEFORCE] {ip}")
            log_event(flow,"BruteForce","BLOCKED","")
            flow.response=http.Response.make(403,b"Brute force detected",{})
            return

    payload=""

    if flow.request.query:
        payload+=normalize_payload(flow.request.query)

    if flow.request.method=="POST":
        if flow.request.urlencoded_form:
            payload+=" "+normalize_payload(flow.request.urlencoded_form)
        elif flow.request.text:
            payload+=" "+normalize_payload(flow.request.text)

    score,attacks=score_payload(payload)

    if 0 < score < BLOCK_THRESHOLD:
        log_yellow(f"[SUSPICIOUS] {attacks} {ip}")

    if cfg["enable_sqli"] and "SQLi" in attacks:
        log_red(f"[BLOCKED][SQLi] {ip}")
        log_event(flow,"SQLi","BLOCKED",payload)
        flow.response=http.Response.make(403,b"SQL injection blocked",{})
        return

    if cfg["enable_xss"] and "XSS" in attacks:
        log_red(f"[BLOCKED][XSS] {ip}")
        log_event(flow,"XSS","BLOCKED",payload)
        flow.response=http.Response.make(403,b"XSS attack blocked",{})
        return

    log_green(f"[ALLOWED] {ip} {flow.request.pretty_url}")
    log_event(flow,"None","ALLOWED",payload)

addons=[request]
