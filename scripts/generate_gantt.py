#!/usr/bin/env python3
"""Generate a Mermaid Gantt chart from dated GitHub Issues."""
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "nk25719/FunctionGeneratorESP32")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
OUTPUT = Path(os.environ.get("GANTT_OUTPUT", "docs/GANTT.md"))
DATE_FIELDS = {
    "start": re.compile(r"^\s*(?:Start date|Start):\s*(\d{4}-\d{2}-\d{2})\s*$", re.I | re.M),
    "due": re.compile(r"^\s*(?:Due date|End date|Target date):\s*(\d{4}-\d{2}-\d{2})\s*$", re.I | re.M),
}


def fetch_issues():
    issues = []
    for page in range(1, 101):
        url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "github-issues-gantt"}
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            break
    return issues



def fetch_project_dates():
    """Return Project V2 date fields by issue number, if a project token is available."""
    token = os.environ.get("PROJECT_TOKEN", "")
    if not token:
        print("Project date sync unavailable: PROJECT_TOKEN not configured.")
        return {}
    query = """
    query($login: String!, $number: Int!, $cursor: String) {
      user(login: $login) {
        projectV2(number: $number) {
          items(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              content {
                ... on Issue {
                  number
                  repository { nameWithOwner }
                }
              }
              fieldValues(first: 50) {
                nodes {
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field { ... on ProjectV2FieldCommon { name } }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    dates = {}
    cursor = None
    while True:
        payload = json.dumps({
            "query": query,
            "variables": {"login": "nk25719", "number": 7, "cursor": cursor},
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.github.com/graphql", payload,
            {"Authorization": f"Bearer {token}",
             "Accept": "application/vnd.github+json",
             "Content-Type": "application/json",
             "User-Agent": "github-issues-gantt"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.load(response)
        if data.get("errors"):
            raise RuntimeError(f"GitHub Projects API: {data['errors']}")
        project = (data.get("data") or {}).get("user", {}) or {}
        project = project.get("projectV2")
        if not project:
            raise RuntimeError("GitHub Project #7 not accessible to PROJECT_TOKEN")
        items = project["items"]
        for item in items["nodes"]:
            issue = item.get("content") or {}
            if issue.get("repository", {}).get("nameWithOwner", "").lower() != REPO.lower():
                continue
            if not issue.get("number"):
                continue
            fields = {}
            for value in item.get("fieldValues", {}).get("nodes", []):
                field = (value or {}).get("field") or {}
                if field.get("name") and value.get("date"):
                    fields[field["name"].strip().lower()] = value["date"]
            dates[issue["number"]] = fields
        page = items["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]
    return dates


def project_date(values, names):
    for name in names:
        raw = values.get(name)
        if raw:
            try:
                return dt.date.fromisoformat(raw)
            except ValueError:
                pass
    return None

def parse_date(body, key):
    match = DATE_FIELDS[key].search(body or "")
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def safe_title(value):
    # Mermaid uses colons, semicolons and line breaks as syntax.
    return re.sub(r"[:;\r\n\x00-\x1f]", " ", value).strip()[:75] or "Untitled"


def create_chart(issues, project_dates=None):
    project_dates = project_dates or {}
    scheduled, unscheduled = [], []
    for issue in issues:
        fields = project_dates.get(issue["number"], {})
        start = project_date(fields, ("start date", "start")) or parse_date(issue.get("body"), "start")
        end = project_date(fields, ("target date", "due date", "end date")) or parse_date(issue.get("body"), "due")
        if not start or not end or end < start:
            unscheduled.append(issue)
            continue
        scheduled.append((start, end, issue))
    scheduled.sort(key=lambda item: (item[0], item[2]["number"]))
    unscheduled.sort(key=lambda item: item["number"])

    lines = [
        "# GitHub Issues Gantt",
        "",
        f"Source: [Issues](https://github.com/{REPO}/issues). Generated automatically; dates are *planned*, not inferred from creation/closure timestamps.",
        "",
        "```mermaid",
        "gantt",
        "    title FunctionGeneratorESP32 issue schedule",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %b %d",
    ]
    if scheduled:
        lines.append("    section Scheduled issues")
        for start, end, issue in scheduled:
            duration = (end - start).days + 1
            completed = "done, " if issue["state"] == "closed" else ""
            lines.append(
                f"    #{issue['number']} {safe_title(issue['title'])} "
                f":{completed}issue{issue['number']}, {start.isoformat()}, {duration}d"
            )
    else:
        lines.extend([
            "    section Getting started",
            "    Add Start date and Due date to an issue :setup, 2026-11-22, 1d",
        ])
    lines.extend(["```", "", "## Issues without valid scheduled dates", ""])
    if unscheduled:
        lines.append("| Issue | Status |")
        lines.append("| --- | --- |")
        for issue in unscheduled:
            title = issue["title"].replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| [#{issue['number']} — {title}](https://github.com/{REPO}/issues/{issue['number']}) "
                f"| {issue['state']} |"
            )
    else:
        lines.append("All issues have valid schedule dates.")
    lines.extend(["", "## Date format", "", "Add these lines to the issue description:", "",
                  "```text", "Start date: 2026-11-23", "Due date: 2026-12-05", "```", "",
                  "Closing an issue marks its bar as completed. Issues without both valid dates remain in the table; no dates are fabricated.", ""])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}: {len(scheduled)} scheduled, {len(unscheduled)} unscheduled")


if __name__ == "__main__":
    create_chart(fetch_issues(), fetch_project_dates())
