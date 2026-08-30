#!/usr/bin/env python3
"""The Kymira doctrine gate.

Run it over a deliverable folder before certifying anything:

    python3 doctrine_gate.py <deliverable_dir>

Exit 0 means every mechanical law held. Exit 1 means the build FAILED and the
report on stdout names each violation with its file. The gate checks only what
is mechanical; a green gate is necessary, never sufficient. The principles it
enforces (see DOCTRINE.md):

  hygiene    Every .html artifact opens with <!doctype html> and declares
             <meta charset="utf-8"> in its first bytes; no artifact contains
             mojibake or replacement glyphs.                    (deliverable contract)
  leaks      No artifact carries a build-machine path (/private/tmp, /Users/,
             /home/, C:\\Users, file:///) that dies on first forward.  (contract)
  prose      Every significant figure in a prose artifact (.md) also appears
             in a machine artifact (.json/.csv/.html). Integers below 100 and
             bare years are exempt, and that exemption is disclosed below.
             A manifest that contradicts its page is a failed build.  (principle 1)
  hashes     Every sha256 recorded in a manifest verifies, binary mode,
             against the shipped file's raw bytes.              (manifest law)
  firetests  Every passing entry in a checks log (*checks*.json) carries
             fire-test evidence: {"fire_test": {"fired": true}}. A check row
             without proof it can turn red may not render as PASS. (principle 6)

Conventions the gate reads (state them in your build):
  - checks log: any *checks*.json holding a list (or {"checks": [...]}) of
    entries with "name"/"id", "status", and "fire_test": {"fired": true}.
  - manifest hashes: any 64-char hex string in *.json / MANIFEST.md that sits
    within two lines of a shipped filename is treated as that file's sha256.

Plain Python 3 standard library. No network, no timestamps, deterministic.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

TEXT_EXT = {".html", ".htm", ".md", ".json", ".csv", ".txt", ".log", ".yaml", ".yml", ".js", ".py"}
LEAK_PATTERNS = [b"/private/tmp", b"/private/var/folders", b"/Users/", b"/home/", b"C:\\Users", b"file:///"]
MOJIBAKE = ["\ufffd", "\u00e2\u20ac", "\u00c3\u0083", "\u00c2\u00b7", "\u00c3\u00a9"]

failures = []
notes = []


def fail(law, path, detail):
    failures.append(f"[{law}] {path}: {detail}")


def read_text(p):
    try:
        return p.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return None


def check_hygiene(root):
    for p in sorted(root.rglob("*.htm*")):
        head = p.read_bytes()[:1024].decode("utf-8", "replace").lower()
        if not head.lstrip().startswith("<!doctype html"):
            fail("hygiene", p.name, "does not open with <!doctype html>")
        if 'charset="utf-8"' not in head and "charset=utf-8" not in head:
            fail("hygiene", p.name, 'no <meta charset="utf-8"> in the first 1024 bytes')
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() not in TEXT_EXT or not p.is_file():
            continue
        text = read_text(p)
        if text is None:
            fail("hygiene", p.name, "not valid UTF-8")
            continue
        for m in MOJIBAKE:
            if m in text:
                fail("hygiene", p.name, f"mojibake sequence {m!r} present")
                break


def check_leaks(root):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        blob = p.read_bytes()
        for pat in LEAK_PATTERNS:
            if pat in blob:
                fail("leaks", p.name, f"build-machine path {pat.decode()} in shipped artifact")
                break


NUM = re.compile(r"(?<![\w.])\$?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{3,})(?![\w.])")


def significant_numbers(text):
    out = set()
    for m in NUM.finditer(text):
        raw = m.group(1).replace(",", "")
        if raw.isdigit() and (int(raw) < 100 or (1900 <= int(raw) <= 2100 and len(raw) == 4)):
            continue  # disclosed exemption: small integers and bare years
        out.add(raw)
    return out


def check_prose(root):
    machine_text = ""
    for p in root.rglob("*"):
        if p.suffix.lower() in {".json", ".csv", ".html", ".htm", ".log", ".txt", ".yaml", ".yml"} and p.is_file():
            t = read_text(p)
            if t:
                machine_text += t.replace(",", "")
    for p in sorted(root.rglob("*.md")):
        t = read_text(p)
        if not t:
            continue
        for n in sorted(significant_numbers(t)):
            if n not in machine_text:
                fail("prose", p.name, f"figure {n} appears in prose but in no machine artifact")


HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def check_hashes(root):
    shipped = {p.name: p for p in root.rglob("*") if p.is_file()}
    for p in sorted(root.rglob("*")):
        if p.name.lower() not in {"manifest.md", "manifest.json"} and "manifest" not in p.name.lower():
            continue
        t = read_text(p)
        if not t:
            continue
        lines = t.splitlines()
        for i, line in enumerate(lines):
            for h in HEX64.findall(line):
                ctx = " ".join(lines[max(0, i - 2):i + 3])
                target = next((n for n in shipped if n != p.name and n in ctx), None)
                if target is None:
                    continue
                actual = hashlib.sha256(shipped[target].read_bytes()).hexdigest()
                if actual != h:
                    fail("hashes", p.name, f"sha256 for {target} does not match its raw bytes")


def check_firetests(root):
    logs = [p for p in root.rglob("*checks*.json") if p.is_file()]
    if not logs:
        fail("firetests", str(root), "no *checks*.json machine checks log found; "
             "a certified deliverable ships its checks as data (deliverable contract)")
        return
    for p in sorted(logs):
        try:
            data = json.loads(p.read_text())
        except Exception:
            fail("firetests", p.name, "checks log is not valid JSON")
            continue
        entries = data.get("checks", data) if isinstance(data, dict) else data
        if not isinstance(entries, list):
            fail("firetests", p.name, "checks log holds no list of check entries")
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            status = str(e.get("status", "")).lower()
            name = e.get("name") or e.get("id") or "?"
            if status in {"pass", "passed", "ok", "green"}:
                ft = e.get("fire_test")
                if not (isinstance(ft, dict) and ft.get("fired") is True):
                    fail("firetests", p.name,
                         f'check "{name}" renders PASS with no fire-test evidence '
                         '(no {"fire_test": {"fired": true}}); a row that cannot '
                         "prove it can turn red may not render as PASS")


def main():
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        print("usage: python3 doctrine_gate.py <deliverable_dir>")
        return 2
    root = Path(sys.argv[1])
    check_hygiene(root)
    check_leaks(root)
    check_prose(root)
    check_hashes(root)
    check_firetests(root)
    print("Kymira doctrine gate")
    print(f"  target: {root}")
    print("  exemptions disclosed: integers under 100 and bare years are not "
          "checked by the prose gate")
    if failures:
        print(f"\nFAILED — {len(failures)} violation(s):")
        for f in failures:
            print("  " + f)
        return 1
    print("\nPASS — every mechanical law held. A green gate is necessary, never sufficient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
