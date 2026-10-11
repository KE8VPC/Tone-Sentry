"""Shared notification placeholders; filename is a basename, never a local path."""
import string
import time
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import quote

FIELDS={'agency','agencies','date','time','site','event_id','recording_id','event_type','transcript','filename','filename_url'}


def filename_for(event):
    if event.get('type') not in ('recording_complete','transcript_complete'):return ''
    raw=str(event.get('path') or event.get('filename') or '')
    name=PurePosixPath(raw.replace('\\','/')).name
    return name if name.lower().endswith('.mp3') and not any(c in name for c in '\r\n\0') else ''


def validate_template(template,allow_empty=False,maximum=10000):
    if not isinstance(template,str) or len(template)>maximum or not allow_empty and not template.strip():
        raise ValueError('Message template is empty or too long')
    for _,field,spec,conversion in string.Formatter().parse(template):
        if field is not None and (field not in FIELDS or spec or conversion):
            raise ValueError('Unsupported message placeholder: '+str(field))
    return template


def values_for(event,include_transcript=False):
    local=datetime.fromtimestamp(event.get('at',event.get('start',time.time())))
    agency=', '.join(str(a) for a in event.get('agencies',[])) or 'Unknown agency'
    return dict(agency=agency,agencies=agency,date=local.strftime('%Y-%m-%d'),time=local.strftime('%I:%M %p').lstrip('0'),
                site=str(event.get('site','')),event_id=str(event.get('id','')),recording_id=str(event.get('recording_id','')),
                event_type=str(event.get('type','')),transcript=str(event.get('text','')) if include_transcript else '',
                filename=filename_for(event),filename_url=quote(filename_for(event),safe=''))


def render(template,event,include_transcript=False):
    return validate_template(template).format_map(values_for(event,include_transcript))
