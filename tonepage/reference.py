"""Offline CE45 tone reference. Frequencies are reference data, not agency assignments."""
import json
from importlib.resources import files


def catalog():
    return json.loads(files("tonepage").joinpath("resources/tone-reference.json").read_text(encoding="utf-8"))


def entries(group=None, query="", selectable_only=False):
    query = query.strip().casefold()
    return [e for e in catalog()["entries"]
            if (not group or e["group"] == group)
            and (not selectable_only or e["selectable"])
            and (not query or query in f"{e['group']} {e['number']} {e['code']} {e['hz']:g}".casefold())]


def frequency_for_code(code):
    entry = next((e for e in catalog()["entries"] if e["code"] == int(code)), None)
    if entry is None or not entry["selectable"]:
        raise ValueError("This chart code is undefined or has no usable frequency")
    return entry["hz"]

