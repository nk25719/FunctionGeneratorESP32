# Automated GitHub Issues Gantt

This feature adds a Mermaid Gantt chart to `docs/GANTT.md`.

## How to schedule an issue

Add these two lines anywhere in an issue description (ISO 8601 dates):

```text
Start date: 2026-11-23
Due date: 2026-12-05
```

Issue state controls the completion marker; closed issues are shown as `done`. Issues missing dates, with invalid dates, or with a due date before the start date appear below the chart instead of receiving guessed dates.

## Automation

`.github/workflows/gantt.yml` runs when an issue is opened, edited, closed, reopened, or deleted; once daily; or on manual dispatch. It regenerates `docs/GANTT.md` and commits changes to `main` once the PR is merged.

## Project #7 date fields

The generator now supports GitHub Project #7's **Start date** and **Target date** fields, with issue-description dates as fallback. Project dates take precedence when configured.

To enable them, create a fine-grained or classic personal access token authorized to read your user-owned GitHub Project (for a classic PAT, use the `read:project` scope). Store it as the repository Actions secret `PROJECT_TOKEN` under **Settings → Secrets and variables → Actions**. Keep the token private. The default `GITHUB_TOKEN` alone generally cannot access user-owned Projects V2.

Until `PROJECT_TOKEN` is configured, the workflow continues to use issue-body dates. On a permission failure, the workflow reports an error rather than silently making up dates. Project updates alone do not fire repository issue events, so the daily cron or **Run workflow** button is needed to refresh the chart immediately after editing project-only dates.

## Testing locally

```sh
GITHUB_REPOSITORY=nk25719/FunctionGeneratorESP32 GITHUB_TOKEN="$(gh auth token)" python3 scripts/generate_gantt.py
```

Check `docs/GANTT.md` afterward. GitHub Actions must be allowed to write repository contents, and branch rules must permit its commits; otherwise the workflow reports an error without modifying issues.
