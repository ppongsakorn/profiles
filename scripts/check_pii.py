#!/usr/bin/env python3
"""Block PII from entering git (public repo).

  python scripts/check_pii.py             # everything git would track (tracked + new, minus .gitignore)
  python scripts/check_pii.py --staged    # staged content only (used by .githooks/pre-commit)
  python scripts/check_pii.py --history   # every line ever added in any commit

Fails on: personal export files (*.csv/*.zip/*.vcf/*.xlsx), e-mail addresses, phone numbers, IPv4 addresses,
13-digit IDs, and signed LinkedIn media URLs. The ONE intentional exception: the value of `basics.email` in
data/profile.yaml (an address the owner decided to publish). Matches are printed redacted.
"""
import re, subprocess, sys

BLOCKED_EXT = re.compile(r"\.(csv|zip|vcf|xlsx|xls)$", re.I)
BLOCKED_PATH = re.compile(r"(^|/)private/")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
PHONE = [re.compile(r"(?<![\d.])(?:\+?66|0)[ -]?[689]\d[ -]?\d{3}[ -]?\d{4}(?![\d.])"),   # Thai mobile
         re.compile(r"(?<![\d.])0[2-7][ -]?\d{3}[ -]?\d{4}(?![\d.])"),                       # Thai landline
         re.compile(r"(?<![\w.])\+\d{1,3}[ -]?\d{8,12}(?![\d.])")]                           # +CC international
IPV4 = re.compile(r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\d.])")
LONGID = re.compile(r"(?<!\d)\d{13}(?!\d)")
LICDN = re.compile(r"media\.licdn\.com|licdn\.com/dms")
ALLOW_EMAIL = {"noreply@anthropic.com"}
ALLOW_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "users.noreply.github.com")
ALLOW_IP = {"127.0.0.1", "0.0.0.0"}
SKIP_DIRS = ("dist/", ".git/", "node_modules/", "__pycache__/")


def sh(*a):
    return subprocess.check_output(a, text=True, errors="replace")


def redact(s):
    return s[:2] + "…" + s[-2:] if len(s) > 6 else "…"


def scan_text(where, text, findings, is_profile=False):
    for n, line in enumerate(text.splitlines(), 1):
        if is_profile and re.match(r"^\s*email:\s", line):
            continue   # basics.email: the one deliberately published address
        for m in EMAIL.finditer(line):
            e = m.group(0).lower()
            if e in ALLOW_EMAIL or e.endswith(ALLOW_EMAIL_DOMAINS):
                continue
            findings.append((where, n, "email", redact(m.group(0))))
        for rx in PHONE:
            for m in rx.finditer(line):
                findings.append((where, n, "phone", redact(m.group(0))))
        for m in IPV4.finditer(line):
            if m.group(0) not in ALLOW_IP and not re.match(r"^(v|ver)", line[max(0, m.start() - 3):m.start()], re.I):
                findings.append((where, n, "ip-address", redact(m.group(0))))
        for m in LONGID.finditer(line):
            findings.append((where, n, "13-digit-id", redact(m.group(0))))
        if LICDN.search(line):
            findings.append((where, n, "linkedin-media-url", "…"))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    findings = []
    if mode == "--history":
        for line in sh("git", "log", "-p", "--all", "--no-color", "-U0").splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                scan_text("history", line[1:], findings)
        names = sh("git", "log", "--all", "--name-only", "--pretty=format:").splitlines()
    elif mode == "--staged":
        names = sh("git", "diff", "--cached", "--name-only", "--diff-filter=ACM").splitlines()
    else:
        names = sh("git", "ls-files", "-c", "-o", "--exclude-standard").splitlines()
    for f in sorted(set(n for n in names if n)):
        if BLOCKED_EXT.search(f) or BLOCKED_PATH.search(f):
            findings.append((f, 0, "blocked-file", "personal export / private file must not be committed"))
            continue
        if mode == "--history" or f.startswith(SKIP_DIRS):
            continue
        try:
            text = sh("git", "show", f":{f}") if mode == "--staged" else open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError, subprocess.CalledProcessError):
            continue
        scan_text(f, text, findings, is_profile=(f == "data/profile.yaml"))
    for w, n, kind, m in findings:
        print(f"PII   {w}:{n}  {kind}  {m}")
    print(f"{len(findings)} PII finding(s)")
    sys.exit(1 if findings else 0)


main()
