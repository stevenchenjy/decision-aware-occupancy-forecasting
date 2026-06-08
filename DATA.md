# Data

## Dataset

Dataset name: LBNL Building 59 Office Building Dataset

Dryad DOI: `10.7941/D1N33Q`

Source link: <https://doi.org/10.7941/D1N33Q>

The project uses Building 59 selected south-zone streams from the extracted Dryad package.

## Raw Data Policy

Raw data is not committed to this repository. The raw dataset is large and should be downloaded from Dryad by each researcher.

The repository expects the extracted data to be placed at:

```text
doi_10_7941_D1N33Q__v20220202/Building_59/Bldg59_clean data/
```

This path is intentionally ignored by `.gitignore`.

## Required Files

The current notebook expects these files:

```text
occ.csv
wifi.csv
site_weather.csv
zone_temp_interior.csv
ele.csv
zone_co2.csv
```

The main target labels are derived from `occ.csv`. The default safe shiftable-load opportunity estimate uses `hvac_S` and `lig_S` from `ele.csv`.

## Expected Folder Structure

```text
decision-aware-occupancy-forecasting/
  doi_10_7941_D1N33Q__v20220202/
    Building_59/
      Bldg59_clean data/
        occ.csv
        wifi.csv
        site_weather.csv
        zone_temp_interior.csv
        ele.csv
        zone_co2.csv
  LBNL_occupancy_forecasting_main.ipynb
  src/
  scripts/
```

## Download Helper

Run:

```bash
python scripts/download_data.py
```

The helper currently prints manual download and placement instructions. It does not automate Dryad download or verify checksums yet.

