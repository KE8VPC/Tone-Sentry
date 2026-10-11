from urllib.parse import unquote
from tonepage.message_templates import values_for,render
from tonepage.integrations import webhook_payload


def test_filename_preserves_underscores_and_url_encodes_spaces():
    name='Cridersville EMS_2026-09-11 01-27-34_Beam_9f4e5c.mp3'
    event=dict(type='recording_complete',path='C:/audio/'+name)
    values=values_for(event)
    assert values['filename']==name
    assert unquote(values['filename_url'])==name
    assert ' ' not in values['filename_url'] and '_Beam_9f4e5c.mp3' in values['filename_url']
    template='[Listen](https://example.invalid/audio/{filename_url})'
    result=webhook_payload(dict(webhook_format='discord',discord_template=template),event)
    assert result['content']=='[Listen](https://example.invalid/audio/'+values['filename_url']+')'
    assert render('{filename}',event)==name


def test_filename_url_escapes_reserved_characters_without_double_encoding():
    name='EMS_#1+50%_ü.mp3'
    event=dict(type='recording_complete',filename=name)
    assert render('{filename_url}',event)=='EMS_%231%2B50%25_%C3%BC.mp3'
    assert render('{filename_url}',dict(type='activation',filename=name))==''
