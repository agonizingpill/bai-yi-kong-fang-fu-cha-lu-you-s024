from sqlalchemy import select

from core.db import transaction
from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.vacant_rooms_model import vacant_rooms
from domain.visit_windows_model import visit_windows
from domain.method_trials_model import method_settings, method_trials, method_trial_entries

METHOD_CURRENT = '滞后回归'
METHOD_TRIAL = '上次实见'
SETTINGS_CODE = 'GLOBAL'
MIN_OBSERVATIONS = 12
MIN_SCORED_DAYS = 5


def ensure_method_settings():
    with transaction() as conn:
        row = conn.execute(select(method_settings.c.code)
            .where(method_settings.c.code == SETTINGS_CODE)).first()
        if row is None:
            conn.execute(method_settings.insert().values(
                code=SETTINGS_CODE, active_method=METHOD_CURRENT, enabled_batch=None))


def active_method(conn):
    row = conn.execute(select(method_settings)
        .where(method_settings.c.code == SETTINGS_CODE)).mappings().first()
    return row['active_method'] if row else METHOD_CURRENT


def open_trial(conn, user, data):
    from domain.visit_rules import calendar_day
    seen = set()
    pairs = []
    for item in data.pairs:
        day = calendar_day(item.target_day)
        room = get(conn, vacant_rooms, item.room_code)
        need((room['code'], day) not in seen, '同一房日在试用批内重复')
        seen.add((room['code'], day))
        windows = [row for row in scan(conn, visit_windows)
            if row['room_code'] == room['code'] and row['visit_day'] <= day]
        need(not any(row['visit_day'] == day and row['status'] == '已观测' for row in windows),
            '该复访日已登记实见，无法作为试用房日')
        history = [row for row in windows if row['visit_day'] < day]
        observations = [row for row in history if row['status'] == '已观测']
        need(len(observations) >= MIN_OBSERVATIONS, '同房间前序实见少于 12 次，试用估计尚不可用')
        pairs.append({'room_code': room['code'], 'target_day': day,
            'observations': observations, 'skipped_refusals': len(history) - len(observations)})
    return submit(user, {'kind': 'trial', 'pairs': pairs})


def lock_trial(conn, user, data):
    run = result(user, data.token)
    inputs, metrics = run['input'], run['result']
    need(inputs.get('kind') == 'trial', '该计算任务不是试用批估计')
    estimates = {(row['room_code'], row['target_day']): row for row in metrics['entries']}
    for pair in inputs['pairs']:
        live = [row for row in scan(conn, visit_windows)
            if row['room_code'] == pair['room_code'] and row['visit_day'] <= pair['target_day']]
        need(not any(row['visit_day'] == pair['target_day'] and row['status'] == '已观测' for row in live),
            '复访日已登记实见，请重新开批')
        history = [row for row in live if row['visit_day'] < pair['target_day']]
        observed = [row for row in history if row['status'] == '已观测']
        need(observed == pair['observations'] and len(history) - len(observed) == pair['skipped_refusals'],
            '新观察或拒入改变历史，请重新开批')
    insert(conn, method_trials, code=data.code, token=data.token,
        status='试用中', scored_days=0, current_mae=None, trial_mae=None)
    for pair in inputs['pairs']:
        estimate = estimates[(pair['room_code'], pair['target_day'])]
        insert(conn, method_trial_entries,
            code=f"{data.code}:{pair['room_code']}:{pair['target_day']}",
            batch_code=data.code, room_code=pair['room_code'], target_day=pair['target_day'],
            current_estimate=estimate['current_estimate'], trial_estimate=estimate['trial_estimate'],
            actual_count=None, current_error=None, trial_error=None)
    return get(conn, method_trials, data.code)


def score_recorded(conn, room_code, day, actual_count):
    trialing = {row['code'] for row in scan(conn, method_trials) if row['status'] == '试用中'}
    affected = set()
    for entry in scan(conn, method_trial_entries):
        if entry['batch_code'] in trialing and entry['room_code'] == room_code \
                and entry['target_day'] == day and entry['actual_count'] is None:
            update(conn, method_trial_entries, entry['code'],
                actual_count=actual_count,
                current_error=round(abs(entry['current_estimate'] - actual_count), 6),
                trial_error=round(abs(entry['trial_estimate'] - actual_count), 6))
            affected.add(entry['batch_code'])
    for batch_code in affected:
        refresh_batch(conn, batch_code)


def refresh_batch(conn, batch_code):
    entries = [row for row in scan(conn, method_trial_entries) if row['batch_code'] == batch_code]
    scored = [row for row in entries if row['actual_count'] is not None]
    current_mae = trial_mae = None
    if scored:
        current_mae = round(sum(row['current_error'] for row in scored) / len(scored), 6)
        trial_mae = round(sum(row['trial_error'] for row in scored) / len(scored), 6)
    update(conn, method_trials, batch_code,
        scored_days=len(scored), current_mae=current_mae, trial_mae=trial_mae)


def enable_trial(conn, user, data):
    batch = get(conn, method_trials, data.code, lock=True)
    need(batch['status'] != '已落选', '该试用批已仅保留对比结果，重试也不能启用')
    need(batch['status'] != '已启用', '该试用批已启用，无需重复提交')
    need(batch['scored_days'] >= MIN_SCORED_DAYS, '已评分房日未满五个，暂不能启用')
    need(batch['trial_mae'] is not None and batch['trial_mae'] < batch['current_mae'],
        '试用法平均绝对误差需小于现行法才可启用')
    settings = conn.execute(select(method_settings)
        .where(method_settings.c.code == SETTINGS_CODE)
        .with_for_update()).mappings().first()
    need(settings is not None, '用法设置尚未初始化')
    if settings['enabled_batch'] is not None:
        update(conn, method_trials, data.code, status='已落选')
        return {'code': data.code, 'rejected': '已有其他试用批先行启用，本批仅保留对比结果'}
    update(conn, method_trials, data.code, status='已启用')
    conn.execute(method_settings.update().where(method_settings.c.code == SETTINGS_CODE)
        .values(active_method=METHOD_TRIAL, enabled_batch=data.code))
    return get(conn, method_trials, data.code)
