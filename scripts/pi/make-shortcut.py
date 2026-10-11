"""Install a menu launcher for this extracted package; no receiver actions."""
import os
from pathlib import Path

base = Path(__file__).resolve().parent

def desktop_value(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')

def exec_quote(value):
    value = str(value).replace('%', '%%')
    for char in ('\\', '"', '`', '$'):
        value = value.replace(char, '\\' + char)
    return desktop_value('"' + value + '"')

target = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
target.mkdir(parents=True, exist_ok=True)
entry = '\n'.join([
    '[Desktop Entry]', 'Type=Application', 'Name=Tone Sentry (Pi test)',
    'Comment=Radio paging monitor and tone discovery',
    'Exec=/bin/bash ' + exec_quote(base / 'launch.sh'),
    'Icon=' + desktop_value(base / 'app/tonepage/resources/app-icon.png'),
    'Terminal=false', 'Categories=AudioVideo;Audio;', '',
])
(target / 'tone-sentry-pi-test.desktop').write_text(entry, encoding='utf-8')
print('Installed application-menu shortcut. Keep the extracted package in this location.')
