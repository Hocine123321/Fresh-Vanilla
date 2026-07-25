#!/usr/bin/env python3
"""
Drafts FEATURES.md from data/mod-history.json.

This is curation, not pure generation: the bucket assignment below encodes
judgment calls about what counts as which "feature" for a player reading the
page, not just raw Modrinth categories. Re-run manually after data/mod-history.json
updates when you want to refresh it — this is intentionally NOT wired into the
6-hourly auto-sync workflow, since bucket assignment can need a human sanity check
after big pack overhauls (e.g. a new version's mods won't be bucketed yet, they'll
fall into "Quality of Life & Tweaks" until MANUAL/BUCKETS below is updated).
"""
import json

DATA_PATH = "data/mod-history.json"
OUT_PATH = "FEATURES.md"

BUCKETS = [
    ("Exploration, Structures & Worldgen", {"worldgen"}, {"library"}),
    ("Bosses & Dangerous Encounters", {"mobs"}, set()),
    ("New Dimensions & End/Nether Overhauls", set(), set()),
    ("Gear, Weapons & Combat", {"equipment", "magic"}, set()),
    ("Storage & Inventory QoL", {"storage"}, set()),
    ("Maps & Navigation", set(), set()),
    ("Visual & Immersion Polish", {"decoration", "gui", "food"}, set()),
    ("Multiplayer & Social", {"social"}, set()),
    ("Performance & Optimization", {"optimization"}, set()),
    ("Quality of Life & Tweaks", {"game-mechanics", "management", "tweaks", "utility"}, set()),
    ("Under the Hood (libraries — enable the features above, not features themselves)", {"library"}, set()),
]

MANUAL = {
    "Eternal Starlight": "New Dimensions & End/Nether Overhauls",
    "Incendium Legacy": "New Dimensions & End/Nether Overhauls",
    "YUNG's Better End Island": "New Dimensions & End/Nether Overhauls",
    "YUNG's Better Nether Fortresses": "New Dimensions & End/Nether Overhauls",
    "True Ending - Ender Dragon Overhaul": "New Dimensions & End/Nether Overhauls",
    "Antique Atlas 4": "Maps & Navigation",
    "AA4 Structure Markers": "Maps & Navigation",
    "Explorer's Compass": "Maps & Navigation",
    "Surveystones": "Maps & Navigation",
    "Surveyor Map Framework": "Maps & Navigation",
    "Wraith Waystones": "Maps & Navigation",
    "Map Atlas": "Maps & Navigation",
    "Map Atlases": "Maps & Navigation",
    "Hoofprint": "Maps & Navigation",
}


def bucket_for(m):
    if m["title"] in MANUAL:
        return MANUAL[m["title"]]
    cats = set(m["categories"])
    for name, include, exclude in BUCKETS:
        if include and cats & include and not (cats & exclude):
            return name
    return "Quality of Life & Tweaks"


def clean_desc(desc, limit=180):
    desc = " ".join((desc or "").split())  # collapse all whitespace/newlines
    if len(desc) > limit:
        cut = desc.rfind(". ", 0, limit)
        desc = desc[:cut + 1] if cut > 40 else desc[:limit].rstrip() + "…"
    return desc


def fmt_range(m):
    if m["first_version"] == m["last_version"]:
        return f"new in v{m['first_version']}"
    return f"since v{m['first_version']}"


def main():
    d = json.load(open(DATA_PATH))
    mods = d["mods"]
    latest = d["latest_release"]

    grouped = {}
    for m in mods:
        if not m["in_latest"]:
            continue
        grouped.setdefault(bucket_for(m), []).append(m)

    lines = []
    lines.append("# Feature List\n")
    lines.append(f"Every mod in the current Fresh Vanilla release (**v{latest}**), grouped by what it "
                  f"actually does in-game, tagged with which version introduced it. Descriptions are the "
                  f"mod authors' own. Generated from `data/mod-history.json` — for the full history "
                  f"including retired/replaced mods, see that file or the version-by-version notes in "
                  f"`CHANGELOG.md`.\n")

    lines.append("## Contents\n")
    toc_order = [b for b, _, _ in BUCKETS if b in grouped]
    for b in toc_order:
        anchor = b.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "").replace(",", "").replace("—", "").replace("/", "")
        anchor = "-".join(filter(None, anchor.split("-")))
        lines.append(f"- [{b}](#{anchor}) ({len(grouped[b])})")
    lines.append("")

    for b in toc_order:
        items = sorted(grouped[b], key=lambda x: x["title"].lower())
        is_library_section = b.startswith("Under the Hood")
        lines.append(f"## {b}\n")
        if is_library_section:
            lines.append(f"<details>\n<summary>Expand — {len(items)} dependency/API mods, not player-facing on their own</summary>\n")
        for m in items:
            desc = clean_desc(m["description"])
            lines.append(f"- **[{m['title']}]({m['url']})** — {desc} _({fmt_range(m)})_")
        if is_library_section:
            lines.append("\n</details>")
        lines.append("")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"wrote {OUT_PATH} — {len(mods)} mods in {len(grouped)} sections")


if __name__ == "__main__":
    main()
