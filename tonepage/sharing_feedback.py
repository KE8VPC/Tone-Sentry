def blocked_agencies(config):
    """Configured tone/destination permission mismatches, not delivery failures."""
    result=[]
    for tone in config['tones']:
        if not tone.get('enabled', True) or tone.get('allow_cloud', False):
            continue
        for dest in config['integrations']:
            needs_sharing=dest['kind'] in ('ftp','ftps','email','transcription') or dest['kind']=='webhook' and dest.get('include_transcript',False)
            if dest.get('enabled') and needs_sharing and (not dest.get('tone_ids') or tone['id'] in dest['tone_ids']):
                result.append(tone)
                break
    return result
