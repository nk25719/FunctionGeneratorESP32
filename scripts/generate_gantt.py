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




def fetch_issue_field_dates(issue_number):
    """Read issue-level Fields from GitHub REST (not Projects fields)."""
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/issue-field-values?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "github-issues-gantt",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        rows = json.load(resp)
    return {
        str(row.get("issue_field_name", "")).strip().lower(): row["value"]
        for row in rows
        if row.get("data_type") == "date"
        and row.get("issue_field_name", "").strip().lower() in ("start date", "target date")
        and isinstance(row.get("value"), str)
    }


def field_date(values, name):
    raw = values.get(name)
    if not raw:
        return None
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
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
    return re.sub(r"[:;\r\n\x00-\x1f]", " ", value).strip()[:43] or "Untitled"


def create_chart(issues):
    scheduled, unscheduled = [], []
    for issue in issues:
        fields = fetch_issue_field_dates(issue["number"])
        start = field_date(fields, "start date")
        end = field_date(fields, "target date")
        if not start or not end or end < start:
            unscheduled.append(issue)
            continue
        scheduled.append((start, end, issue))
    scheduled.sort(key=lambda item: (item[0], item[2]["number"]))
    unscheduled.sort(key=lambda item: item["number"])

    lines = [
        "# GitHub Issues Gantt",
        "",
        f"Source: [Issues](https://github.com/{REPO}/issues). Generated automatically; dates are sourced from the issue sidebar Fields, not Projects.",
        "",
        "```mermaid",
        "gantt",
        "    title FunctionGeneratorESP32 issue schedule",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %b %d",
        "    tickInterval 1day",
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
            "    Set Start date and Target date in issue Fields :setup, 2026-11-22, 1d",
        ])
    lines.extend(["```", "", "## Scheduled issue dates", ""])
    if scheduled:
        lines.extend(["| Issue | Start | Target | State |", "| --- | --- | --- | --- |"])
        for start, end, issue in scheduled:
            title = issue["title"].replace("|", "&#124;").replace("\\n", " ")
            lines.append(
                f"| [#{issue['number']} — {title}](https://github.com/{REPO}/issues/{issue['number']}) "
                f"| {start.isoformat()} | {end.isoformat()} | {issue['state']} |"
            )
    else:
        lines.append("Set Start date and Target date in an issue's Fields section.")
    lines.extend(["", "## Issues without valid scheduled dates", ""])
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
    lines.extend(["", "## Scheduling", "", "Set Start date and Target date directly in the issue sidebar under Fields.", "",
                  "Closing an issue marks its bar as completed. Issues without both valid dates remain in the table; no dates are fabricated.", ""])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}: {len(scheduled)} scheduled, {len(unscheduled)} unscheduled")


if __name__ == "__main__":
    create_chart(fetch_issues())
