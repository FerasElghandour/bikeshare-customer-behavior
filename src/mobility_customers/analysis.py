"""Validated trip analytics and aggregate-only report generation."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from .reporting import publish_report

REQUIRED = {'start_time', 'end_time', 'duration_sec', 'user_type'}


def prepare_trips(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    data = frame[list(REQUIRED)].copy()
    starts = pd.to_datetime(data.start_time, errors='coerce')
    ends = pd.to_datetime(data.end_time, errors='coerce')
    seconds = pd.to_numeric(data.duration_sec, errors='coerce')
    valid = (starts.notna() & ends.notna() & np.isfinite(seconds) & seconds.gt(0)
             & ends.ge(starts) & data.user_type.isin(['Subscriber', 'Customer']))
    # Exclusions are explicit; duplicates remain records because trip IDs are absent.
    audit = {'input_rows': len(data), 'valid_rows': int(valid.sum()),
             'excluded_invalid_rows': int((~valid).sum()),
             'duplicate_input_rows': int(frame.duplicated().sum())}
    data = data.loc[valid].copy()
    if data.empty:
        raise ValueError('No valid trips remain after timestamp, duration and user-type checks.')
    data['date'] = starts.loc[valid].dt.normalize()
    data['hour'] = starts.loc[valid].dt.hour
    data['duration_min'] = seconds.loc[valid] / 60
    data['day_type'] = np.where(data.date.dt.dayofweek < 5, 'Weekday', 'Weekend')
    data['elapsed_difference_sec'] = ((ends.loc[valid] - starts.loc[valid]).dt.total_seconds()
                                      - seconds.loc[valid])
    audit['elapsed_difference_max_abs_sec'] = float(data.elapsed_difference_sec.abs().max())
    return data, audit


def daily_bootstrap_gap(data: pd.DataFrame, draws=2000, seed=42) -> dict:
    """Resample days, preserving within-day clustering and category dependence.

    Estimate the difference between means of daily category medians. This is
    deliberately distinct from the pooled trip median difference.
    """
    daily = data.groupby(['date', 'user_type']).duration_min.median().unstack()
    if not {'Subscriber', 'Customer'} <= set(daily.columns):
        return {'available': False, 'reason': 'Both user categories are required.'}
    gaps = (daily.Customer - daily.Subscriber).dropna().to_numpy()
    if len(gaps) < 2:
        return {'available': False, 'reason': 'At least two paired dates are required.'}
    rng = np.random.default_rng(seed)
    estimates = rng.choice(gaps, size=(draws, len(gaps)), replace=True).mean(axis=1)
    low, high = np.quantile(estimates, [.025, .975])
    return {'available': True, 'paired_days': len(gaps), 'estimate_minutes': float(gaps.mean()),
            'ci95_minutes': [float(low), float(high)], 'draws': draws, 'seed': seed,
            'estimand': 'Mean daily customer median minus mean daily subscriber median',
            'scope': 'Day resampling does not remove serial dependence or identify unique riders.'}


def summarize(data: pd.DataFrame, audit: dict) -> dict:
    # Calendar exposure includes every date in the observed interval, even a zero-trip day.
    calendar = pd.DataFrame({'date': pd.date_range(data.date.min(), data.date.max(), freq='D')})
    calendar['day_type'] = np.where(calendar.date.dt.dayofweek < 5, 'Weekday', 'Weekend')
    exposure = calendar.day_type.value_counts().to_dict()
    groups = data.groupby(['user_type', 'day_type']).duration_min.agg(['size', 'median', 'mean']).reset_index()
    groups['trips_per_calendar_day'] = groups.apply(lambda r: r['size'] / exposure[r.day_type], axis=1)
    hourly = data.groupby(['user_type', 'day_type', 'hour']).size().rename('trips').reset_index()
    hourly['share_percent'] = hourly.trips / hourly.groupby(['user_type', 'day_type']).trips.transform('sum') * 100
    daily = data.groupby(['date', 'user_type']).agg(trips=('duration_min', 'size'), median_minutes=('duration_min', 'median')).reset_index()
    return {'audit': audit, 'calendar_days': exposure,
            'period': [str(data.date.min().date()), str(data.date.max().date())],
            'overall': data.groupby('user_type').duration_min.agg(['size', 'median']).reset_index().to_dict('records'),
            'segments': groups.to_dict('records'), 'hourly': hourly.to_dict('records'),
            'daily_gap': daily_bootstrap_gap(data),
            'daily': daily.assign(date=daily.date.dt.strftime('%Y-%m-%d')).to_dict('records')}


def report_spec(result):
    views = []
    for day in ['Weekday', 'Weekend']:
        rows = [r for r in result['segments'] if r['day_type'] == day]
        views.append({'label': f'{day}: median duration', 'kind': 'bar', 'unit': 'minutes',
                      'series': [{'name': 'Median trip duration', 'points': [{'x': r['user_type'], 'y': r['median']} for r in rows]}]})
        series = []
        for user in ['Subscriber', 'Customer']:
            rows = [r for r in result['hourly'] if r['day_type'] == day and r['user_type'] == user]
            values = {r['hour']: r['share_percent'] for r in rows}
            series.append({'name': user, 'points': [{'x': h, 'y': values.get(h, 0)} for h in range(24)]})
        views.append({'label': f'{day}: departure profile', 'kind': 'line', 'unit': '% of group trips', 'series': series})
    gap = result['daily_gap']
    finding = ('The day-cluster bootstrap estimates a daily median duration gap of '
               f'{gap["estimate_minutes"]:.2f} minutes (95% interval {gap["ci95_minutes"][0]:.2f} to {gap["ci95_minutes"][1]:.2f}).') if gap['available'] else gap['reason']
    return {'title': 'Bike-share customer behavior', 'subtitle': 'Separate customer patterns from the size of the subscriber base.',
            'category': 'Customer analytics / mobility', 'findings': [f'{result["audit"]["valid_rows"]:,} valid trips, with explicit quality checks.', finding,
             'Within-group timing profiles distinguish behavior from unequal group sizes.'], 'views': views,
            'methodology': [{'title': 'Calendar-aware comparison', 'body': 'Daily volumes use the full observed calendar interval, including any zero-trip dates. Duration comparisons retain all valid trips.'},
             {'title': 'Uncertainty with a defined estimand', 'body': '2,000 fixed-seed resamples of paired dates estimate the mean difference between daily category medians. This is not the pooled trip median difference.'},
             {'title': 'Decision boundary', 'body': 'Use the results to investigate station capacity and duration patterns. One month of observational trips does not prove user intent, a causal membership effect or unique-customer behavior.'}],
            'notes': 'Only aggregate summaries are embedded. Input trips and demographic fields are not published.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Historical trip CSV')
    parser.add_argument('--output', type=Path, default=Path('reports'))
    args = parser.parse_args()
    try:
        data, audit = prepare_trips(pd.read_csv(args.input))
        result = summarize(data, audit)
        publish_report(args.output, result, report_spec(result), [args.input])
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Analysis failed: {exc}\n')


if __name__ == '__main__':
    main()
