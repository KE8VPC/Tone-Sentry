"""Advisory overlap context. Never changes recording eligibility or tone identity."""
import json


def context(store, data):
    if not data.get('discovery_only'):
        return data
    result = dict(data)
    start, end = data['start'], data.get('end', data['start'])
    links = {}
    # Known sequences are bounded by two 60-second tones and a five-second gap.
    rows = store.rows("SELECT data FROM events WHERE type='detection' AND at>=? AND at<? ORDER BY at", (start-125, end))
    for row in rows:
        event = json.loads(row['data'])
        if event.get('end', event['at']) <= start:
            continue
        if event.get('instance_id') != data.get('instance_id') or bool(event.get('synthetic')) != bool(data.get('synthetic')):
            continue
        links[event['id']] = {key: event.get(key) for key in
            ('id', 'at', 'end', 'tone_ids', 'agencies', 'recording_id', 'duplicate', 'test')}
    result['known_page_overlaps'] = list(links.values())
    result['discovery_note'] = ('Confirmed pages overlap this discovery clip. Other tones may remain unidentified; review the full sequence.'
                              if links else 'Discovery capture; no overlapping confirmed page found. This is not a confirmed agency identity.')
    return result


def label(data):
    if not data.get('discovery_only'):
        return ', '.join(data.get('agencies', []))
    agencies = sorted({name for event in data.get('known_page_overlaps', []) for name in event.get('agencies', [])})
    return 'Discovery clip — overlaps ' + ', '.join(agencies) if agencies else 'Discovery clip — unconfirmed'
