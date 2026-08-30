#!/usr/bin/env python3
"""The Kymira doctrine gate, v2.

Build side (run before certifying, writes the captured verdict into the pack):

    python3 doctrine_gate.py --stamp <deliverable_dir>

Audit side (what a customer, reviewer, or grader runs; also requires that the
build captured its verdict):

    python3 doctrine_gate.py <deliverable_dir>

Exit 0 means every mechanical law held. Exit 1 means FAILED, with each
violation named on stdout. The gate checks only what a script can prove; a
green gate is necessary, never sufficient. Laws enforced (see DOCTRINE.md):

  hygiene    .html artifacts open with <!doctype html> and declare
             <meta charset="utf-8"> in the first bytes; no artifact carries
             mojibake or replacement glyphs.
  leaks      No build-machine path (/private/tmp, /Users/, /home/, C:\\Users,
             file:///) in any shipped artifact.
  prose      Significant figures in .md prose also appear in a machine
             artifact. Disclosed exemption: integers under 100 and bare years.
  hashes     Manifest sha256 claims verify against raw bytes (binary mode).
             JSON manifests are parsed structurally; markdown manifests bind a
             hash only to a filename on the SAME line. Any hex token of 12+
             chars sharing a line with a shipped filename must be a prefix of
             that file's true sha256, so stale truncated hashes fail too.
  firetests  Every PASS row in a checks log carries fire-test EVIDENCE, not a
             boolean: {"fire_test": {"fired": true, "evidence": "<path>"}}
             where <path> exists in the pack, names this exact check, contains
             a failure marker ("fail" or "red", case-insensitive), and is not
             shared with any other check. A row that cannot prove it can turn
             red may not render as PASS (render it INFO instead: INFO rows
             need no fire test and claim no guarantee).
  verdict    (plain mode only) gate_verdict.txt exists in the pack and records
             a PASS: proof the build ran the gate and shipped its answer. The
             stamp writes this file; no manifest lists or hashes it.

Conventions the gate reads:
  - checks log: any *checks*.json holding a list (or {"checks": [...]}) of
    entries with "name"/"id", "status" (PASS | INFO | BLOCKED | FAIL), and for
    PASS rows the fire_test evidence object above.
  - evidence files live inside the pack; one file per check.

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
VERDICT_FILE = "gate_verdict.txt"
PASS_STATUSES = {"pass", "passed", "ok", "green"}
INFO_STATUSES = {"info", "informational", "disclosed", "blocked", "fail", "failed", "red", "flag", "flagged", "uncalibrated"}

failures = []


def fail(law, path, detail):
    failures.append(f"[{law}] {path}: {detail}")


def read_text(p):
    try:
        return p.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return None


def artifacts(root):
    return [p for p in sorted(root.rglob("*")) if p.is_file() and p.name != VERDICT_FILE]


def check_hygiene(root):
    for p in artifacts(root):
        if p.suffix.lower() in {".html", ".htm"}:
            head = p.read_bytes()[:1024].decode("utf-8", "replace").lower()
            if not head.lstrip().startswith("<!doctype html"):
                fail("hygiene", p.name, "does not open with <!doctype html>")
            if 'charset="utf-8"' not in head and "charset=utf-8" not in head:
                fail("hygiene", p.name, 'no <meta charset="utf-8"> in the first 1024 bytes')
        if p.suffix.lower() in TEXT_EXT:
            text = read_text(p)
            if text is None:
                fail("hygiene", p.name, "not valid UTF-8")
                continue
            for m in MOJIBAKE:
                if m in text:
                    fail("hygiene", p.name, f"mojibake sequence {m!r} present")
                    break


def check_leaks(root):
    for p in artifacts(root):
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
    for p in artifacts(root):
        if p.suffix.lower() in {".json", ".csv", ".html", ".htm", ".log", ".txt", ".yaml", ".yml"}:
            t = read_text(p)
            if t:
                machine_text += t.replace(",", "")
    for p in artifacts(root):
        if p.suffix.lower() != ".md":
            continue
        t = read_text(p)
        if not t:
            continue
        for n in sorted(significant_numbers(t)):
            if n not in machine_text:
                fail("prose", p.name, f"figure {n} appears in prose but in no machine artifact")


HEX = re.compile(r"\b[0-9a-f]{12,64}\b")


def sha256_of(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def walk_json(node, out):
    """Collect (filename, hash) pairs from structured manifest JSON."""
    if isinstance(node, dict):
        fname = next((str(node[k]) for k in ("file", "path", "name", "filename") if k in node), None)
        hval = next((str(v) for k, v in node.items() if "sha" in str(k).lower() and isinstance(v, str)), None)
        if fname and hval:
            out.append((Path(fname).name, hval.strip()))
        for v in node.values():
            walk_json(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_json(v, out)


def check_hashes(root):
    shipped = {p.name: p for p in artifacts(root)}
    true_hash = {}

    def actual(name):
        if name not in true_hash:
            true_hash[name] = sha256_of(shipped[name])
        return true_hash[name]

    # structured JSON manifests
    for p in artifacts(root):
        if p.suffix.lower() == ".json" and "manifest" in p.name.lower():
            try:
                pairs = []
                walk_json(json.loads(p.read_text()), pairs)
                for fname, h in pairs:
                    if fname in shipped and fname != p.name and re.fullmatch(r"[0-9a-f]{64}", h):
                        if actual(fname) != h:
                            fail("hashes", p.name, f"sha256 for {fname} does not match its raw bytes")
            except Exception:
                fail("hashes", p.name, "manifest JSON does not parse")
    # same-line claims in any text artifact (catches stale truncated hashes too)
    for p in artifacts(root):
        if p.suffix.lower() not in TEXT_EXT:
            continue
        t = read_text(p)
        if not t:
            continue
        for line in t.splitlines():
            named = [n for n in shipped if n != p.name and n in line]
            if len(named) != 1:
                continue  # bind only unambiguous same-line claims
            for h in HEX.findall(line):
                if h in named[0]:
                    continue  # the hex was part of the filename itself
                if not actual(named[0]).startswith(h):
                    fail("hashes", p.name,
                         f"hash claim {h[:16]}… beside {named[0]} is not a prefix of its true sha256")


def check_firetests(root):
    logs = [p for p in artifacts(root) if p.suffix.lower() == ".json" and "checks" in p.name.lower()]
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
        used_evidence = {}
        for e in entries:
            if not isinstance(e, dict):
                continue
            status = str(e.get("status", "")).lower()
            name = str(e.get("name") or e.get("id") or "?")
            if status in INFO_STATUSES:
                continue  # INFO/BLOCKED/FAIL rows claim no guarantee and need no fire test
            if status not in PASS_STATUSES:
                fail("firetests", p.name, f'check "{name}" has unknown status "{status}"; '
                     "the vocabulary is PASS | INFO | BLOCKED | FAIL")
                continue
            ft = e.get("fire_test")
            if not (isinstance(ft, dict) and ft.get("fired") is True and ft.get("evidence")):
                fail("firetests", p.name, f'PASS row "{name}" has no fire-test evidence '
                     '({"fire_test": {"fired": true, "evidence": "<path>"}}); a row that '
                     "cannot prove it can turn red may not render as PASS (use INFO)")
                continue
            ev = str(ft["evidence"]).lstrip("./")
            ep = root / ev
            if not ep.is_file():
                fail("firetests", p.name, f'"{name}": evidence file {ev} does not exist in the pack')
                continue
            if ev in used_evidence:
                fail("firetests", p.name, f'"{name}" shares evidence file {ev} with '
                     f'"{used_evidence[ev]}"; borrowed evidence proves neither check')
                continue
            used_evidence[ev] = name
            et = read_text(ep) or ""
            if name not in et:
                fail("firetests", p.name, f'"{name}": evidence file {ev} never names this check')
            elif not re.search(r"fail|red", et, re.I):
                fail("firetests", p.name, f'"{name}": evidence file {ev} shows no failure; '
                     "fire-test evidence is the captured RED run, not a description")


def render_report(root, stamped):
    lines = ["Kymira doctrine gate v2", f"  target: {root.name}",
             "  exemptions disclosed: integers under 100 and bare years are not "
             "checked by the prose gate"]
    if failures:
        lines.append(f"FAILED — {len(failures)} violation(s):")
        lines += ["  " + f for f in failures]
    else:
        lines.append("PASS — every mechanical law held. A green gate is necessary, never sufficient.")
    if stamped:
        lines.append("stamped: gate_verdict.txt written into the pack")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    stamp = "--stamp" in args
    args = [a for a in args if a != "--stamp"]
    if len(args) != 1 or not Path(args[0]).is_dir():
        print("usage: python3 doctrine_gate.py [--stamp] <deliverable_dir>")
        return 2
    root = Path(args[0])
    check_hygiene(root)
    check_leaks(root)
    check_prose(root)
    check_hashes(root)
    check_firetests(root)
    if not stamp:
        v = root / VERDICT_FILE
        if not v.is_file():
            fail("verdict", VERDICT_FILE, "no captured gate verdict in the pack; the build "
                 "must run the gate with --stamp before shipping")
        elif "PASS" not in (read_text(v) or ""):
            fail("verdict", VERDICT_FILE, "the captured verdict is not a PASS")
    report = render_report(root, stamp)
    if stamp:
        (root / VERDICT_FILE).write_text(report + "\n")
    print(report)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
