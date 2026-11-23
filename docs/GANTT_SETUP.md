# Automated issue-field Gantt

This feature generates `docs/GANTT.md` from the **Fields** sidebar on GitHub issues.

## How to schedule an issue

1. Open any issue in `nk25719/FunctionGeneratorESP32`.
2. Under **Fields** set **Start date** and **Target date** (not project custom fields).
3. The resulting Gantt uses these dates inclusive of both endpoints. Closed issues are marked done.

For example, issue #19 has Start date 2026-11-22 and Target date 2026-11-25, so its Gantt bar spans four days.

## Automation

`.github/workflows/gantt.yml` runs on issue creation, editing, closing, reopening, deletion, and native issue field additions/changes/removals (`field_added` and `field_removed`), plus daily and manual execution. It commits the generated Gantt to `main` after the PR is merged.

The generator uses the issue field values REST API with GitHub API version `2026-03-10`: `GET /repos/{owner}/{repo}/issues/{issue_number}/issue-field-values`. The built-in `GITHUB_TOKEN` needs `issues: read`; no personal access token or Project #7 integration is required.

If a date is not set or the end date precedes the start date, the issue remains in the unscheduled table. API access failures fail the job rather than silently reporting issues as unscheduled.

## Test

Run with `GITHUB_TOKEN` set to a token with issues-read access:

```sh
GITHUB_REPOSITORY=nk25719/FunctionGeneratorESP32 python3 scripts/generate_gantt.py
```

Ensure GitHub Actions is enabled and allowed to write contents; restrictive branch rules may require a PR publishing strategy instead of direct bot commits.
