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

The workflow uses the repository `GITHUB_TOKEN` and does not read GitHub Projects custom date fields. **Project #7 dates are not automatically synchronized.** To use those fields instead requires a separate Projects GraphQL integration and an access token with the relevant project permissions.

## Testing locally

```sh
GITHUB_REPOSITORY=nk25719/FunctionGeneratorESP32 GITHUB_TOKEN="$(gh auth token)" python3 scripts/generate_gantt.py
```

Check `docs/GANTT.md` afterward. GitHub Actions must be allowed to write repository contents, and branch rules must permit its commits; otherwise the workflow reports an error without modifying issues.
