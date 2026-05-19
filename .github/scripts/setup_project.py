#!/usr/bin/env python3
"""VASH 3.0 GitHub Project Setup — Creates ProjectV2 with all activities"""
import re, json, os, time, urllib.request, urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN","")
OWNER = "mazharr-hussain"
REPO  = "vash3-framework"

def gql(query, variables=None):
    url = "https://api.github.com/graphql"
    headers = {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
    body = json.dumps({"query":query,"variables":variables or {}}).encode()
    req = urllib.request.Request(url,data=body,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read())
            return d.get("data"), d.get("errors")
    except urllib.error.HTTPError as e:
        return None, e.read().decode()

def parse_activities():
    content = open("knowledge/activity_list.md").read()
    activities = []
    for block in re.split(r'\n---\n', content):
        if 'ID:' not in block: continue
        a = {}
        for f in ['ID','NAME','TYPE','PHASE','PARALLEL_SAFE','DEPENDS_ON','THRESHOLD','STATUS','DESCRIPTION']:
            m = re.search(rf'{f}:\s*(.+)', block)
            if m: a[f] = m.group(1).strip()
        if 'ID' in a and re.match(r'\d+\.\d+', a.get('ID','')):
            activities.append(a)
    return activities

def main():
    if not TOKEN: print("ERROR: No GITHUB_TOKEN"); return
    print("=== VASH 3.0 GitHub Project Setup ===")

    # Get owner ID
    d, e = gql('query($l:String!){user(login:$l){id}}', {"l":OWNER})
    if not d: print(f"Error: {e}"); return
    owner_id = d["user"]["id"]
    print(f"Owner: {owner_id}")

    # Create ProjectV2
    d, e = gql('''mutation($o:ID!,$t:String!){
      createProjectV2(input:{ownerId:$o,title:$t}){
        projectV2{id number url}}}''',
      {"o":owner_id,"t":"VASH 3.0 — Activity Board"})
    if not d: print(f"Error creating project: {e}"); return
    proj = d["createProjectV2"]["projectV2"]
    pid = proj["id"]
    print(f"✅ Project: {proj['url']}")

    # Add custom fields
    def add_select(name, opts):
        d, e = gql('''mutation($p:ID!,$n:String!,$o:[ProjectV2SingleSelectFieldOptionInput!]!){
          addProjectV2CustomField(input:{projectId:$p,name:$n,dataType:SINGLE_SELECT,singleSelectOptions:$o}){
            clientMutationId}}''',
          {"p":pid,"n":name,"o":[{"name":o,"color":"GRAY","description":""} for o in opts]})
        print(f"  {'✅' if not e else '❌'} Field: {name}")

    def add_text(name):
        d, e = gql('''mutation($p:ID!,$n:String!){
          addProjectV2CustomField(input:{projectId:$p,name:$n,dataType:TEXT}){
            clientMutationId}}''', {"p":pid,"n":name})
        print(f"  {'✅' if not e else '❌'} Field: {name}")

    print("\nAdding fields...")
    add_select("Phase", ["Phase 0: Setup","Phase 1: Vision","Phase 2: Agents",
                         "Phase 3: Technology","Phase 4: Skills","Phase 5: Platform","Phase 6: Blueprint"])
    add_select("Status", ["PENDING","IN_PROGRESS","PASS","FAIL","MODIFY"])
    add_select("Parallel Safe", ["YES","NO"])
    add_select("Type", ["ARTIFACT","MANUAL"])
    add_text("Depends On")
    add_text("Threshold")
    time.sleep(1)

    # Get field IDs
    d, e = gql('''query($p:ID!){node(id:$p){...on ProjectV2{
      fields(first:20){nodes{
        ...on ProjectV2Field{id name}
        ...on ProjectV2SingleSelectField{id name options{id name}}}}}}}''',
      {"p":pid})
    fields = {}
    if d:
        for f in d["node"]["fields"]["nodes"]:
            if f: fields[f.get("name")] = f

    def opt_id(field_name, opt_name):
        for o in fields.get(field_name,{}).get("options",[]):
            if o["name"] == opt_name: return o["id"]
        return None

    # Add activities
    activities = parse_activities()
    print(f"\nAdding {len(activities)} activities...")
    phase_map = {"0":"Phase 0: Setup","1":"Phase 1: Vision","2":"Phase 2: Agents",
                 "3":"Phase 3: Technology","4":"Phase 4: Skills",
                 "5":"Phase 5: Platform","6":"Phase 6: Blueprint"}

    for a in activities:
        tid = a.get('ID','')
        phase = phase_map.get(tid.split('.')[0],"Phase 0: Setup")
        par = a.get('PARALLEL_SAFE','NO')
        stat = a.get('STATUS','PENDING')
        icon = "✅" if stat=="PASS" else "⚡" if par=="YES" else "⏳"
        title = f"{icon} [{tid}] {a.get('NAME','')}"
        body = f"**Phase:** {a.get('PHASE','')}\n**Type:** {a.get('TYPE','')}\n**Parallel:** {par}\n**Depends:** {a.get('DEPENDS_ON','NONE')}\n**Threshold:** {a.get('THRESHOLD','88')}/100\n**Status:** {stat}\n\n{a.get('DESCRIPTION','')}"

        d, e = gql('''mutation($p:ID!,$t:String!,$b:String!){
          addProjectV2DraftIssue(input:{projectId:$p,title:$t,body:$b}){
            projectItem{id}}}''', {"p":pid,"t":title,"b":body})
        if not d: print(f"  ❌ {tid}"); continue
        item_id = d["addProjectV2DraftIssue"]["projectItem"]["id"]

        def set_select(fname, val):
            fid = fields.get(fname,{}).get("id")
            oid = opt_id(fname, val)
            if not fid or not oid: return
            gql('''mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){
              updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,
                value:{singleSelectOptionId:$v}}){clientMutationId}}''',
              {"p":pid,"i":item_id,"f":fid,"v":oid})

        def set_text(fname, val):
            fid = fields.get(fname,{}).get("id")
            if not fid: return
            gql('''mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){
              updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,
                value:{text:$v}}){clientMutationId}}''',
              {"p":pid,"i":item_id,"f":fid,"v":val})

        set_select("Phase", phase)
        set_select("Status", stat)
        set_select("Parallel Safe", par)
        set_select("Type", a.get('TYPE','ARTIFACT'))
        set_text("Depends On", a.get('DEPENDS_ON','NONE'))
        set_text("Threshold", a.get('THRESHOLD','88'))

        print(f"  {icon} [{tid}] {a.get('NAME','')[:50]}")
        time.sleep(0.2)

    print(f"\n✅ Project ready: {proj['url']}")

if __name__ == "__main__":
    main()
