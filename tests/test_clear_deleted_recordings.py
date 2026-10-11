import pytest
from tonepage.store import Store


def test_clear_only_deleted_preserves_metadata_and_survives_restart(tmp_path):
    store=Store(tmp_path)
    for index,status in enumerate(('deleted','complete','capturing','encoding')):
        store.recording(status,index,index+1,status,tmp_path/(status+'.mp3'),{'recording_id':status})
    with pytest.raises(ValueError):store.clear_history('recordings',mode='all')
    assert store.clear_history('recordings',mode='deleted')==1
    assert store.clear_history('recordings',mode='deleted')==0
    assert {r['id'] for r in store.visible_history('recordings')}=={'complete','capturing','encoding'}
    assert len(store.recent('recordings'))==4
    store.close()
    store=Store(tmp_path)
    try:
        assert len(store.visible_history('recordings'))==3
        store.recording('later',9,10,'deleted',tmp_path/'later.mp3',{})
        assert store.visible_history('recordings')[0]['id']=='later'
        store.recording('deleted',0,1,'complete',tmp_path/'restored.mp3',{})
        assert 'deleted' in {r['id'] for r in store.visible_history('recordings')}
    finally:store.close()
