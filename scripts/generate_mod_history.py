#!/usr/bin/env python3
"""
Builds data/mod-history.json: for every mod Modrinth has ever resolved as
"embedded" in a Fresh Vanilla version, which pack versions it appeared in,
plus its title/description/category pulled from the mod's own project page.

This is the level-1 backbone for FEATURES.md (hand-curated on top of it).
Safe to re-run anytime; purely additive/mechanical, no judgment calls.
"""
import json
import os
import urllib.request

PROJECT_ID = "H1WDyVEk"
H = {"User-Agent": "fresh-vanilla-github-sync/1.0 (github.com/Hocine123321/Fresh-Vanilla)"}


def get(url):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    versions = get(f"https://api.modrinth.com/v2/project/{PROJECT_ID}/version")
    versions.sort(key=lambda v: v["date_published"])  # ascending, for first/last-seen

    # version_id -> project_id, for dependency entries missing project_id
    need_resolve = set()
    per_version_deps = {}  # version_number -> [ {project_id or version_id, dependency_type} ]

    for v in versions:
        deps = [d for d in v.get("dependencies", []) if d.get("dependency_type") == "embedded"]
        per_version_deps[v["version_number"]] = deps
        for d in deps:
            if not d.get("project_id") and d.get("version_id"):
                need_resolve.add(d["version_id"])

    version_to_project = {}
    if need_resolve:
        ids = list(need_resolve)
        for batch in chunks(ids, 50):
            q = json.dumps(batch)
            resolved = get(f"https://api.modrinth.com/v2/versions?ids={urllib.parse.quote(q)}")
            for r in resolved:
                version_to_project[r["id"]] = r["project_id"]

    # project_id -> sorted list of version_numbers it appeared in
    appearances = {}
    for vnum, deps in per_version_deps.items():
        for d in deps:
            pid = d.get("project_id") or version_to_project.get(d.get("version_id"))
            if not pid:
                continue
            appearances.setdefault(pid, []).append(vnum)

    order = [v["version_number"] for v in versions]  # chronological order
    for pid in appearances:
        appearances[pid] = sorted(set(appearances[pid]), key=lambda x: order.index(x))

    latest_release = next((v["version_number"] for v in reversed(versions)
                            if v.get("version_type") == "release"), versions[-1]["version_number"])

    # batch-fetch project metadata
    all_ids = list(appearances.keys())
    projects = {}
    for batch in chunks(all_ids, 100):
        q = json.dumps(batch)
        for p in get(f"https://api.modrinth.com/v2/projects?ids={urllib.parse.quote(q)}"):
            projects[p["id"]] = p

    out = []
    for pid, vlist in appearances.items():
        p = projects.get(pid, {})
        out.append({
            "project_id": pid,
            "slug": p.get("slug"),
            "title": p.get("title", pid),
            "description": p.get("description", ""),
            "categories": p.get("categories", []),
            "project_type": p.get("project_type"),
            "url": f"https://modrinth.com/{p.get('project_type', 'mod')}/{p.get('slug', pid)}",
            "appeared_in": vlist,
            "first_version": vlist[0] if vlist else None,
            "last_version": vlist[-1] if vlist else None,
            "in_latest": latest_release in vlist,
        })

    out.sort(key=lambda m: m["title"].lower())

    os.makedirs("data", exist_ok=True)
    with open("data/mod-history.json", "w") as f:
        json.dump({
            "generated_from_versions": order,
            "latest_release": latest_release,
            "mods": out,
        }, f, indent=2)

    print(f"wrote data/mod-history.json — {len(out)} mods across {len(order)} versions")


if __name__ == "__main__":
    import urllib.parse
    main()
