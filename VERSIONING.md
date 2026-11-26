# Versioning Policy

## Version Format

Firmware follows Semantic Versioning:

MAJOR.MINOR.PATCH

## Source of Truth

The root VERSION file contains the current firmware
version. Automated scripts synchronize version identifiers
across the supported firmware implementations.

## Version Classification

Every pull request must have exactly one version label.

| Label | Meaning |
| --- | --- |
| version:major | Breaking change |
| version:minor | Backward-compatible feature |
| version:patch | Backward-compatible fix |
| version:none | No firmware version increment |

The contributor proposes the version impact.
The reviewer confirms its correctness before merging.

## Automated Version Management

After a qualifying pull request is merged into main,
GitHub Actions updates the version identifiers.

Repeated workflow executions must not increment
the version twice for the same pull request.

Documentation-only changes and unchanged file
relocations do not require firmware version increments.

## Releases

A development version increment does not constitute
an official product release.

Official releases require separate verification,
release artifacts and maintainer approval.

See RELEASE_PROCESS.md.
