# Methods and validation

## Automated checks

The test suite currently contains **8 tests**. It covers invalid rows, missing schemas, zero-trip calendar exposure, normalized profile totals, paired-date resampling, missing categories, report safety and source/report consistency.

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
```

Tests use small synthetic fixtures to isolate failure cases. They are not performance benchmarks. The checked-in report is generated from the historical project data and records its own input hashes, code hashes and exact dependency versions in `docs/metrics.json`. A consistency test rejects a report whose recorded implementation hashes differ from the current source.

## Report checks

All comparison selectors, numerical tables and CSV downloads are checked in a browser at desktop and mobile widths. Reports use self-contained HTML, SVG and embedded aggregate JSON. The chart scrolls inside its own region on narrow screens. No external scripts or raw restricted datasets are loaded.

## Evaluation scope

The daily contrast is the mean of customer daily medians minus the mean of subscriber daily medians. It is different from the pooled trip-median difference. Day resampling preserves within-day grouping but does not remove serial dependence. One month of trips does not identify unique customers or prove that membership causes longer or shorter rides.

## Reproduction boundaries

The current execution record uses Python 3.14.3 and the dependency versions saved alongside the results. Automated repository checks also target Python 3.11 and 3.12. Floating-point values and model outputs may vary by library/runtime version. External source files can change; compare input fingerprints before interpreting a difference as an implementation regression.
