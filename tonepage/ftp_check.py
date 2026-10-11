"""Read-only FTP destination validation; never uploads or creates directories."""
import ftplib
import ssl
from pathlib import PurePosixPath
from .ftp_credentials import ftp_password


def check_destination(destination):
    stage='settings'
    try:
        kind=destination.get('kind')
        if kind not in ('ftp','ftps'):raise ValueError()
        host=str(destination.get('host','')).strip()
        directory=str(destination.get('directory','/')) or '/'
        username=str(destination.get('username','anonymous'))
        port=int(destination.get('port',21))
        if not host or not 1<=port<=65535 or '..' in PurePosixPath(directory).parts:
            raise ValueError()
        if any('\r' in v or '\n' in v or '\x00' in v for v in (host,directory,username)):
            raise ValueError()
        stage='credentials'
        password=ftp_password(destination)
        client=ftplib.FTP_TLS(context=ssl.create_default_context()) if kind=='ftps' else ftplib.FTP()
        with client:
            stage='connection'
            client.connect(host,port,timeout=15)
            stage='login'
            client.login(username,password)
            if kind=='ftps':
                stage='TLS protection'
                client.prot_p()
            stage='directory access'
            client.cwd(directory)
            client.pwd()
        return True,'Success: login and directory access verified. No files were created. Upload permission was not tested.'
    except Exception:
        messages={'settings':'Check the host, port and remote directory.',
                  'credentials':'Enter the FTP password again, or check the legacy password environment variable if using one.',
                  'connection':'Check the host, port, network and FTP/FTPS selection; for FTPS also check the server certificate.',
                  'login':'Check the FTP username and password; the server rejected or interrupted login.',
                  'TLS protection':'The server could not enable protected FTPS transfers.',
                  'directory access':'Login succeeded, but the configured directory could not be accessed. Check that it exists and that the account can enter it.'}
        # Server replies can contain credentials or other private information.
        return False,'Test failed at '+stage+'. '+messages[stage]
