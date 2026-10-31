OCCUPANCY SAVED-OUTPUT REPLAY KIT

Junyu Chen. Research with guidance from Prof. Chong Li.

Recompute three reported policy rows using Python 3.10 or later. The command uses
only Python's standard library and the compact records included in this archive.
It works offline after download. It does not train models or run a controller.

1. Extract the ZIP into a folder.
2. Open a terminal in the extracted occupancy-replay-kit folder.
3. Run:

   python replay.py --receipt reproduction-receipt.json --csv comparison.csv

   On systems whose Python command is python3, use python3 instead of python.
   On Windows, py replay.py may also work if Python Launcher is installed.

Expected reported comparison:

Model        Threshold  Minimum hours  Windows  Intervals  Conflicts  Load (kWh)
hybrid       0.875      1              14       259        0          490.1
historical   0.950      1              12        66        0           94.6
lightgbm     0.950      1              19       265       11          493.9

The command checks the archive's file hashes and reconciles each reported row.
If you modify a file, keep an original copy to run the integrity-checked replay.

Optional exploration of the same historical records:

   python replay.py --model hybrid --threshold 0.85 --min-hours 2

Changed settings are labelled exploratory. They cannot establish a new validated
policy on this already inspected test period. Use --help to see all options.

OPTIONAL FEEDBACK

The receipt records the kit version, source commit, data hashes, Python version,
OS family and observed results. It does not include a username, hostname, home
directory or IP address. Review it before sharing it yourself. It contains no
proof of identity or independent use and can be edited by its holder.

Nothing is sent automatically. If you choose to report an attempt, including one
that failed, describe what happened and attach the receipt if useful:
https://github.com/stevenchenjy/decision-aware-occupancy-forecasting/issues/new?template=reproduction.yml

You can also open notebooks/try_the_study.ipynb in a local Jupyter environment.
Jupyter and the optional plotting library are not needed for the replay command.

DATA, LICENSE AND SCOPE

Original software is MIT-licensed. DATA.md and LICENSING.md explain the separate
data and manuscript terms. The compact records derive from the cleaned LBNL
Building 59 release and saved predictions. The archive is not a new dataset or
empirical validation. It does not establish source availability at an earlier
forecast time, physical absence, future performance, or measured energy savings.

kit-manifest.json identifies the exact source commit and each included file hash.
The release also supplies a SHA-256 checksum for the archive. Citation files
attribute the original study; this kit is a separate software distribution.

Paper and citation:
https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/paper.html
Browser demo:
https://stevenchenjy.github.io/decision-aware-occupancy-forecasting/demo/
Source repository:
https://github.com/stevenchenjy/decision-aware-occupancy-forecasting
