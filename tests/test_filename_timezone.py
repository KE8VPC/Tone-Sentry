import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pytest
from tonepage.config import defaults, load_config, validate
from tonepage.recording_names import filename_clock
from tonepage.settings_import import prepare_import
from tonepage.engine import Engine


def test_new_and_legacy_filename_zones(tmp_path):
    assert load_config(tmp_path)['recording']['filename_timezone']=='Local time'
    old=defaults();old['recording'].pop('filename_timezone')
    path=tmp_path/'config.json';path.write_text(json.dumps(old))
    assert load_config(tmp_path)['recording']['filename_timezone']=='UTC'
    incoming,_=prepare_import(path,defaults())
    assert incoming['recording']['filename_timezone']=='UTC'
    old['recording']['filename_timezone']='bad'
    with pytest.raises(ValueError):validate(old)


@pytest.mark.parametrize('stamp',[1791048040.3864865,1793511000,1793514600,1791073800])
def test_filename_clock_uses_recording_date_and_os_offset(stamp):
    utc=datetime.fromtimestamp(stamp,timezone.utc)
    assert filename_clock(stamp,'UTC')==dict(date=utc.strftime('%Y-%m-%d'),time=utc.strftime('%H-%M-%S'),offset='UTC')
    local=utc.astimezone()
    assert filename_clock(stamp,'Local time')==dict(date=local.strftime('%Y-%m-%d'),time=local.strftime('%H-%M-%S'),offset=local.strftime('%z'))


@pytest.mark.parametrize('mode',['Local time','UTC',None])
def test_queued_encode_retains_timezone_and_epoch(tmp_path,mode):
    config=defaults();config['recording']['filename']='{date}_{time}_{offset}'
    config['recording']['filename_timezone']=mode or 'UTC'
    e=Engine(tmp_path,config)
    try:
        stamp=1791048040.3864865
        e.begin_recording(stamp)
        e.active['writer'].writeframes(np.zeros(1600,dtype='<i2').tobytes())
        e.active['data'].update(samples=1600,end=stamp+.1,synthetic=True)
        e.finish_recording()
        payload=json.loads(e.store.rows("SELECT payload FROM jobs WHERE kind='encode'")[0]['payload'])
        if mode is None:payload['data'].pop('encoding_settings')
        e.config['recording']['filename_timezone']='UTC' if mode=='Local time' else 'Local time'
        e.encode(payload)
        row=e.store.recent('recordings')[0]
        expected=filename_clock(stamp,mode or 'UTC')
        assert Path(row['path']).name.startswith('{date}_{time}_{offset}_'.format_map(expected))
        data=json.loads(row['data'])
        assert data['start']==stamp and data['end']==stamp+.1
    finally:e.close();e.store.close()
