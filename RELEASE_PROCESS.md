# Release Process

## 1. Development

All changes originate from GitHub issues and
are reviewed through pull requests.

Every pull request requires a version impact label.

Continuous integration must pass before merging.

## 2. Version management

Merged changes are processed by the automated
versioning and changelog workflow.

The VERSION file is the firmware version source
of truth.

A version increment does not constitute an
official release.

## 3. Release candidate generation

After all intended changes have been merged and
versioning automation has completed:

1. Open GitHub Actions.
2. Select Release Candidate.
3. Select Run workflow.
4. Select the main branch.
5. Wait for all automated checks to pass.
6. Download the release candidate artifact.

The workflow compiles all supported build targets
and generates a ZIP package, manifest, checksums,
release notes and build report.

## 4. Candidate validation

Verify package checksums before use.

Perform physical hardware validation using the
included VALIDATION_CHECKLIST.md.

Record measurements, deviations and test evidence.

A candidate must not be represented as an
approved release before maintainer approval.

## 5. Official release

Official release publication requires:

- Successful automated verification.
- Completed hardware validation.
- Reviewed documentation.
- Confirmed licensing.
- Maintainer approval.
- An immutable Git tag identifying the source.
- Publication of the approved candidate artifacts.

Official release automation will be implemented
in the next development phase.

## 6. Traceability

Every published release must identify:

- Firmware version.
- Source commit.
- Supported board targets.
- Build environment.
- File checksums.
- Release notes.
- Validation evidence.

## 7. Release corrections

Published artifacts and tags must not be silently
replaced.

Corrections require a new version or an explicitly
documented release withdrawal.
