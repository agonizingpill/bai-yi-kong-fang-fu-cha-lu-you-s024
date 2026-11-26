from datetime import date
from math import expm1, log1p

import numpy as np
from sklearn.linear_model import LinearRegression

METHOD_CURRENT = '滞后回归'
METHOD_TRIAL = '上次实见'


def gap(newer,older):
    return (date.fromisoformat(newer)-date.fromisoformat(older)).days


def features(previous_count,gap_days):
    return [log1p(previous_count),log1p(gap_days)]


def ordered(observations):
    return sorted(observations,key=lambda row: (row['visit_day'],row['code']))


def regression_predict(observations,target_day):
    rows = [
        (features(past['activity_count'],gap(current['visit_day'],past['visit_day'])),
            log1p(current['activity_count']))
        for past,current in zip(observations,observations[1:])
    ]
    model = LinearRegression().fit([x for x,_ in rows],[y for _,y in rows])
    newest = observations[-1]
    estimate = expm1(float(np.clip(model.predict(
        [features(newest['activity_count'],gap(target_day,newest['visit_day']))])[0],0,9)))
    return max(0.,estimate)


def calculate(data):
    observations = ordered(data['observations'])
    rows = [
        (features(past['activity_count'],gap(current['visit_day'],past['visit_day'])),
            log1p(current['activity_count']))
        for past,current in zip(observations,observations[1:])
    ]
    hold = max(3,len(rows)//5)
    newest = observations[-1]
    lag_count = newest['activity_count']
    gap_days = gap(data['target_day'],newest['visit_day'])
    base = {'gap_days':gap_days,'lag_count':lag_count,
        'skipped_refusals':data['skipped_refusals'],
        'observed_zeroes':sum(row['activity_count']==0 for row in observations),
        'validation_from':observations[-hold]['visit_day'],'holdout_rows':hold}
    if data.get('method') == METHOD_TRIAL:
        tail = list(zip(observations,observations[1:]))[-hold:]
        mae = float(np.mean([abs(current['activity_count']-past['activity_count'])
            for past,current in tail]))
        return base | {'method':METHOD_TRIAL,'prediction':float(lag_count),
            'holdout_mae':round(mae,6)}
    train = rows[:-hold]
    model = LinearRegression().fit([x for x,_ in train],[y for _,y in train])
    validation_x = [x for x,_ in rows[-hold:]]
    actual = np.expm1([y for _,y in rows[-hold:]])
    estimates = np.maximum(0,np.expm1(np.clip(model.predict(validation_x),0,9)))
    mae = float(np.mean(np.abs(actual-estimates)))
    model.fit([x for x,_ in rows],[y for _,y in rows])
    prediction = max(0.,expm1(float(np.clip(model.predict([features(lag_count,gap_days)])[0],0,9))))
    return base | {'method':METHOD_CURRENT,'prediction':round(prediction,5),
        'holdout_mae':round(mae,6),'training_rows':len(train),
        'coefficient_prev_count':round(float(model.coef_[0]),6),
        'coefficient_gap_days':round(float(model.coef_[1]),6)}


def calculate_trial(data):
    entries = []
    for pair in data['pairs']:
        observations = ordered(pair['observations'])
        entries.append({'room_code':pair['room_code'],'target_day':pair['target_day'],
            'current_estimate':round(regression_predict(observations,pair['target_day']),5),
            'trial_estimate':float(observations[-1]['activity_count'])})
    return {'entries':entries}
