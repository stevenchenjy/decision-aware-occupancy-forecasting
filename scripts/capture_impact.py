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


def api(endpoint, *, paginated=False):
    command = ["gh", "api", f"repos/{REPOSITORY}/{endpoint}".rstrip("/")]
    if paginated:
        command.extend(["--paginate", "--slurp"])
    response = subprocess.run(command, capture_output=True, text=True)
    if response.returncode:
        return {"available": False, "error": response.stderr.strip()}
    data = json.loads(response.stdout)
    if paginated:
        data = [item for page in data for item in page]
    return {"available": True, "data": data}


def participation(owner, stars, issues):
    """Describe account activity, without inferring independence or successful use."""
    result = {"interpretation": "Non-owner accounts may still be collaborators. A report candidate needs manual reading before any reproduction or use claim."}
    if stars["available"]:
        users = stars["data"]
        result["owner_has_starred"] = any(user["login"].casefold() == owner.casefold() for user in users)
        result["non_owner_non_bot_star_accounts"] = sorted({user["login"] for user in users if user["login"].casefold() != owner.casefold() and user.get("type") != "Bot" and not user["login"].endswith("[bot]")})
    else:
        result["stars_available"] = False
        result["stars_error"] = stars["error"]
    if issues["available"]:
        external = [item for item in issues["data"] if not item.get("pull_request") and item["user"]["login"].casefold() != owner.casefold() and item["user"].get("type") != "Bot" and not item["user"]["login"].endswith("[bot]")]
        result["non_owner_non_bot_issues"] = [{key: item[key] for key in ["number", "title", "html_url", "state"]} for item in external]
        result["reproduction_report_candidates"] = [item["number"] for item in external if item["title"].casefold().startswith("reproduction:")]
    else:
        result["issues_available"] = False
        result["issues_error"] = issues["error"]
    return result


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
        "participation": participation(raw["owner"]["login"], api("stargazers?per_page=100", paginated=True), api("issues?state=all&per_page=100", paginated=True)),
        "traffic_window_note": "GitHub rolling 14-day visitor/clone data; includes testing and does not establish successful reuse.",
        "traffic": {name: api(f"traffic/{name}") for name in ["views", "clones", "popular/referrers", "popular/paths"]},
    }
    output.mkdir(parents=True, exist_ok=True)
    name = "github-impact-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = output / name
    path.write_text(json.dumps(snapshot, indent=2) + "\n")
    print("Saved private evidence snapshot:", path)
    print("Public counts:", snapshot["public_counts"])
    print("Account activity:", snapshot["participation"])
    for name, value in snapshot["traffic"].items():
        print(name + ":", "captured" if value["available"] else "unavailable; see the snapshot for the exact error")


if __name__ == "__main__":
    main()
