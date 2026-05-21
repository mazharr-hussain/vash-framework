#!/usr/bin/env python3
"""Diagnostic — prints all project fields and items."""
import os, json, urllib.request, urllib.error, sys

TOKEN = os.environ.get("PROJECT_TOKEN", "")
OWNER = "mazharr-hussain"

def gql(query, variables=None):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read())
            if d.get("errors"):
                print(f"GQL error: {d['errors']}")
            return d.get("data")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:200]}")
        return None

d = gql('''query($l:String!){user(login:$l){
  projectsV2(first:10){nodes{id title number url
    fields(first:30){nodes{
      __typename
      ...on ProjectV2Field{id name}
      ...on ProjectV2SingleSelectField{id name options{id name}}
    }}
  }}
}}''', {"l": OWNER})

if not d:
    print("No data returned"); sys.exit(1)

for p in d["user"]["projectsV2"]["nodes"]:
    print(f"\n=== Project: {p['title']} ===")
    print(f"URL: {p['url']}")
    print(f"Fields ({len(p['fields']['nodes'])}):")
    for f in p["fields"]["nodes"]:
        if not f: continue
        print(f"  [{f['__typename']}] {f.get('name')} (id: {f.get('id','')})")
        for o in f.get("options", []):
            print(f"    option: {o['name']} (id: {o['id']})")
