# Data and Provenance

## Dataset used by the repository

- Dataset: LBNL Building 59 Office Building Dataset
- Dryad DOI: [10.7941/D1N33Q](https://doi.org/10.7941/D1N33Q)
- Pipeline source directory name: 'Bldg59_clean data'

The repository uses selected south-zone occupancy, Wi-Fi, weather, temperature, electrical, and CO2 streams from the **cleaned** release. It does not commit the external package.

## Provenance boundary

The cleaned release is not equivalent to original acquisition data. The source cleaning workflow may contain interpolation and other imputation. The repository cannot reconstruct original observation-end times, source-timezone semantics, per-value imputation lineage, or whether an imported value was prospective at a claimed decision instant.

The committed downstream processing uses left-labelled 15-min bins. A label 't' represents '[t,t+15 min)' and is treated as usable only at 't+15 min'. Post-import forward filling is row-order-only and does not repair upstream provenance.

## Expected external layout

    doi_10_7941_D1N33Q__v20220202/
      Building_59/
        Bldg59_clean data/
          occ.csv
          wifi.csv
          site_weather.csv
          zone_temp_interior.csv
          ele.csv
          zone_co2.csv

This directory is intentionally ignored. The helper 'python3 scripts/download_data.py' gives placement instructions but does not download, validate checksums, or establish empirical provenance.

## Committed derived artifacts

- 'results/processed_lbnl_15min_pacific.csv'
- 'results/forecast_predictions_validation_all_models.csv'
- 'results/forecast_predictions_test_all_models.csv'

These are sufficient for downstream saved-output reproduction, including opportunity accounting. They are not substitutes for a raw/provenance-correct retraining or independent data validation.
