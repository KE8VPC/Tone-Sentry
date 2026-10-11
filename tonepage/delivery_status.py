"""Operator-facing delivery status without exposing destination credentials."""
import json


def related_upload(store,row):
    payload=json.loads(row['payload'])
    destination=payload.get('destination',{})
    if row['kind']!='webhook' or not destination.get('wait_for_ftp'):return None
    event=payload.get('event',{})
    key=f"action:{event.get('id','')}:{destination['wait_for_ftp']}"
    matches=store.rows('SELECT * FROM jobs WHERE id=?',(key,))
    return matches[0] if matches and matches[0]['kind'] in ('ftp','ftps') else None


def display_status(store,row):
    state=row['status']
    if state=='done':return 'Completed'
    if state=='cancelled':return 'Cancelled'
    if state=='running':return 'Uploading' if row['kind'] in ('ftp','ftps') else 'In progress'
    if state=='ambiguous':return 'Outcome uncertain'
    payload=json.loads(row['payload'])
    if row['kind']=='webhook' and payload.get('destination',{}).get('wait_for_ftp'):
        upload=related_upload(store,row)
        if upload is None:return 'Upload not queued'
        if upload['status']=='failed':return 'Upload failed'
        if upload['status']=='cancelled':return 'Upload cancelled'
        if upload['status']!='done':return 'Waiting for FTP'
        if state=='pending':return 'Ready to send'
        if state=='failed' and (row['error'] or '').startswith('Required FTP upload'):
            return 'Ready to retry'
    if state=='failed':return 'Upload failed' if row['kind'] in ('ftp','ftps') else 'Failed — review result'
    return 'Retry scheduled' if row['attempts'] else 'Queued'
