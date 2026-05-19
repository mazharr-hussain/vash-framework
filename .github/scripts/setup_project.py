#!/usr/bin/env python3
"""
VASH 3.0 — GitHub Project Setup
Creates GitHub Issues for all activities with correct labels.
Runs once via GitHub Actions — no effect on pipeline logic.
"""

import re, json, os, time
import urllib.request, urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "mazharr-hussain"
REPO = "vash3-framework"


def gh(method, endpoint, data=None):
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()


def setup_labels():
    labels = [
        ("parallel-safe", "0075ca", "Can run in parallel with other activities"),
        ("sequential",    "e4e669", "Must run sequentially — has dependencies"),
        ("vash-pass",     "0e8a16", "Activity completed and approved"),
        ("vash-fail",     "d73a4a", "Activity failed validation"),
        ("vash-pending",  "cccccc", "Activity not yet started"),
        ("vash-modify",   "fbca04", "Activity needs corrections"),
        ("phase-0",       "f9d0c4", "Phase 0: GitHub Setup"),
        ("phase-1",       "fef2c0", "Phase 1: VASH Vision"),
        ("phase-2",       "c2e0c6", "Phase 2: Agent Architecture"),
        ("phase-3",       "bfdadc", "Phase 3: Technology Decisions"),
        ("phase-4",       "d4c5f9", "Phase 4: Skills Architecture"),
        ("phase-5",       "e99695", "Phase 5: Platform Design"),
        ("phase-6",       "f9d0c4", "Phase 6: VASH Blueprint"),
        ("manual",        "0052cc", "Manual step — human action required"),
        ("artifact",      "5319e7", "Produces an artifact via pipeline"),
    ]
    print("Setting up labels...")
    for name, color, desc in labels:
        r, err = gh("POST", f"/repos/{OWNER}/{REPO}/labels",
                    {"name": name, "color": color, "description": desc})
        if err and "already_exists" not in err:
            # Try to update existing
            gh("PATCH", f"/repos/{OWNER}/{REPO}/labels/{name}",
               {"color": color, "description": desc})
        print(f"  {'✅' if not err else '↺'} {name}")


def parse_activities():
    with open("knowledge/activity_list.md") as f:
        content = f.read()
    activities = []
    blocks = re.split(r'\n---\n', content)
    for block in blocks:
        if 'ID:' not in block:
            continue
        a = {}
        for field in ['ID', 'NAME', 'TYPE', 'PHASE', 'PARALLEL_SAFE',
                      'DEPENDS_ON', 'THRESHOLD', 'STATUS', 'DESCRIPTION']:
            m = re.search(rf'{field}:\s*(.+)', block)
            if m:
                a[field] = m.group(1).strip()
        if 'ID' in a and re.match(r'\d+\.\d+', a.get('ID', '')):
            activities.append(a)
    return activities


def create_issues(activities):
    phase_labels = {
        "0": "phase-0", "1": "phase-1", "2": "phase-2",
        "3": "phase-3", "4": "phase-4", "5": "phase-5", "6": "phase-6"
    }

    # Get existing issues to avoid duplicates
    existing, _ = gh("GET", f"/repos/{OWNER}/{REPO}/issues?state=all&per_page=100")
    existing_titles = {i["title"] for i in (existing or [])}

    print(f"\nCreating issues for {len(activities)} activities...")
    created = 0
    skipped = 0

    for a in activities:
        task_id = a.get('ID', '')
        phase = task_id.split('.')[0]
        parallel = a.get('PARALLEL_SAFE', 'NO') == 'YES'
        status = a.get('STATUS', 'PENDING')
        depends = a.get('DEPENDS_ON', 'NONE')
        threshold = a.get('THRESHOLD', '88')
        desc = a.get('DESCRIPTION', '')
        atype = a.get('TYPE', 'ARTIFACT')

        title = f"[{task_id}] {a.get('NAME', '')}"

        if title in existing_titles:
            print(f"  ↺ Already exists: {task_id}")
            skipped += 1
            continue

        labels = [
            phase_labels.get(phase, 'phase-0'),
            'parallel-safe' if parallel else 'sequential',
            'artifact' if atype == 'ARTIFACT' else 'manual',
        ]
        if status == 'PASS':
            labels.append('vash-pass')
        elif status == 'FAIL':
            labels.append('vash-fail')
        else:
            labels.append('vash-pending')

        # Build parallel context
        parallel_note = ""
        if parallel:
            parallel_note = "\n> ⚡ **PARALLEL SAFE** — can run simultaneously with other parallel-safe activities in same phase"
        else:
            parallel_note = f"\n> → **SEQUENTIAL** — depends on: `{depends}`"

        body = f"""## {a.get('NAME', '')}

**Phase:** {a.get('PHASE', '')}
**Type:** `{atype}`
**Status:** `{status}`
**Threshold:** {threshold}/100
{parallel_note}

### Description
{desc}

### Depends On
`{depends}`

---
*Auto-managed by VASH 3.0 pipeline*
*Do not edit the Status or Labels manually — pipeline updates them*"""

        r, err = gh("POST", f"/repos/{OWNER}/{REPO}/issues", {
            "title": title,
            "body": body,
            "labels": labels
        })

        if err:
            print(f"  ❌ {task_id}: {err[:60]}")
        else:
            state = "✅" if status == "PASS" else "⏳"
            par = "⚡" if parallel else "→"
            print(f"  {state} {par} #{r.get('number')} [{task_id}] {a.get('NAME', '')[:45]}")
            created += 1

        time.sleep(0.3)  # avoid rate limit

    print(f"\nDone: {created} created, {skipped} already existed")


def main():
    if not TOKEN:
        print("ERROR: GITHUB_TOKEN not set")
        return

    setup_labels()
    activities = parse_activities()
    create_issues(activities)

    print("\n✅ GitHub Project setup complete")
    print(f"View issues: https://github.com/{OWNER}/{REPO}/issues")
    print("Create a Project Board at:")
    print(f"https://github.com/{OWNER}/{REPO}/projects")
    print("Add issues to board and group by phase label for best view")


if __name__ == "__main__":
    main()
