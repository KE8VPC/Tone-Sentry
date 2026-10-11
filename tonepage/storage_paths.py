"""New local audio layout, with continued access to legacy managed recordings."""
from pathlib import Path


def audio_root(home):
    path = Path(home)/'audio'
    path.mkdir(parents=True, exist_ok=True)
    return path


def managed_audio(home, path):
    resolved = Path(path).resolve()
    return any(resolved.is_relative_to((Path(home)/name).resolve()) for name in ('audio','recordings'))
