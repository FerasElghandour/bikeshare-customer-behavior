# Ford GoBike: Trip Duration and Riding Patterns

Explore trip duration and departure timing in February 2019 San Francisco Bay Area bike-share records, then present four focused explanatory charts.

## Completion

Udacity project: **Communicate Data Findings**. Passed on **2026-10-11**, verified against the authenticated Udacity project-pass email. The receipt is kept privately.

This is a cleaned portfolio edition of the recovered implementation associated with that project. Udacity's email confirms the project passed; it does not certify this Git commit or identify the accepted archive by hash.

## Approach

Convert timestamps and duration units, derive weekday/weekend groups and station endpoint separation, compare subgroup medians, and normalize hourly profiles within each user/day-type group. Both notebooks retain all source rows for summaries.

## Recorded results

The saved analysis contains 183,412 trips. Subscribers account for 89.17% of trips. Customer median duration is 13.20 minutes, compared with 8.17 for subscribers. Customer medians rise from 12.40 minutes on weekdays to 16.05 on weekends.

These figures come from saved execution records. Release validation is described in `VALIDATION.md`.

## Run

Release execution checks used Python 3.14.3; analysis dependency versions are pinned in `requirements.txt`.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

After supplying the CSV, open and run `Part_I_exploration.ipynb`, then `Part_II_explanatory.ipynb`, from the repository root.

See [DATA.md](DATA.md) for inputs, attribution and excluded materials. Notebook outputs are cleared in this edition to exclude raw-data previews and machine-specific output.

## Limitations

One month and one system; rows represent trips rather than unique riders. Endpoint separation is not actual route length. Demographics are not used. These observations do not establish why groups differ or predict other seasons.

## Provenance and rights

Prepared by Mohamed Feras Elghandour with AI assistance in implementation, debugging, analysis and documentation. This repository does not claim unaided coding or production deployment. Udacity supplied the educational context; third-party tools and inputs retain their own rights. Course lesson text, assessment prompts, rubrics, answer keys, pass-email bodies and authenticated classroom captures are excluded.

No new repository-wide software license is granted in this release. Existing third-party license notices remain applicable; see [DATA.md](DATA.md) and any `third_party/` or `vendor/` notices. This is an educational portfolio project, without a claim of Udacity endorsement.
