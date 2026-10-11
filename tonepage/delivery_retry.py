"""Explicit retry with current destination settings, preserving job identity."""
import copy
import json
from .integrations import destinations


def refreshed_payload(job,config):
    if job['status'] in ('running','done'):
        raise ValueError('Active or completed deliveries cannot be retried')
    payload=json.loads(job['payload']) if isinstance(job['payload'],str) else copy.deepcopy(job['payload'])
    old=payload.get('destination',{})
    current=next((d for d in config['integrations'] if d['id']==old.get('id')),None)
    if current is None:raise ValueError('This destination was removed; recreate it before retrying')
    if current['kind']!=job['kind']:raise ValueError('Destination type changed; this delivery cannot use it')
    event=payload['event']
    if current['id'] not in {d['id'] for d in destinations(config,event,payload.get('action_scope'))}:
        raise ValueError('The destination is disabled or no longer matches this event, tone filter or delivery scope')
    if current.get('scope','shared')!=old.get('scope','shared'):
        raise ValueError('Destination scope changed; keep the original scope to retry this delivery')
    if (job['kind'] in ('ftp','ftps','email','transcription') or current.get('include_transcript')) and not event.get('allow_cloud',False):
        raise ValueError('This recording does not allow audio/transcript sharing')
    destination=copy.deepcopy(current)
    if job['kind']=='email':
        recipients=old.get('recipients',[])
        if len(recipients)!=1 or recipients[0] not in current.get('recipients',[]):
            raise ValueError('The original email recipient is no longer configured')
        destination['recipients']=recipients
    payload['destination']=destination
    payload['protect']=destination.get('protect_recording',True)
    return payload


def retry_with_settings(store,job_id,config):
    with store.transaction() as db:
        row=db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row is None:raise ValueError('Delivery no longer exists')
        payload=refreshed_payload(dict(row),config)
        db.execute("UPDATE jobs SET payload=?,status='pending',due=0,attempts=0,error=NULL,claim=NULL WHERE id=?",
                   (json.dumps(payload),job_id))
