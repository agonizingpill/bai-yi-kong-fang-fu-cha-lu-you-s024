from fastapi import APIRouter, Depends, HTTPException

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import method_trials_service as service
from domain.method_trials_model import method_trials, method_trial_entries
from domain.method_trials_schemas import EnableTrial, LockTrial, OpenTrial

router = APIRouter()

@router.get('/method_trials')
def list_method_trials(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, method_trials)


@router.get('/method_trial_entries')
def list_method_trial_entries(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, method_trial_entries)


@router.post('/method_trials/open-trial')
def open_trial(data: OpenTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.open_trial(conn, user, data)
        record(conn, user, 'method_trials.open_trial')
        return output


@router.post('/method_trials/lock-trial')
def lock_trial(data: LockTrial, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.lock_trial(conn, user, data)
        record(conn, user, 'method_trials.lock_trial')
        return output


@router.post('/method_trials/enable-trial')
def enable_trial(data: EnableTrial, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.enable_trial(conn, user, data)
        record(conn, user, 'method_trials.enable_trial')
    if 'rejected' in output:
        raise HTTPException(409, detail=output['rejected'])
    return output
