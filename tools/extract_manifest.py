#!/usr/bin/env python3
"""Build DIMENSION_MANIFEST.csv and ENTITY_AUDIT.csv from a Liminal Space Project Overhaul JAR.

Reads only data files inside the JAR (JSON/TXT/TSV); never executes or redistributes its code
or assets. Usage:

    python3 -I tools/extract_manifest.py <path/to/Liminal-Space-Project-Overhaul.jar> <out_dir>

Every column is copied from a file inside the JAR; "unknown" means the JAR does not state it.
"""
import csv
import hashlib
import json
import os
import re
import sys
import zipfile

NS = "liminalspaces"


def read(z, name):
    return z.read(name).decode("utf-8")


def main(jar_path, out_dir):
    with open(jar_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    z = zipfile.ZipFile(jar_path)
    names = set(z.namelist())

    lang = json.loads(read(z, f"assets/{NS}/lang/en_us.json"))
    commands = read(z, "COMMANDS.txt")

    # COMMANDS.txt: "/new <id> — <title> [<layout>]" for added worlds,
    # "/liminalspaces enter <id> — <title>" in the ORIGINAL DIMENSIONS section.
    added = {}
    for m in re.finditer(r"^/new (\S+) — (.+?) \[(.+?)\]$", commands, re.M):
        added[m.group(1)] = (m.group(2), m.group(3))
    originals = {}
    section = commands.split("ORIGINAL DIMENSIONS", 1)[1] if "ORIGINAL DIMENSIONS" in commands else ""
    for m in re.finditer(r"^/liminalspaces enter (\S+) — (.+)$", section, re.M):
        originals[m.group(1)] = m.group(2).strip()

    # new-scenes.tsv: the 83 "new video" scenes with family/palette/night/mega flags.
    tsv = {}
    for line in read(z, "new-scenes.tsv").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("|")
        tsv[cols[0]] = dict(zip(["id", "title", "family", "palette", "night", "mega", "video", "frame"], cols))

    dims = sorted(n.rsplit("/", 1)[1][:-5] for n in names
                  if n.startswith(f"data/{NS}/dimension/") and n.endswith(".json"))

    rows = []
    for d in dims:
        dim = json.loads(read(z, f"data/{NS}/dimension/{d}.json"))
        dt_path = f"data/{NS}/dimension_type/{d}.json"
        dt = json.loads(read(z, dt_path)) if dt_path in names else {}
        gen = dim.get("generator", {})
        layers = gen.get("settings", {}).get("layers", [])
        if d in originals:
            group, title, layout = "original_31", originals[d], "unknown (not stated in JAR docs)"
        elif d in tsv:
            group, title, layout = "new_video_83", added.get(d, (tsv[d]["title"], ""))[0], added.get(d, ("", "unknown"))[1]
        elif d in added:
            group, title, layout = "prior_added_61", added[d][0], added[d][1]
        else:
            group, title, layout = "UNCLASSIFIED", "", "unknown"
        name = lang.get(f"dimension.{NS}.{d}") or lang.get(f"biome.{NS}.{d}") or title
        t = tsv.get(d, {})
        rows.append({
            "dimension_id": f"{NS}:{d}",
            "display_name": name,
            "group": group,
            "access_command": f"/liminalspaces enter {d}" + ("" if group == "original_31" else f" | /new {d}"),
            "generator_type": gen.get("type", "unknown"),
            "scene_key": gen.get("scene", ""),
            "layout_per_jar_docs": layout,
            "family_tsv": t.get("family", ""),
            "palette_tsv": t.get("palette", ""),
            "night_flag_tsv": t.get("night", ""),
            "mega_flag_tsv": t.get("mega", ""),
            "min_y": dt.get("min_y", ""),
            "height": dt.get("height", ""),
            "has_skylight": dt.get("has_skylight", ""),
            "has_ceiling": dt.get("has_ceiling", ""),
            "fixed_time": dt.get("fixed_time", ""),
            "ambient_light": dt.get("ambient_light", ""),
            "effects": dt.get("effects", ""),
            "bed_works": dt.get("bed_works", ""),
            "flat_layers": ";".join(f"{l.get('block')}x{l.get('height')}" for l in layers),
            "existing_entities": "unknown (encounter pool not data-driven; see Encounters.class)",
            "story_module_fit": "NEEDS TEST",
        })

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "DIMENSION_MANIFEST.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Entities: creature-optimization.json + MODEL-CREDITS.txt
    creatures = json.loads(read(z, "creature-optimization.json"))
    credits = read(z, "MODEL-CREDITS.txt")
    blocks = [b for b in credits.split("Model Information:") if b.strip()]
    ent_rows = []
    for i, c in enumerate(creatures):
        b = blocks[i] if i < len(blocks) else ""
        g = lambda k: (re.search(rf"\* {k}:\s*(.+)", b) or [None, ""])[1].strip()
        ent_rows.append({
            "entity_id": f"{NS}:{c['name']}",
            "source": "original (liminalspaces)",
            "model_title_per_credits": g("title"),
            "model_url": g("source"),
            "model_author": g("author"),
            "model_license": g("license type"),
            "original_triangles": c.get("original_triangles"),
            "lod_near_tris": c["lod_triangles"]["near"],
            "lod_medium_tris": c["lod_triangles"]["medium"],
            "lod_far_tris": c["lod_triangles"]["far"],
            "height_blocks": c.get("height"),
            "width_blocks": round(c.get("width", 0), 2),
            "texture_atlas_px": "x".join(map(str, c.get("atlas", []))),
            "render_path": "custom mesh renderer (ImportedCreatureRenderer, .mesh.gz), not vanilla cuboid model",
            "credit_order_note": "credit block matched by order; verify",
        })
    with open(os.path.join(out_dir, "ENTITY_AUDIT.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ent_rows[0].keys()))
        w.writeheader()
        w.writerows(ent_rows)

    groups = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    print(f"jar sha256={sha}")
    print(f"dimensions={len(rows)} groups={groups} entities={len(ent_rows)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
