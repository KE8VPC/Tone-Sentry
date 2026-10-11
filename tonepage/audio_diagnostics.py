"""Read-only audio inventory; never opens or reinitializes an audio stream."""
import json
import platform


def input_inventory(sd):
    hosts = sd.query_hostapis()
    return [dict(index=i, name=d['name'], interface=hosts[d['hostapi']]['name'],
                 channels=int(d['max_input_channels']), default_sample_rate=float(d['default_samplerate']))
            for i, d in enumerate(sd.query_devices()) if d['max_input_channels']]


def input_choices(inventory):
    return {'System default': None, **{
        f"{d['index']}: {d['name']} — {d['interface']}": d['index'] for d in inventory}}


def report(sd, selected, channel, sample_rate, last_error=None):
    from . import __version__
    data = dict(application='Tone Sentry '+__version__, platform=platform.system(),
                selected_input=selected, channel=channel, sample_rate=sample_rate,
                last_audio_error=last_error)
    try:
        data['inputs'] = input_inventory(sd)
        data['system_default_input'] = int(sd.default.device[0])
        data['portaudio'] = str(sd.get_portaudio_version())
    except Exception as error:
        data['inventory_error'] = str(error)
    return json.dumps(data, indent=2, ensure_ascii=False)


def error_detail(error, settings):
    return dict(error_type=type(error).__name__, detail=str(error)[:2000],
                device=settings['device'], channel=settings['channel'],
                sample_rate=settings['sample_rate'])
