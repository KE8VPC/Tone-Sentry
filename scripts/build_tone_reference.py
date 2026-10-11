"""Extract the supplied CE45 chart into checked package data (build-time pypdf only)."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from pypdf import PdfReader

parser = argparse.ArgumentParser()
parser.add_argument("pdf", type=Path)
args = parser.parse_args()
text = PdfReader(args.pdf).pages[0].extract_text()
blocks = text.split("Tone Freq.\n(Hz)\n")[1:]
frequencies = []
for block in blocks:
    frequencies.extend(float(x) for x in re.findall(r"^\d+\.\d+$", block.split("Group Name")[0], re.M))
assert len(frequencies) == 256, "Chart extraction must retain every code, including undefined entries"
ranges = [(0,9,"Motorola Quick Call 2 / Reed Group 1"), (10,19,"Motorola Quick Call 2 / Reed Group 2"),
          (20,29,"Motorola Quick Call 2 / Reed Group 3"), (30,31,"Not Defined"),
          (32,41,"Motorola Quick Call 2 / Reed Group 4"), (42,51,"Motorola Quick Call 2 / Reed Group 5"),
          (52,61,"Motorola Quick Call 2 / Reed Group 6"), (62,63,"Not Defined"),
          (64,73,"Motorola Quick Call 2 / Reed Group 10"), (74,83,"Motorola Quick Call 2 / Reed Group 11"),
          (84,93,"GE Type 99 / Table 1 / Group A"), (94,103,"GE Type 99 / Table 1 / Group B"),
          (104,114,"GE Type 99 / Table 1 / Group C"), (115,130,"AVCALL 2+2"),
          (131,189,"Plectron Format Tones"), (190,199,"Reach Two Tone / Group A"),
          (200,209,"Reach Two Tone / Group B"), (210,219,"Reach Two Tone / Group C"),
          (220,229,"Reach Two Tone / Group D"), (230,239,"Reach Two Tone / Group E"), (240,255,"Spear")]
entries = []
for code, hz in enumerate(frequencies):
    first, last, group = next(r for r in ranges if r[0] <= code <= r[1])
    number = str(code-first)
    if code == 114:
        number = "DIA"
    elif 115 <= code <= 130:
        number = list("ABCDEFGHJKLMPQRS")[code-115]
    elif 190 <= code <= 239:
        number = str((code-first+1)%10)
    elif group in ("Not Defined", "Spear", "Plectron Format Tones"):
        number = ""
    entries.append({"code":code,"number":number,"hz":hz,"group":group,"selectable":hz>0 and group!="Not Defined"})
out = Path(__file__).resolve().parents[1]/"tonepage"/"resources"
out.mkdir(exist_ok=True)
(out/"tone-reference.json").write_text(json.dumps({"title":"CE45 EEPROM Programming Software Reference Manual - 2-Tone Code Chart", "source":"tone-chart.pdf", "source_page_label":"21", "source_sha256":hashlib.sha256(args.pdf.read_bytes()).hexdigest(), "entries":entries},indent=2),encoding="utf-8")
shutil.copyfile(args.pdf, out/"tone-chart.pdf")
print(f"Packaged {len(entries)} chart rows; {sum(e['selectable'] for e in entries)} selectable frequencies")

