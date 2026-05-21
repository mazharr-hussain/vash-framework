#!/usr/bin/env python3
"""
VASH 3.0 — GitHub Project Library
Single source of truth for all activity data.
Reads and writes GitHub ProjectV2 via GraphQL API.
LAW 1: Python stdlib only
LAW 2: Fully automated
LAW 3: Standard GraphQL patterns
"""

import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


class ProjectClient:
    """All GitHub ProjectV2 operations via GraphQL."""

    def __init__(self):
        self.token = os.environ.get("PROJECT_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
        self.owner = "mazharr-hussain"
        self.repo = "vash3-framework"
        self.project_name = "VASH 3.0 — Activity Board"
        self._project_id = os.environ.get("PROJECT_ID", "")
        self._all_items_cache = None

    # ─────────────────────────────────────────────
    # GraphQL core
    # ─────────────────────────────────────────────

    def _gql(self, query: str, variables: dict = None) -> tuple:
        """Execute a GraphQL query. Returns (data, errors)."""
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        payload = {"query": query, "variables": variables or {}}
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                d = json.loads(r.read())
                return d.get("data"), d.get("errors")
        except urllib.error.HTTPError as e:
            return None, e.read().decode()
        except Exception as e:
            return None, str(e)

    # ─────────────────────────────────────────────
    # Project discovery
    # ─────────────────────────────────────────────

    def get_project_id(self) -> str:
        """Get project ID — from env or by searching user projects."""
        if self._project_id:
            return self._project_id

        query = """query($login: String!) {
          user(login: $login) {
            projectsV2(first: 20) {
              nodes { id title number }
            }
          }
        }"""
        data, err = self._gql(query, {"login": self.owner})
        if err or not data:
            print(f"[ProjectLib] Error finding project: {err}")
            return ""

        for p in data["user"]["projectsV2"]["nodes"]:
            if self.project_name in p.get("title", ""):
                self._project_id = p["id"]
                return self._project_id

        print(f"[ProjectLib] Project '{self.project_name}' not found")
        return ""

    # ─────────────────────────────────────────────
    # Field discovery
    # ─────────────────────────────────────────────

    def _get_fields(self, project_id: str) -> dict:
        """Get all field definitions including option IDs."""
        query = """query($pid: ID!) {
          node(id: $pid) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2Field { id name }
                  ... on ProjectV2SingleSelectField {
                    id name
                    options { id name }
                  }
                }
              }
            }
          }
        }"""
        data, err = self._gql(query, {"pid": project_id})
        if err or not data:
            return {}
        fields = {}
        for f in data["node"]["fields"]["nodes"]:
            if f:
                fields[f.get("name", "")] = f
        return fields

    def _get_option_id(self, fields: dict, field_name: str, option_name: str) -> str:
        """Get option ID for a single select field."""
        for opt in fields.get(field_name, {}).get("options", []):
            if opt["name"] == option_name:
                return opt["id"]
        return ""

    # ─────────────────────────────────────────────
    # Item reading
    # ─────────────────────────────────────────────

    def _get_all_items(self, project_id: str, force_refresh: bool = False) -> list:
        """Get all project items with their fields and body."""
        if self._all_items_cache and not force_refresh:
            return self._all_items_cache

        query = """query($pid: ID!, $cursor: String) {
          node(id: $pid) {
            ... on ProjectV2 {
              items(first: 100, after: $cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  content {
                    ... on DraftIssue {
                      title
                      body
                    }
                  }
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field { ... on ProjectV2SingleSelectField { name } }
                      }
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field { ... on ProjectV2Field { name } }
                      }
                    }
                  }
                }
              }
            }
          }
        }"""

        all_items = []
        cursor = None

        while True:
            data, err = self._gql(query, {"pid": project_id, "cursor": cursor})
            if err or not data:
                break

            items_data = data["node"]["items"]
            for item in items_data["nodes"]:
                if not item or not item.get("content"):
                    continue

                parsed = self._parse_item(item)
                if parsed:
                    all_items.append(parsed)

            if not items_data["pageInfo"]["hasNextPage"]:
                break
            cursor = items_data["pageInfo"]["endCursor"]

        self._all_items_cache = all_items
        return all_items

    def _parse_item(self, item: dict) -> dict:
        """Parse a project item into a clean activity dict."""
        content = item.get("content", {})
        title = content.get("title", "")
        body = content.get("body", "")

        # Extract task_id from title: "[0.1] Create repo..." or "✅ ⚡ [0.1] ..."
        tid_match = re.search(r'\[(\d+\.\d+)\]', title)
        if not tid_match:
            return {}
        task_id = tid_match.group(1)

        # Extract name from title after [task_id]
        name_match = re.search(r'\[\d+\.\d+\]\s*(.+)', title)
        name = name_match.group(1).strip() if name_match else title

        # Parse field values
        fields = {}
        for fv in item.get("fieldValues", {}).get("nodes", []):
            if not fv:
                continue
            field_name = fv.get("field", {}).get("name", "")
            if "name" in fv:
                fields[field_name] = fv["name"]
            elif "text" in fv:
                fields[field_name] = fv["text"]

        # Parse body for description
        description = self._parse_body_field(body, "Description") or body[:200]

        return {
            "item_id": item["id"],
            "task_id": task_id,
            "name": name,
            "title": title,
            "body": body,
            "description": description,
            "status": fields.get("VASH Status", "PENDING"),
            "phase": fields.get("Phase", ""),
            "parallel_safe": fields.get("Parallel Safe", "NO"),
            "type": fields.get("Type", "ARTIFACT"),
            "depends_on": fields.get("Depends On", "NONE"),
            "threshold": (lambda s: int(s) if s else 88)(
                re.sub(r'[^0-9]', '', fields.get("Threshold", "88") or "88")),
        }

    def _parse_body_field(self, body: str, field_name: str) -> str:
        """Extract a field value from item body markdown."""
        # Look for **Description:** or **field_name:**\n content
        pattern = rf'\*\*{field_name}:\*\*\s*\n(.*?)(?=\n\*\*|\Z)'
        m = re.search(pattern, body, re.DOTALL)
        if m:
            return m.group(1).strip()
        # Also try inline: **Description:** value
        pattern2 = rf'\*\*{field_name}:\*\*\s*(.+)'
        m2 = re.search(pattern2, body)
        if m2:
            return m2.group(1).strip()
        return ""

    # ─────────────────────────────────────────────
    # Public activity methods
    # ─────────────────────────────────────────────

    def get_activity(self, task_id: str) -> dict:
        """Get full activity details from Project."""
        pid = self.get_project_id()
        if not pid:
            return {}
        items = self._get_all_items(pid)
        for item in items:
            if item["task_id"] == task_id:
                return item
        return {}

    def get_threshold(self, task_id: str) -> int:
        """Get threshold for an activity."""
        activity = self.get_activity(task_id)
        return activity.get("threshold", 88)

    def get_description(self, task_id: str) -> str:
        """Get full description from item body."""
        activity = self.get_activity(task_id)
        return activity.get("description", "")

    def _deps_met(self, activity: dict, all_items: list) -> bool:
        """Check if all dependencies are PASS."""
        depends = activity.get("depends_on", "NONE")
        if not depends or depends.upper() == "NONE":
            return True
        dep_ids = [d.strip() for d in depends.split(",")]
        status_map = {i["task_id"]: i["status"] for i in all_items}
        for dep in dep_ids:
            if status_map.get(dep, "PENDING") != "PASS":
                return False
        return True

    def get_next_activity(self) -> dict:
        """Get next PENDING activity with all dependencies PASS."""
        pid = self.get_project_id()
        if not pid:
            return {}
        items = self._get_all_items(pid)

        # Sort by task_id numerically
        def sort_key(item):
            parts = item["task_id"].split(".")
            return (int(parts[0]), int(parts[1]))

        sorted_items = sorted(items, key=sort_key)

        for item in sorted_items:
            if item["status"] == "PENDING" and self._deps_met(item, items):
                return item
        return {}

    def get_parallel_activities(self) -> list:
        """Get all PENDING PARALLEL_SAFE activities with deps met."""
        pid = self.get_project_id()
        if not pid:
            return []
        items = self._get_all_items(pid)

        result = []
        for item in items:
            if (item["status"] == "PENDING" and
                    item["parallel_safe"] == "YES" and
                    self._deps_met(item, items)):
                result.append(item)

        # Sort by task_id
        result.sort(key=lambda x: (int(x["task_id"].split(".")[0]),
                                    int(x["task_id"].split(".")[1])))
        return result

    def get_all_activities(self) -> list:
        """Get all activities sorted by task_id."""
        pid = self.get_project_id()
        if not pid:
            return []
        items = self._get_all_items(pid)
        items.sort(key=lambda x: (int(x["task_id"].split(".")[0]),
                                   int(x["task_id"].split(".")[1])))
        return items

    # ─────────────────────────────────────────────
    # Status updates
    # ─────────────────────────────────────────────

    def update_status(self, task_id: str, status: str) -> bool:
        """Update activity status in Project."""
        pid = self.get_project_id()
        if not pid:
            return False

        # Get item
        activity = self.get_activity(task_id)
        if not activity:
            print(f"[ProjectLib] Activity {task_id} not found")
            return False
        item_id = activity["item_id"]

        # Get fields
        fields = self._get_fields(pid)
        status_field = fields.get("VASH Status", {})
        if not status_field:
            return False

        option_id = self._get_option_id(fields, "VASH Status", status)
        if not option_id:
            print(f"[ProjectLib] Status option '{status}' not found")
            return False

        query = """mutation($pid: ID!, $iid: ID!, $fid: ID!, $oid: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $pid
            itemId: $iid
            fieldId: $fid
            value: { singleSelectOptionId: $oid }
          }) { clientMutationId }
        }"""
        data, err = self._gql(query, {
            "pid": pid,
            "iid": item_id,
            "fid": status_field["id"],
            "oid": option_id
        })

        if err:
            print(f"[ProjectLib] Status update error: {err}")
            return False

        # Invalidate cache
        self._all_items_cache = None
        print(f"[ProjectLib] {task_id} → {status}")
        return True

    # ─────────────────────────────────────────────
    # Activity format for prompts
    # ─────────────────────────────────────────────

    def format_for_prompt(self, task_id: str) -> str:
        """Format activity details for inclusion in PE prompt."""
        activity = self.get_activity(task_id)
        if not activity:
            return f"Activity {task_id} not found in project"
        return "\n".join([
            f"ID: {activity['task_id']}",
            f"NAME: {activity['name']}",
            f"TYPE: {activity['type']}",
            f"PHASE: {activity['phase']}",
            f"THRESHOLD: {activity['threshold']}/100",
            f"DEPENDS_ON: {activity['depends_on']}",
            f"DESCRIPTION: {activity['description']}",
        ])

    def update_ava_result(self, task_id: str, score: int,
                          round_num: int, verdict: str) -> bool:
        """Update Last AvA Result section in item body after each AvA run."""
        pid = self.get_project_id()
        if not pid:
            return False
        activity = self.get_activity(task_id)
        if not activity:
            return False
        item_id = activity["item_id"]
        body = activity.get("body", "")
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        new_result = (
            "## Last AvA Result\n"
            "- **Score:** " + str(score) + "/100\n"
            "- **Round:** " + str(round_num) + "\n"
            "- **Verdict:** " + verdict + "\n"
            "- **Updated:** " + ts
        )
        if "## Last AvA Result" in body:
            start = body.find("## Last AvA Result")
            rest = body[start:]
            end = len(rest)
            for marker in ["\n## ", "\n---"]:
                idx = rest.find(marker, 5)
                if 0 < idx < end:
                    end = idx
            body = body[:start] + new_result + rest[end:]
        else:
            body = body + "\n\n" + new_result
        query = """mutation($iid: ID!, $title: String!, $body: String!) {
          updateProjectV2DraftIssue(input: {
            draftIssueId: $iid title: $title body: $body
          }) { draftIssue { id } } }"""
        data, err = self._gql(query, {
            "iid": item_id, "title": activity["title"], "body": body
        })
        if err:
            print("[ProjectLib] Body update error: " + str(err)[:100])
            return False
        self._all_items_cache = None
        return True
