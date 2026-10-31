#!/usr/bin/env python3
"""Build a small reproducible replay ZIP from a specific committed source version."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TAG = "replay-kit-v1"
FILES = ["replay.py", "src/demo_analysis.py", "docs/demo/data.json", "notebooks/try_the_study.ipynb",
         "LICENSE", "LICENSING.md", "DATA.md", "CLAIMS_AND_LIMITATIONS.md", "CITATION.cff", "docs/citation.bib"]


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(ROOT), *arguments])


def archive(source_ref="HEAD"):
    commit = git("rev-parse", "--verify", "--end-of-options", source_ref + "^{commit}").decode().strip()
    files = {name: git("show", f"{commit}:{name}") for name in FILES}
    files["README.txt"] = git("show", f"{commit}:replay/README.txt")
    manifest = {"release_tag": TAG, "source_commit": commit,
                "files": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())}}
    files["kit-manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo("occupancy-replay-kit/" + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return stream.getvalue(), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD", help="Commit or existing Git ref to package; uncommitted files are excluded")
    parser.add_argument("--output", type=Path, required=True, help="Artifact directory outside the repository")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Keep generated release archives outside the repository")
    content, manifest = archive(args.ref)
    output.mkdir(parents=True, exist_ok=True)
    name = "occupancy-replay-kit-v1.zip"
    (output / name).write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {name}\n", encoding="utf-8")
    print(json.dumps({"archive": str(output / name), "bytes": len(content), "sha256": digest,
                      "source_commit": manifest["source_commit"], "files": len(manifest["files"])}, indent=2))


if __name__ == "__main__":
    main()
