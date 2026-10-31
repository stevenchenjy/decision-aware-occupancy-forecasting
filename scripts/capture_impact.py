#!/usr/bin/env python3
"""Save an owner-only evidence snapshot using an already authenticated gh CLI.

This reads GitHub only. It does not request credentials, change permissions,
track demo visitors, or publish metrics. Traffic may include the owner's tests.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

REPOSITORY = "stevenchenjy/decision-aware-occupancy-forecasting"
ROOT = Path(__file__).resolve().parents[1]


def api(endpoint):
    response = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/{endpoint}".rstrip("/")], capture_output=True, text=True)
    if response.returncode:
        return {"available": False, "error": response.stderr.strip()}
    return {"available": True, "data": json.loads(response.stdout)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Private directory outside the repository, or local-impact/ (gitignored)")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == ROOT or (ROOT in output.parents and output.relative_to(ROOT).parts[0] != "local-impact"):
        raise SystemExit("Save private metrics outside the repository or in its gitignored local-impact/ directory.")
    repository = api("")
    if not repository["available"]:
        raise SystemExit(repository["error"])
    raw = repository["data"]
    snapshot = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": REPOSITORY,
        "public_counts": {key: raw[key] for key in ["stargazers_count", "forks_count", "subscribers_count", "open_issues_count"]},
        "traffic_window_note": "GitHub rolling 14-day visitor/clone data; includes testing and does not establish successful reuse.",
        "traffic": {name: api(f"traffic/{name}") for name in ["views", "clones", "popular/referrers", "popular/paths"]},
    }
    output.mkdir(parents=True, exist_ok=True)
    name = "github-impact-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = output / name
    path.write_text(json.dumps(snapshot, indent=2) + "\n")
    print("Saved private evidence snapshot:", path)
    print("Public counts:", snapshot["public_counts"])
    for name, value in snapshot["traffic"].items():
        print(name + ":", "captured" if value["available"] else "unavailable; see the snapshot for the exact error")


if __name__ == "__main__":
    main()
