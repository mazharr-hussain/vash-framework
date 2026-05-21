#!/usr/bin/env python3
"""
VASH 3.0 — GitHub Project Setup v2
Creates ProjectV2 with correct custom fields and structured item bodies.
Runs once via workflow_dispatch.
LAW 1: Python stdlib only
"""
import re, json, os, time, sys
import urllib.request, urllib.error

TOKEN = os.environ.get("PROJECT_TOKEN", "")
OWNER = "mazharr-hussain"
REPO  = "vash3-framework"
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
                print(f"  GQL error: {d['errors'][0].get('message','')}")
            return d.get("data")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:100]}")
        return None

def get_or_create_project(owner_id):
    """Get existing project or create new one."""
    # Check existing
    d = gql('''query($l:String!){user(login:$l){
      projectsV2(first:20){nodes{id title number url}}}}''', {"l": OWNER})
    if d:
        for p in d["user"]["projectsV2"]["nodes"]:
            if PROJECT_NAME in p.get("title", ""):
                print(f"Found existing project: {p['url']}")
                return p["id"], p["url"]
    # Create new
    d = gql('''mutation($o:ID!,$t:String!){
      createProjectV2(input:{ownerId:$o,title:$t}){
        projectV2{id number url}}}''',
      {"o": owner_id, "t": PROJECT_NAME})
    if not d or not d.get("createProjectV2"):
        print("Failed to create project")
        return None, None
    p = d["createProjectV2"]["projectV2"]
    print(f"Created project: {p['url']}")
    return p["id"], p["url"]

def get_fields(pid):
    d = gql('''query($p:ID!){node(id:$p){...on ProjectV2{
      fields(first:30){nodes{
        __typename
        ...on ProjectV2Field{id name}
        ...on ProjectV2SingleSelectField{id name options{id name}}}}}}}''',
      {"p": pid})
    fields = {}
    if d:
        for f in d["node"]["fields"]["nodes"]:
            if f: fields[f.get("name","")] = f
    return fields

def ensure_select_field(pid, name, options, existing_fields):
    """Create select field only if it does not exist."""
    if name in existing_fields:
        print(f"  ↺ Field exists: {name}")
        return
    d = gql('''mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]!){
      addProjectV2CustomField(input:{projectId:$p,name:$n,dataType:SINGLE_SELECT,
        singleSelectOptions:$o}){clientMutationId}}''',
      {"p": pid, "n": name,
       "o": [{"name": o, "color": "GRAY", "description": ""} for o in options]})
    print(f"  {'✅' if d else '❌'} Field: {name}")

def ensure_text_field(pid, name, existing_fields):
    """Create text field only if it does not exist."""
    if name in existing_fields:
        print(f"  ↺ Field exists: {name}")
        return
    d = gql('''mutation($p:ID!,$n:String!){
      addProjectV2CustomField(input:{projectId:$p,name:$n,dataType:TEXT}){
        clientMutationId}}''', {"p": pid, "n": name})
    print(f"  {'✅' if d else '❌'} Field: {name}")

def opt_id(fields, field_name, option_name):
    for o in fields.get(field_name, {}).get("options", []):
        if o["name"] == option_name: return o["id"]
    return ""

def get_existing_items(pid):
    """Get titles of existing items to avoid duplicates."""
    d = gql('''query($p:ID!){node(id:$p){...on ProjectV2{
      items(first:100){nodes{content{
        ...on DraftIssue{title}}}}}}}''', {"p": pid})
    if not d: return set()
    titles = set()
    for item in d["node"]["items"]["nodes"]:
        if item and item.get("content"):
            titles.add(item["content"].get("title",""))
    return titles

def build_item_body(a):
    """Build structured item body for an activity."""
    task_id = a.get("ID","")
    name = a.get("NAME","")
    phase = a.get("PHASE","")
    depends = a.get("DEPENDS_ON","NONE")
    threshold = a.get("THRESHOLD","88")
    atype = a.get("TYPE","ARTIFACT")
    parallel = a.get("PARALLEL_SAFE","NO")
    desc = a.get("DESCRIPTION","")

    # Build why it is important based on phase
    phase_why = {
        "0": "Foundation of the VASH pipeline. Without this activity the automation cannot run.",
        "1": "Defines the north star for VASH. All subsequent phases depend on this vision.",
        "2": "Defines how agents collaborate. Governs quality control across all activities.",
        "3": "Selects the technology stack. All infrastructure and platform decisions flow from here.",
        "4": "Builds the reusable skill library. Agents use these skills to do their work.",
        "5": "Designs the operational platform. How VASH runs day-to-day.",
        "6": "Consolidates all design into the master blueprint. Final deliverable of the design phase.",
    }
    phase_num = task_id.split(".")[0] if task_id else "0"
    why = phase_why.get(phase_num, "Required for VASH to function correctly.")

    depends_note = "None — this is a foundation activity" if depends in ("NONE","") else depends

    return f"""## What This Activity Does
{desc}

## Why It Is Important
{why}

## Acceptance Criteria
- Artifact passes AvA review with score ≥ {threshold}/100
- All checklist items PASS
- All three VASH laws respected (LAW 1: free/open, LAW 2: automated, LAW 3: reuse first)
- Human approval received

## Activity Details
- **Type:** {atype}
- **Phase:** {phase}
- **Parallel Safe:** {parallel}
- **Depends On:** {depends_note}
- **Threshold:** {threshold}/100

## Last AvA Result
- **Score:** —
- **Round:** —
- **Verdict:** —
- **Updated:** —

---
*Managed by VASH 3.0 pipeline — Last AvA Result is auto-updated after each run*"""

def parse_activities():
    with open("knowledge/activity_list.md") as f:
        content = f.read()
    activities = []
    for block in re.split(r'\n---\n', content):
        if 'ID:' not in block: continue
        a = {}
        for field in ['ID','NAME','TYPE','PHASE','PARALLEL_SAFE',
                      'DEPENDS_ON','THRESHOLD','STATUS','DESCRIPTION']:
            m = re.search(rf'{field}:\s*(.+)', block)
            if m: a[field] = m.group(1).strip()
        if 'ID' in a and re.match(r'\d+\.\d+', a.get('ID','')):
            activities.append(a)
    return activities

def set_field_value(pid, item_id, field_id, value_type, value):
    if value_type == "select":
        gql('''mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){
          updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,
            value:{singleSelectOptionId:$v}}){clientMutationId}}''',
          {"p":pid,"i":item_id,"f":field_id,"v":value})
    elif value_type == "text":
        gql('''mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){
          updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,
            value:{text:$v}}){clientMutationId}}''',
          {"p":pid,"i":item_id,"f":field_id,"v":value})

def main():
    if not TOKEN:
        print("ERROR: PROJECT_TOKEN not set")
        sys.exit(1)

    print("=== VASH 3.0 Project Setup v2 ===\n")

    # Get owner ID
    d = gql('query($l:String!){user(login:$l){id}}', {"l": OWNER})
    if not d: sys.exit(1)
    owner_id = d["user"]["id"]

    # Get or create project
    pid, url = get_or_create_project(owner_id)
    if not pid: sys.exit(1)

    # Get existing fields
    existing_fields = get_fields(pid)
    print(f"\nExisting fields: {list(existing_fields.keys())}")

    # Ensure all required custom fields exist
    print("\nEnsuring custom fields...")
    ensure_select_field(pid, "VASH Status",
        ["PENDING", "IN_PROGRESS", "PASS", "FAIL", "RETRY"], existing_fields)
    ensure_select_field(pid, "Type",
        ["ARTIFACT", "MANUAL"], existing_fields)
    ensure_select_field(pid, "Parallel Safe",
        ["YES", "NO"], existing_fields)
    ensure_text_field(pid, "Depends On", existing_fields)
    ensure_text_field(pid, "Threshold", existing_fields)
    time.sleep(1)

    # Refresh fields after creation
    fields = get_fields(pid)
    print(f"All fields: {list(fields.keys())}")

    # Get existing items to avoid duplicates
    existing_titles = get_existing_items(pid)
    print(f"\nExisting items: {len(existing_titles)}")

    # Parse and add activities
    activities = parse_activities()
    print(f"Activities to add: {len(activities)}\n")

    phase_map = {
        "0": "Phase 0: Setup",    "1": "Phase 1: Vision",
        "2": "Phase 2: Agents",   "3": "Phase 3: Technology",
        "4": "Phase 4: Skills",   "5": "Phase 5: Platform",
        "6": "Phase 6: Blueprint"
    }

    # Find or add built-in Status field
    builtin_status_field = None
    for fname, fdata in fields.items():
        opts = [o["name"] for o in fdata.get("options", [])]
        if "Todo" in opts and "Done" in opts:
            builtin_status_field = fdata
            print(f"Built-in Status field: {fname} (id: {fdata['id']})")
            break

    created = skipped = 0
    for a in activities:
        task_id = a.get("ID","")
        par = a.get("PARALLEL_SAFE","NO")
        status = a.get("STATUS","PENDING")
        atype = a.get("TYPE","ARTIFACT")
        depends = a.get("DEPENDS_ON","NONE")
        threshold = a.get("THRESHOLD","88")
        phase_num = task_id.split(".")[0]
        phase_label = phase_map.get(phase_num, "Phase 0: Setup")

        status_icon = "✅" if status=="PASS" else "⚡" if par=="YES" else "⏳"
        title = f"{status_icon} [{task_id}] {a.get('NAME','')}"

        if title in existing_titles:
            print(f"  ↺ Exists: [{task_id}]")
            skipped += 1
            continue

        body = build_item_body(a)

        # Add item
        d = gql('''mutation($p:ID!,$t:String!,$b:String!){
          addProjectV2DraftIssue(input:{projectId:$p,title:$t,body:$b}){
            projectItem{id}}}''',
          {"p": pid, "t": title, "b": body})

        if not d:
            print(f"  ❌ Failed: [{task_id}]")
            continue

        item_id = d["addProjectV2DraftIssue"]["projectItem"]["id"]

        # Set VASH Status
        vash_fid = fields.get("VASH Status", {}).get("id", "")
        vash_oid = opt_id(fields, "VASH Status", status)
        if vash_fid and vash_oid:
            set_field_value(pid, item_id, vash_fid, "select", vash_oid)

        # Set built-in Status
        if builtin_status_field:
            builtin_map = {"PASS": "Done", "FAIL": "In Progress",
                          "MODIFY": "In Progress", "RETRY": "In Progress",
                          "IN_PROGRESS": "In Progress", "PENDING": "Todo"}
            builtin_val = builtin_map.get(status, "Todo")
            builtin_oid = opt_id(fields, builtin_status_field["name"], builtin_val)
            if builtin_oid:
                set_field_value(pid, item_id, builtin_status_field["id"],
                               "select", builtin_oid)

        # Set Type
        type_fid = fields.get("Type", {}).get("id", "")
        type_oid = opt_id(fields, "Type", atype)
        if type_fid and type_oid:
            set_field_value(pid, item_id, type_fid, "select", type_oid)

        # Set Parallel Safe
        par_fid = fields.get("Parallel Safe", {}).get("id", "")
        par_oid = opt_id(fields, "Parallel Safe", par)
        if par_fid and par_oid:
            set_field_value(pid, item_id, par_fid, "select", par_oid)

        # Set Depends On
        dep_fid = fields.get("Depends On", {}).get("id", "")
        if dep_fid:
            set_field_value(pid, item_id, dep_fid, "text", depends)

        # Set Threshold
        thr_fid = fields.get("Threshold", {}).get("id", "")
        if thr_fid:
            set_field_value(pid, item_id, thr_fid, "text", f"{threshold}/100")

        print(f"  {status_icon} [{task_id}] {a.get('NAME','')[:50]}")
        created += 1
        time.sleep(0.3)

    print(f"\n✅ Done: {created} created, {skipped} skipped")
    print(f"Project: {url}")

if __name__ == "__main__":
    main()
