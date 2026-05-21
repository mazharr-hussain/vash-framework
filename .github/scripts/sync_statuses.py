#!/usr/bin/env python3
"""
VASH 3.0 — Sync activity statuses to GitHub Project.
Updates the built-in Status field (Todo/In Progress/Done)
AND our custom Status field (PENDING/PASS/FAIL/MODIFY).
"""
import os, re, sys, json, urllib.request, urllib.error
from pathlib import Path

TOKEN = os.environ.get("PROJECT_TOKEN", "")
OWNER = "mazharr-hussain"
PROJECT_NAME = "VASH 3.0 — Activity Board"

def gql(query, variables=None):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read())
            if d.get("errors"):
                print(f"  GraphQL error: {d['errors']}")
            return d.get("data")
    except Exception as e:
        print(f"  Error: {e}")
        return None

def get_project():
    d = gql('''query($login: String!) {
      user(login: $login) {
        projectsV2(first: 10) {
          nodes { id title
            fields(first: 30) {
              nodes {
                __typename
                ... on ProjectV2Field { id name }
                ... on ProjectV2SingleSelectField {
                  id name options { id name }
                }
              }
            }
          }
        }
      }
    }''', {"login": OWNER})

    if not d:
        return None, {}

    for proj in d["user"]["projectsV2"]["nodes"]:
        if PROJECT_NAME in proj.get("title", ""):
            # Build field map
            fields = {}
            for f in proj["fields"]["nodes"]:
                if f:
                    fields[f.get("name", "")] = f
            print(f"Project found: {proj['title']}")
            print(f"Fields: {list(fields.keys())}")
            return proj["id"], fields

    return None, {}

def get_all_items(pid):
    d = gql('''query($pid: ID!) {
      node(id: $pid) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                ... on DraftIssue { title }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field { ... on ProjectV2SingleSelectField { name } }
                  }
                }
              }
            }
          }
        }
      }
    }''', {"pid": pid})

    items = []
    if not d:
        return items

    for item in d["node"]["items"]["nodes"]:
        if not item or not item.get("content"):
            continue
        title = item["content"].get("title", "")
        tid_m = re.search(r'\[(\d+\.\d+)\]', title)
        if not tid_m:
            continue
        items.append({
            "item_id": item["id"],
            "task_id": tid_m.group(1),
            "title": title,
        })
    return items

def set_field(pid, item_id, field_id, option_id):
    gql('''mutation($pid:ID!,$iid:ID!,$fid:ID!,$oid:String!){
      updateProjectV2ItemFieldValue(input:{
        projectId:$pid itemId:$iid fieldId:$fid
        value:{singleSelectOptionId:$oid}
      }){clientMutationId}
    }''', {"pid": pid, "iid": item_id, "fid": field_id, "oid": option_id})

def opt_id(fields, field_name, option_name):
    for o in fields.get(field_name, {}).get("options", []):
        if o["name"] == option_name:
            return o["id"]
    return ""

def read_validation_statuses():
    statuses = {}
    for f in Path("runtime/validation").glob("*_summary.md"):
        m = re.match(r"(\d+-\d+)_summary", f.name)
        if not m:
            continue
        task_id = m.group(1).replace("-", ".")
        content = f.read_text(encoding="utf-8")
        vm = re.search(r"\*\*Verdict:\*\*\s*(\w+)", content)
        if not vm:
            continue
        verdict = vm.group(1).upper()
        statuses[task_id] = "PASS" if verdict == "APPROVED" else verdict
    return statuses

KNOWN = {"0.10": "PASS", "0.11": "PASS", "0.12": "PASS"}

# Map our status to built-in Status options
BUILTIN_MAP = {
    "PASS": "Done",
    "FAIL": "In Progress",
    "MODIFY": "In Progress",
    "IN_PROGRESS": "In Progress",
    "PENDING": "Todo",
}

def main():
    if not TOKEN:
        print("ERROR: PROJECT_TOKEN not set")
        sys.exit(1)

    pid, fields = get_project()
    if not pid:
        print("Project not found")
        sys.exit(1)

    print(f"\nAll field names: {list(fields.keys())}\n")

    # Build target statuses
    target = {**KNOWN, **read_validation_statuses()}
    print(f"Activities to update: {len(target)}")
    for k, v in sorted(target.items()):
        print(f"  {k}: {v}")

    items = get_all_items(pid)
    print(f"\nProject items: {len(items)}")

    updated = 0
    for item in items:
        task_id = item["task_id"]
        status = target.get(task_id)
        if not status:
            continue

        # Update custom Status field
        custom_fid = fields.get("VASH Status", {}).get("id")
        custom_oid = opt_id(fields, "VASH Status", status)
        if custom_fid and custom_oid:
            set_field(pid, item["item_id"], custom_fid, custom_oid)

        # Update built-in Status field
        builtin_name = BUILTIN_MAP.get(status, "Todo")
        # Find built-in status field (usually named "Status" with Todo/In Progress/Done)
        for fname, fdata in fields.items():
            opts = fdata.get("options", [])
            opt_names = [o["name"] for o in opts]
            if "Todo" in opt_names and "Done" in opt_names:
                builtin_oid = opt_id(fields, fname, builtin_name)
                if builtin_oid:
                    set_field(pid, item["item_id"], fdata["id"], builtin_oid)
                break

        icon = {"PASS":"✅","FAIL":"❌","MODIFY":"⚠️"}.get(status,"⏳")
        print(f"  {icon} [{task_id}] → {status}")
        updated += 1

    print(f"\n✅ Updated {updated} activities")

if __name__ == "__main__":
    main()
