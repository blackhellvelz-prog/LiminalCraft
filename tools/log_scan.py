#!/usr/bin/env python3
"""Index every WARN/ERROR line and key events of a Forge 1.20.1 latest.log.

Usage:
    python3 -I tools/log_scan.py <latest.log> <out_dir> [--encoding cp1251]

Writes <out_dir>/LOG_INDEX.csv (one row per WARN/ERROR/GL-error line, grouped by pattern)
and prints a summary. The player name and UUID from the launch arguments are replaced
with <player>/<uuid> so the output can be shared.
"""
import csv
import os
import re
import sys
from collections import Counter, OrderedDict

LINE_RE = re.compile(r"^\[(\d\d:\d\d:\d\d)\] \[([^\]]+)/(INFO|WARN|ERROR|FATAL|DEBUG)\]: (.*)$")

# (pattern_id, regex) — first match wins. Pattern ids are stable keys used in LOG_FINDINGS.md.
PATTERNS = [
    ("P01_missing_modstoml", r"is missing mods\.toml file"),
    ("P02_trashslot_refmap", r"Reference map 'trashslot\.refmap\.json'"),
    ("P03_embeddium_nvidia_workaround", r"NVIDIA_THREADED_OPTIMIZATIONS|This is not necessarily an issue|secondary workaround for NVIDIA"),
    ("P04_ipn_dependency_resolving", r"Doing our own dependency resolving"),
    ("P05_oculus_force_disable_mixin", r"Force-disabling mixin"),
    ("P06_class_not_found_optional", r"Error loading class: .*ClassNotFoundException"),
    ("P07_mixin_target_not_found", r"@Mixin target .* was not found"),
    ("P08_assets_url_schema", r"Assets URL .* uses unexpected sch"),
    ("P09_auth_401", r"Failed to verify authentication"),
    ("P10_embeddium_tainted", r"Mod mixin into Embeddium internals detected"),
    ("P11_modifying_embeddium_class", r"are modifying Embeddium class"),
    ("P12_shader_unknown_option", r"Tried to get boolean value for unknown option"),
    ("P13_shader_custom_images_flag", r"Found flag CUSTOM_IMAGES"),
    ("P14_xaero_online_data_expired", r"Online mod data expired"),
    ("P15_missing_sound_event", r"Missing sound for event"),
    ("P16_vanilla_shader_missing_sampler", r"could not find sampler named"),
    ("P17_patcher_gl_fragcolor", r"gl_FragColor is not supported yet"),
    ("P18_http_301", r"GET request failed\. Response Code: 301"),
    ("P19_ipv6_property", r"preferIPv6Addresses"),
    ("P20_clouds_shader_uniform", r"Shader clouds could not find uniform"),
    ("P21_server_cant_keep_up", r"Can't keep up! Is the server overloaded"),
    ("P22_gl_debug_error", r"OpenGL debug message: .*type=ERROR"),
]
COMPILED = [(pid, re.compile(rx)) for pid, rx in PATTERNS]


def anonymise(text, names):
    for n, repl in names:
        text = text.replace(n, repl)
    return text


def main(path, out_dir, encoding="cp1251"):
    raw = open(path, "rb").read().decode(encoding, errors="replace").replace("\r", "")
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    names = []
    m = re.search(r"--username, ([^,\]]+)", raw)
    if m:
        names.append((m.group(1), "<player>"))
    m = re.search(r"--uuid, ([0-9a-f-]{36})", raw)
    if m:
        names.append((m.group(1), "<uuid>"))

    levels = Counter()
    rows, unmatched = [], []
    for no, line in enumerate(lines, 1):
        mm = LINE_RE.match(line)
        if not mm:
            continue
        time, thread, level, msg = mm.groups()
        if level == "INFO" and "OpenGL debug message" not in msg:
            continue
        if level == "INFO" and "type=ERROR" not in msg:
            continue
        levels[level] += 1
        pid = next((p for p, rx in COMPILED if rx.search(msg)), None)
        row = OrderedDict(line=no, time=time, thread=thread, level=level,
                          pattern=pid or "UNMATCHED", message=anonymise(msg, names))
        rows.append(row)
        if pid is None:
            unmatched.append(row)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "LOG_INDEX.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    all_levels = Counter(mm.group(3) for mm in (LINE_RE.match(l) for l in lines) if mm)
    save_noise = sum(1 for l in lines if "Saving chunks for level" in l or "All chunks are saved" in l)
    print(f"lines={len(lines)} levels={dict(all_levels)} indexed={len(rows)} unmatched={len(unmatched)} save_noise_lines={save_noise}")
    by = Counter(r["pattern"] for r in rows)
    for pid, _ in PATTERNS:
        if by.get(pid):
            first = next(r for r in rows if r["pattern"] == pid)
            print(f"{pid:36s} {by[pid]:4d}  first L{first['line']} {first['time']}")
    for r in unmatched:
        print("UNMATCHED", r["line"], r["message"][:160])


if __name__ == "__main__":
    enc = "cp1251"
    if "--encoding" in sys.argv:
        enc = sys.argv[sys.argv.index("--encoding") + 1]
    main(sys.argv[1], sys.argv[2], enc)
