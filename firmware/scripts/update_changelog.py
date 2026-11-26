"""Update the changelog from merged GitHub pull requests."""

import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

SECTIONS = (
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
)


def classify(title, impact):
    kind = re.split(r"[:(!]", title.lower(), maxsplit=1)[0]

    mapping = {
        "feat": "Added",
        "feature": "Added",
        "fix": "Fixed",
        "security": "Security",
        "deprecate": "Deprecated",
        "remove": "Removed",
    }

    if kind in mapping:
        return mapping[kind]

    if impact == "minor":
        return "Added"

    if impact == "patch":
        return "Fixed"

    return "Changed"


def update(root, pr, title, impact, author, repository):
    if pr < 1:
        raise ValueError("Invalid PR number")

    if impact not in {"major", "minor", "patch", "none"}:
        raise ValueError("Invalid version impact")

    path = root / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")

    marker = f"<!-- pr:{pr} -->"

    if marker in text:
        print(f"PR #{pr} already recorded")
        return False

    title = " ".join(title.split())
    title = re.sub(r"([\\`*_\[\]<>])", r"\\\1", title)
    author = " ".join(author.split())

    section = classify(title, impact)

    url = f"https://github.com/{repository}/pull/{pr}"

    entry = (
        f"- {title} ([#{pr}]({url})) "
        f"— @{author} — {impact.upper()} {marker}\n"
    )

    heading = "## [Unreleased]\n"

    if text.count(heading) != 1:
        raise ValueError("Expected one Unreleased section")

    before, remainder = text.split(heading, 1)

    match = re.search(r"(?m)^## ", remainder)

    if match:
        unreleased = remainder[:match.start()]
        history = remainder[match.start():]
    else:
        unreleased = remainder
        history = ""

    target = f"### {section}\n"

    if target not in unreleased:
        unreleased = unreleased.rstrip() + "\n\n" + target

    unreleased = unreleased.replace(
        target,
        target + entry,
        1
    )

    updated = before + heading + unreleased + history
    path.write_text(updated, encoding="utf-8")

    print(f"Recorded PR #{pr} under {section}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--impact", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--repository", required=True)

    args = parser.parse_args()

    update(
        ROOT,
        args.pr,
        args.title,
        args.impact,
        args.author,
        args.repository,
    )
