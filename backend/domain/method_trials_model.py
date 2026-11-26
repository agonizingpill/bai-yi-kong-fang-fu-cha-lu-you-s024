from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, Table, UniqueConstraint

from core.db import metadata


method_settings = Table('method_settings', metadata,
    Column('code', String(64), primary_key=True),
    Column('active_method', String(160), nullable=False),
    Column('enabled_batch', String(64), nullable=True),
    CheckConstraint("active_method IN ('滞后回归','上次实见')"),
)

method_trials = Table('method_trials', metadata,
    Column('code', String(64), primary_key=True),
    Column('status', String(160), nullable=False),
    Column('scored_days', Integer, nullable=False),
    Column('current_mae', Float, nullable=True),
    Column('trial_mae', Float, nullable=True),
    Column('token', String(64), nullable=False, unique=True),
    CheckConstraint("status IN ('试用中','已启用','已落选')"),
    CheckConstraint('scored_days >= 0'),
)

method_trial_entries = Table('method_trial_entries', metadata,
    Column('code', String(256), primary_key=True),
    Column('batch_code', String(64), ForeignKey('method_trials.code'), nullable=False),
    Column('room_code', String(160), ForeignKey('vacant_rooms.code'), nullable=False),
    Column('target_day', String(160), nullable=False),
    Column('current_estimate', Float, nullable=False),
    Column('trial_estimate', Float, nullable=False),
    Column('actual_count', Integer, nullable=True),
    Column('current_error', Float, nullable=True),
    Column('trial_error', Float, nullable=True),
    CheckConstraint('current_estimate >= 0'),
    CheckConstraint('trial_estimate >= 0'),
    UniqueConstraint('batch_code', 'room_code', 'target_day'),
)
