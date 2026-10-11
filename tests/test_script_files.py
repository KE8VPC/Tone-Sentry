import os
import subprocess
import pytest
from tonepage.script_files import script_command
from tonepage.config import defaults,validate
from tonepage.integrations import JobWorker
from tonepage.store import Store


@pytest.mark.skipif(os.name!='nt',reason='Windows batch execution')
def test_batch_with_spaces_filename_and_exit_status(tmp_path):
    folder=tmp_path/'script folder';folder.mkdir()
    script=folder/'page log.bat'
    script.write_text('@echo off\n> "%~dp0receipt.txt" echo "%~1"\nexit /b 0\n')
    config=defaults();worker=JobWorker(Store(tmp_path),config)
    payload=dict(destination=dict(script_file=str(script),timeout=5),event=dict(type='recording_complete',filename='Test & More_123abc.mp3'))
    worker.execute(dict(id='local-test',kind='script',payload=payload))
    assert (folder/'receipt.txt').read_text().strip()=='"Test & More_123abc.mp3"'
    script.write_text('@exit /b 9\n')
    with pytest.raises(RuntimeError,match='Script failed'):
        worker.execute(dict(id='local-test',kind='script',payload=payload))


@pytest.mark.skipif(os.name!='nt',reason='Windows quoting constraints')
@pytest.mark.parametrize('name',['bad%PATH%.mp3','bad".mp3','bad!.mp3','bad\n.mp3'])
def test_batch_rejects_expansion_characters(tmp_path,name):
    path=tmp_path/'safe.bat';path.write_text('@exit /b 0')
    with pytest.raises(ValueError):script_command(path,name)


def test_missing_file_and_config_validation(tmp_path):
    with pytest.raises(ValueError,match='not found'):script_command(tmp_path/'missing.bat','file.mp3')
    c=defaults();c['integrations']=[dict(id='script',kind='script',script_file=str(tmp_path/'future.bat'))]
    validate(c) # An import on another machine must be possible before locating its file.
    c['integrations'][0].pop('script_file')
    with pytest.raises(ValueError):validate(c)


@pytest.mark.skipif(os.name=='nt',reason='Unix executable script')
def test_unix_shebang_and_spaces(tmp_path):
    script=tmp_path/'page log.sh'
    script.write_text('#!/bin/sh\nprintf "%s" "$1" > receipt.txt\n')
    with pytest.raises(ValueError,match='permission'):script_command(script,'page.mp3')
    script.chmod(0o700)
    argv,cwd=script_command(script,'page with spaces.mp3')
    subprocess.run(argv,cwd=cwd,check=True,timeout=5)
    assert (tmp_path/'receipt.txt').read_text()=='page with spaces.mp3'
