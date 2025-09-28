#!/usr/bin/env python3
"""
lightburn_export.py

Konvertiert eine LightBurn .lbrn / .lbrn2 (XML) Datei in:
- SVG (Standard, schnell)
- PNG (benötigt CairoSVG)

Beispiele:
    python script.py eingabe.lbrn2 ausgabe.svg
    python script.py eingabe.lbrn2 ausgabe.png

Hinweise PNG:
- Für den PNG-Export wird das Python-Paket "cairosvg" benötigt.
- Installation (eine der Varianten):
    pip install cairosvg
    python3 -m pip install cairosvg
"""

import sys
import base64
import xml.etree.ElementTree as ET
from pathlib import Path
from html import escape

SVG_HEADER = '<?xml version="1.0" encoding="utf-8"?>\n'

def parse_matrix(elem):
    # LightBurn uses m11..m32 sometimes. Try both styles.
    keys = ['m11','m12','m21','m22','m31','m32']
    vals = []
    for k in keys:
        v = elem.get(k)
        if v is None:
            break
        vals.append(v)
    if len(vals) == 6:
        # SVG uses matrix(a b c d e f)
        return f'matrix({vals[0]} {vals[1]} {vals[2]} {vals[3]} {vals[4]} {vals[5]})'
    # sometimes there's a single "Matrix" attribute or child text; try to parse
    mtext = (
        elem.get('Matrix')
        or (elem.findtext('Matrix') if elem.find('Matrix') is not None else None)
        or (elem.findtext('XForm') if elem.find('XForm') is not None else None)
    )
    if mtext:
        parts = mtext.replace(',', ' ').split()
        if len(parts) >= 6:
            return f'matrix({parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]} {parts[5]})'
    return None

def add_style_from_cutsettings(elem):
    # Very basic: if element has CutSettingName or LayerIndex, we map to stroke.
    style = {}
    color = elem.get('Color') or elem.get('colour') or elem.findtext('Color')
    if color:
        # LightBurn colors sometimes as "#RRGGBB"
        style['stroke'] = color
    stroke_w = elem.get('StrokeWidth') or elem.findtext('StrokeWidth')
    if stroke_w:
        style['stroke-width'] = stroke_w
    fill = elem.get('Fill') or elem.findtext('Fill')
    if fill and fill.lower() not in ['none', 'false', '0']:
        style['fill'] = fill
    else:
        style.setdefault('fill', 'none')
    # Fallback: ensure visible stroke if nothing else specified
    if 'stroke' not in style and (style.get('fill') in (None, 'none')):
        style['stroke'] = '#000'
        style.setdefault('stroke-width', '1')
    # return style string
    return ';'.join(f'{k}:{v}' for k, v in style.items())

def svg_rect_from_elem(elem):
    x = elem.get('X') or elem.get('x') or elem.findtext('X') or '0'
    y = elem.get('Y') or elem.get('y') or elem.findtext('Y') or '0'
    w = elem.get('Width') or elem.get('Width') or elem.findtext('Width') or elem.get('W') or '0'
    h = elem.get('Height') or elem.get('Height') or elem.findtext('Height') or elem.get('H') or '0'
    style = add_style_from_cutsettings(elem)
    t = parse_matrix(elem)
    tr = f' transform="{t}"' if t else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" style="{style}"{tr} />'

def svg_ellipse_from_elem(elem):
    cx = elem.get('CX') or elem.get('cx') or elem.findtext('CX') or '0'
    cy = elem.get('CY') or elem.get('cy') or elem.findtext('CY') or '0'
    rx = elem.get('RX') or elem.get('rx') or elem.findtext('RX') or elem.get('RadiusX') or '0'
    ry = elem.get('RY') or elem.get('ry') or elem.findtext('RY') or elem.get('RadiusY') or '0'
    style = add_style_from_cutsettings(elem)
    t = parse_matrix(elem)
    tr = f' transform="{t}"' if t else ''
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" style="{style}"{tr} />'

def svg_path_from_d(d, elem):
    style = add_style_from_cutsettings(elem)
    t = parse_matrix(elem)
    tr = f' transform="{t}"' if t else ''
    return f'<path d="{escape(d)}" style="{style}"{tr} />'

def points_to_path(points_text):
    # Expect points like "x1,y1 x2,y2 x3,y3" or newline separated
    pts = points_text.strip().replace(',', ' ').split()
    if len(pts) < 4:
        return ''
    # regroup into pairs
    coords = []
    it = iter(pts)
    for a, b in zip(it, it):
        coords.append((a, b))
    d = f'M {coords[0][0]} {coords[0][1]}'
    for x, y in coords[1:]:
        d += f' L {x} {y}'
    # close if first==last (optional)
    if coords[0] == coords[-1]:
        d += ' Z'
    return d

def embed_image(elem, out_dir: Path, idx=0):
    # Try to extract embedded Data (base64)
    data_text = elem.get('Data') or elem.findtext('Data')
    if not data_text:
        return None
    # Some Data fields include xml header etc. Try to detect base64 (contains lots of '=' or '/')
    b64 = ''.join(data_text.split())
    # try to decode
    try:
        raw = base64.b64decode(b64, validate=True)
        # attempt to guess format by header
        if raw.startswith(b'\x89PNG'):
            mime = 'image/png'; ext = '.png'
        elif raw[:3] == b'\xff\xd8\xff':
            mime = 'image/jpeg'; ext = '.jpg'
        else:
            mime = 'application/octet-stream'; ext = '.bin'
        fname = f'image_embedded_{idx}{ext}'
        (out_dir / fname).write_bytes(raw)
        # return reference to saved image
        x = elem.get('X') or '0'; y = elem.get('Y') or '0'
        w = elem.get('Width') or elem.findtext('Width') or 'auto'
        h = elem.get('Height') or elem.findtext('Height') or 'auto'
        t = parse_matrix(elem)
        tr = f' transform="{t}"' if t else ''
        # reference as relative path (same folder as output)
        return f'<image href="{fname}" x="{x}" y="{y}" width="{w}" height="{h}"{tr} />'
    except Exception:
        return None

def process_element(elem, out_dir, images_counter):
    tag = elem.tag.split('}')[-1]  # strip namespace
    svgs = []
    if tag.lower() in ('path', 'svgpath', 'shape', 'item'):
        # different projects use different child names
        # try common attributes/text
        d = elem.get('D') or elem.get('d') or elem.findtext('D') or elem.findtext('d') or elem.findtext('Path')
        if d:
            svgs.append(svg_path_from_d(d, elem))
        else:
            # maybe points
            pts = elem.get('Points') or elem.findtext('Points')
            if pts:
                d2 = points_to_path(pts)
                if d2:
                    svgs.append(svg_path_from_d(d2, elem))
    elif tag.lower() in ('polygon','polyline'):
        pts = elem.get('Points') or elem.findtext('Points')
        if pts:
            d2 = points_to_path(pts)
            if d2:
                svgs.append(svg_path_from_d(d2, elem))
    elif tag.lower() in ('rectangle','rect'):
        svgs.append(svg_rect_from_elem(elem))
    elif tag.lower() in ('ellipse','circle'):
        svgs.append(svg_ellipse_from_elem(elem))
    elif tag.lower() == 'text':
        text = elem.get('Text') or elem.findtext('Text') or ''
        x = elem.get('X') or elem.findtext('X') or '0'
        y = elem.get('Y') or elem.findtext('Y') or '0'
        style = add_style_from_cutsettings(elem)
        t = parse_matrix(elem)
        tr = f' transform="{t}"' if t else ''
        svgs.append(f'<text x="{x}" y="{y}" style="{style}"{tr}>{escape(text)}</text>')
    elif tag.lower() == 'image':
        img_tag = embed_image(elem, out_dir, images_counter[0])
        if img_tag:
            svgs.append(img_tag)
            images_counter[0] += 1
    # recurse children
    for c in list(elem):
        svgs.extend(process_element(c, out_dir, images_counter))
    return svgs

def build_svg(infile: Path, out_dir: Path) -> tuple[str, bool, str | None]:
    """Parst die LightBurn-Datei und gibt den SVG-Text zurück.

    Eingebettete Bitmaps (falls vorhanden) werden in out_dir geschrieben und im SVG relativ referenziert.
    """
    # parse XML (LightBurn .lbrn / .lbrn2)
    tree = ET.parse(infile)
    root = tree.getroot()

    # Try to find overall canvas size in root or top-level nodes
    width = root.get('Width') or root.findtext('Width') or '1000'
    height = root.get('Height') or root.findtext('Height') or '1000'

    svg_elems = []
    images_counter = [0]

    # Search for likely containers: <Shapes>, <Items>, <Children>, etc.
    candidates = []
    for candidate_name in ('Shapes','Items','Children','Objects','Root','Document'):
        for node in root.findall('.//' + candidate_name):
            candidates.append(node)
    if not candidates:
        candidates = [root]

    for node in candidates:
        svg_elems.extend(process_element(node, out_dir, images_counter))

    # Build SVG
    svg_body = '\n  '.join(svg_elems)
    svg_text = (
        SVG_HEADER
        + f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        + f'  {svg_body}\n'
        + '</svg>\n'
    )
    # Discover embedded thumbnail (PNG) as a fallback if no vector shapes were recognized
    thumb_b64 = None
    thumb_node = root.find('.//Thumbnail')
    if thumb_node is not None:
        thumb_b64 = thumb_node.get('Source')
    return svg_text, (len(svg_elems) > 0), thumb_b64

def write_svg(svg_text: str, out_path: Path):
    out_path.write_text(svg_text, encoding='utf-8')
    print(f"SVG exportiert: {out_path}")

def write_png(svg_text: str, out_path: Path, base_dir: Path):
    try:
        import cairosvg
    except Exception:
        print("Fehlender PNG-Export: Das Paket 'cairosvg' ist nicht installiert.\n"
              "Installiere es z.B. mit:\n  pip install cairosvg")
        sys.exit(2)

    # Ensure base directory exists for resolving relative image references
    base_dir.mkdir(parents=True, exist_ok=True)
    # CairoSVG nutzt den base URL Kontext, damit relative hrefs (z.B. eingebettete Bilder) gefunden werden
    abs_base = base_dir.resolve()
    base_url = abs_base.as_uri()
    cairosvg.svg2png(bytestring=svg_text.encode('utf-8'), write_to=str(out_path), url=base_url)
    print(f"PNG exportiert: {out_path}")

def main(infile, outfile):
    in_path = Path(infile)
    out_path = Path(outfile)
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    svg_text, has_elems, thumb_b64 = build_svg(in_path, out_dir)

    if out_path.suffix.lower() == '.png':
        if has_elems:
            write_png(svg_text, out_path, out_dir)
        elif thumb_b64:
            # Fallback: write embedded LightBurn thumbnail PNG
            try:
                raw = base64.b64decode(''.join(thumb_b64.split()))
                out_path.write_bytes(raw)
                print(f"PNG exportiert (Thumbnail): {out_path}")
            except Exception as e:
                print(f"Konnte Thumbnail nicht schreiben: {e}")
                print("Keine erkennbaren Vektorelemente gefunden.")
                sys.exit(3)
        else:
            print("Keine erkennbaren Vektorelemente und kein Thumbnail gefunden.")
            sys.exit(3)
    else:
        # Standard: SVG schreiben (auch bei anderen Endungen als .png)
        write_svg(svg_text, out_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Verwendung:\n  python script.py input.lbrn2 output.svg\n  python script.py input.lbrn2 output.png")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])