import numpy as np
import pandas as pd
import pytest
from analysis import prepare_trips, summarize, daily_bootstrap_gap


def fixture_trips():
    return pd.DataFrame([{'start_time': f'2019-02-{day:02} 08:00:00',
                          'end_time': f'2019-02-{day:02} 08:{minutes:02}:00',
                          'duration_sec': minutes*60, 'user_type': user}
                         for day in [1, 2, 3] for user, minutes in [('Subscriber', 5), ('Customer', 15)]])


def test_invalid_rows_are_counted_not_silently_mixed():
    raw = fixture_trips()
    raw.loc[0, 'duration_sec'] = -1
    raw.loc[1, 'start_time'] = 'invalid'
    data, audit = prepare_trips(raw)
    assert audit['excluded_invalid_rows'] == 2
    assert len(data) == 4


def test_missing_schema_fails_with_useful_error():
    with pytest.raises(ValueError, match='Missing required columns'):
        prepare_trips(pd.DataFrame({'start_time': ['2019-02-01']}))


def test_calendar_exposure_counts_zero_trip_dates():
    raw = fixture_trips()
    raw = raw[~raw.start_time.str.startswith('2019-02-02')]
    data, audit = prepare_trips(raw)
    result = summarize(data, audit)
    assert result['calendar_days'] == {'Weekend': 2, 'Weekday': 1}
    customer_weekend = next(r for r in result['segments'] if r['user_type']=='Customer' and r['day_type']=='Weekend')
    assert customer_weekend['trips_per_calendar_day'] == .5


def test_hour_profiles_are_normalized_within_group():
    data, audit = prepare_trips(fixture_trips())
    result = summarize(data, audit)
    hourly = pd.DataFrame(result['hourly'])
    assert np.allclose(hourly.groupby(['user_type','day_type']).share_percent.sum(), 100)


def test_bootstrap_resamples_paired_days_and_defines_estimand():
    data, _ = prepare_trips(fixture_trips())
    result = daily_bootstrap_gap(data, draws=100)
    assert result['estimate_minutes'] == 10
    assert result['ci95_minutes'] == [10, 10]
    assert result['paired_days'] == 3


def test_bootstrap_missing_category_is_explicit():
    data, _ = prepare_trips(fixture_trips().query('user_type == "Subscriber"'))
    assert daily_bootstrap_gap(data)['available'] is False
