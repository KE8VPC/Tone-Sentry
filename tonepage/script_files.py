"""Launch supported script files with completion tracking, not a document editor."""
import os
import subprocess
from pathlib import Path


def script_command(file,filename):
    path=Path(file).expanduser().resolve()
    if not path.is_file():raise ValueError('Script file was not found on this computer')
    if os.name=='nt':
        if path.suffix.lower() not in ('.bat','.cmd'):
            raise ValueError('Choose a Windows .bat or .cmd script')
        # cmd performs expansion even inside quotes. Reject expansion/control
        # characters rather than interpreting them from a recording filename.
        if any(c in str(path)+filename for c in '"%!\r\n\0'):
            raise ValueError('Script path and filename cannot contain quotes, percent signs, exclamation marks or line breaks')
        command=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'cmd.exe'
        return subprocess.list2cmdline([str(command)])+' /d /v:off /s /c ""'+str(path)+'" "'+filename+'""',path.parent
    if not os.access(path,os.X_OK):
        raise ValueError('Script must be executable on this computer; enable its execute permission')
    with path.open('rb') as source:
        if source.read(2)!=b'#!':raise ValueError('Script needs a #! interpreter declaration on its first line')
    return [str(path),filename],path.parent
