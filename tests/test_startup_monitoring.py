import copy
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tonepage.config import defaults, validate, save_config, load_config
from tonepage.gui import Application
from tonepage.settings_import import prepare_import


def test_default_and_import_preserve_receiver_preference(tmp_path):
    config=defaults();assert not config['ui']['start_monitoring']
    config['ui'].pop('start_monitoring');save_config(tmp_path,config)
    assert not load_config(tmp_path)['ui']['start_monitoring']
    current=defaults();current['ui']['start_monitoring']=True
    incoming,_=prepare_import(tmp_path/'config.json',current)
    assert incoming['ui']['start_monitoring'] is True
    config['ui']['start_monitoring']='yes'
    with pytest.raises(ValueError):validate(config)


def app_stub(enabled):
    app=SimpleNamespace(config={'ui':{'start_monitoring':enabled}},startup_timer=None,
        root=SimpleNamespace(after_idle=Mock(return_value='timer')),
        engine=SimpleNamespace(running=False,replay_safe=False,start=Mock()),safe=lambda fn:fn())
    app.startup_monitor=lambda:Application.startup_monitor(app)
    return app


def test_schedule_once_and_never_toggle_running_receiver():
    app=app_stub(False);Application.schedule_startup_monitoring(app)
    app.root.after_idle.assert_not_called()
    app.config['ui']['start_monitoring']=True
    Application.schedule_startup_monitoring(app);Application.schedule_startup_monitoring(app)
    assert app.root.after_idle.call_count==1
    app.engine.running=True;app.startup_monitor();app.engine.start.assert_not_called()
    app.engine.running=False;app.engine.replay_safe=True;app.startup_monitor();app.engine.start.assert_not_called()
    app.engine.replay_safe=False;app.startup_monitor();app.engine.start.assert_called_once()


def test_save_does_not_start_and_updates_pending_settings(tmp_path):
    import threading
    config=defaults();engine=SimpleNamespace(config=copy.deepcopy(config),delivery_config=copy.deepcopy(config),pending_settings=copy.deepcopy(config),settings_lock=threading.RLock(),start=Mock())
    var=SimpleNamespace(get=lambda:True,set=Mock())
    app=SimpleNamespace(config=config,home=tmp_path,engine=engine,startup_monitoring=var)
    Application.save_startup_monitoring(app)
    assert load_config(tmp_path)['ui']['start_monitoring']
    assert engine.pending_settings['ui']['start_monitoring']
    assert engine.config['ui']['start_monitoring']
    engine.start.assert_not_called()


def test_failed_save_restores_checkbox(tmp_path,monkeypatch):
    app=SimpleNamespace(config=defaults(),home=tmp_path,startup_monitoring=SimpleNamespace(get=lambda:True,set=Mock()))
    def fail(*args):raise OSError('Disk full')
    monkeypatch.setattr('tonepage.gui.save_config',fail)
    with pytest.raises(OSError):Application.save_startup_monitoring(app)
    assert not app.config['ui']['start_monitoring']
    app.startup_monitoring.set.assert_called_once_with(False)
