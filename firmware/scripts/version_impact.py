"""Determine version impact from GitHub PR labels."""

import json
import sys

VALID_LABELS = {
    "version:major": "major",
    "version:minor": "minor",
    "version:patch": "patch",
    "version:none": "none",
}


def select_impact(labels):
    selected = [
        VALID_LABELS[label]
        for label in labels
        if label in VALID_LABELS
    ]

    if len(selected) != 1:
        raise ValueError(
            "Exactly one version impact label is required."
        )

    return selected[0]


if __name__ == "__main__":
    data = json.load(sys.stdin)

    labels = [
        item["name"] if isinstance(item, dict) else item
        for item in data
    ]

    print(select_impact(labels))
