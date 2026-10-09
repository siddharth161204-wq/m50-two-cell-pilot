#!/bin/bash
# Markdown -> HTML (pandoc) -> PDF (headless Chromium); run from note/
set -e
pandoc m50_two_cell_note.md -f markdown -t html5 -s --css note.css --metadata pagetitle="Where and when a neighbour cell first reaches thermal-runaway onset temperatures: resolved against lumped, a pre-registered two-cell LG M50 pilot" -o m50_two_cell_note.html
python3 - <<'PY'
import re
p = 'm50_two_cell_note.html'
h = open(p).read()
h = re.sub(r'<header id="title-block-header">[\s\S]*?</header>', '', h)
# keep every number on the same line as its unit: non-breaking space, text nodes only
unit = r'(?:C/min|kW/m2|mW/K|W/mK|J/K|W/K|kJ|mm2|mm|UTC|C|K|s|g|%)(?![\w/])'
parts = re.split(r'(<[^>]+>)', h)
for i, t in enumerate(parts):
    if not t.startswith('<'):
        parts[i] = re.sub(r'(\d) (?=' + unit + ')', '\\1\u00a0', t)
open(p, 'w').write(''.join(parts))
PY
CHROME=${CHROME:-/opt/pw-browsers/chromium-1194/chrome-linux/chrome}
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=m50_two_cell_note.pdf --allow-file-access-from-files "file://$(pwd)/m50_two_cell_note.html" 2>/dev/null
pdfinfo m50_two_cell_note.pdf | grep -E 'Title|Pages'
