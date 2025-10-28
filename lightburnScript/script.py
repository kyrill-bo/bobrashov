#!/usr/bin/env python3
"""
lightburn_export.py

Konvertiert eine LightBurn .lbrn / .lbrn2 (XML) Datei in PNG.

Beispiele:
    python script.py eingabe.lbrn2            # erzeugt eingabe.png neben der Eingabedatei
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

    b64 = ''.join(data_text.split())

    # try to decode to guess format
    try:
        raw = base64.b64decode(b64, validate=True)
        if raw.startswith(b'\x89PNG'):
            mime = 'image/png'
        elif raw[:3] == b'\xff\xd8\xff':
            mime = 'image/jpeg'
        else:
            mime = 'image/png'  # fallback
    except Exception:
        mime = 'image/png' # fallback

    data_uri = f"data:{mime};base64,{b64}"

    x = elem.get('X') or '0'
    y = elem.get('Y') or '0'
    w = elem.get('Width') or elem.findtext('Width') or 'auto'
    h = elem.get('Height') or elem.findtext('Height') or 'auto'
    t = parse_matrix(elem)
    tr = f' transform="{t}"' if t else ''
    return f'<image href="{data_uri}" x="{x}" y="{y}" width="{w}" height="{h}"{tr} />'

def process_element(elem, out_dir, images_counter):
    tag = elem.tag.split('}')[-1]  # strip namespace
    svgs = []

    # Handle <Shape Type="..."> elements
    if tag.lower() == 'shape':
        shape_type = elem.get('Type', '').lower()
        if shape_type in ('rect', 'rectangle'):
            svgs.append(svg_rect_from_elem(elem))
        elif shape_type in ('ellipse', 'circle'):
            svgs.append(svg_ellipse_from_elem(elem))
        elif shape_type == 'text':
            text = elem.get('Str', '')
            if text:
                style = add_style_from_cutsettings(elem)
                t = parse_matrix(elem)
                tr = f' transform="{t}"' if t else ''
                font_size = elem.get('H')
                if font_size:
                    style += f';font-size:{font_size}px'
                font_family_attr = elem.get('Font')
                if font_family_attr:
                    font_family = font_family_attr.split(',')[0]
                    style += f';font-family:{font_family}'
                style += ';text-anchor:middle'
                
                lines = escape(text).split('\n')
                text_svg = f'<text x="0" y="0" style="{style}"{tr}>'
                for i, line in enumerate(lines):
                    dy = '1.2em' if i > 0 else '0'
                    text_svg += f'<tspan x="0" dy="{dy}">{line}</tspan>'
                text_svg += '</text>'
                svgs.append(text_svg)

        elif shape_type == 'bitmap':
            img_tag = embed_image(elem, out_dir, images_counter[0])
            if img_tag:
                svgs.append(img_tag)
                images_counter[0] += 1
        elif shape_type == 'path':
            d = elem.get('D') or elem.get('d')
            if d:
                svgs.append(svg_path_from_d(d, elem))

    # Legacy handling for other formats
    elif tag.lower() in ('path', 'svgpath', 'shape', 'item'):
        d = elem.get('D') or elem.get('d') or elem.findtext('D') or elem.findtext('d') or elem.findtext('Path')
        if d:
            svgs.append(svg_path_from_d(d, elem))
        else:
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
    
    # Recurse into children
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

    # Get original canvas size, default to 1000x1000
    width_str = root.get('Width') or root.findtext('Width') or '1000'
    height_str = root.get('Height') or root.findtext('Height') or '1000'
    original_width = float(width_str)
    original_height = float(height_str)

    # Scale the output PNG size up to a minimum dimension
    scaled_width = original_width
    scaled_height = original_height
    min_size = 1080
    if scaled_width > scaled_height:
        if scaled_width < min_size:
            scale = min_size / scaled_width
            scaled_width = min_size
            scaled_height *= scale
    else:
        if scaled_height < min_size:
            scale = min_size / scaled_height
            scaled_height = min_size
            scaled_width *= scale

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

    # Use a fixed viewBox based on the original canvas size
    viewbox_str = f'0 0 {original_width} {original_height}'

    # Sort elements to draw images behind vectors
    image_elems = [s for s in svg_elems if s.strip().startswith('<image')]
    vector_elems = [s for s in svg_elems if not s.strip().startswith('<image')]
    sorted_elems = image_elems + vector_elems
    svg_body = '\n  '.join(sorted_elems)

    # Build SVG
    svg_text = (
        SVG_HEADER
        + f'<svg xmlns="http://www.w3.org/2000/svg" width="{scaled_width}" height="{scaled_height}" viewBox="{viewbox_str}">\n'
        + f'  {svg_body}\n'
        + '</svg>\n'
    )
    
    # Discover embedded thumbnail (PNG) as a fallback if no vector shapes were recognized
    thumb_b64 = None
    thumb_node = root.find('.//Thumbnail')
    if thumb_node is not None:
        thumb_b64 = thumb_node.get('Source')
    return svg_text, (len(svg_elems) > 0), thumb_b64

def write_png(svg_text: str, out_path: Path, base_dir: Path):
    """Schreibt PNG aus SVG-Text.

    Primär via Qt (PySide6); falls nicht verfügbar, verwende CairoSVG als Fallback.
    """
    # 1) Versuch: Qt (PySide6)
    try:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QImage, QPainter, QGuiApplication
        from PySide6.QtCore import QByteArray, QSize

        app = QGuiApplication.instance() or QGuiApplication([])
        renderer = QSvgRenderer(QByteArray(svg_text.encode('utf-8')))
        size = renderer.defaultSize()
        if not size.isValid():
            # Fallback-Größe, falls SVG keine Size anbietet
            size = QSize(1000, 1000)
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(0x00000000)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        if not image.save(str(out_path)):
            raise RuntimeError("Konnte PNG nicht speichern")
        print(f"PNG exportiert (Qt): {out_path}")
        return
    except Exception as e_qt:
        # 2) Fallback: CairoSVG
        try:
            import cairosvg
            base_dir.mkdir(parents=True, exist_ok=True)
            abs_base = base_dir.resolve()
            base_url = abs_base.as_uri()
            cairosvg.svg2png(bytestring=svg_text.encode('utf-8'), write_to=str(out_path), url=base_url)
            print(f"PNG exportiert (CairoSVG-Fallback): {out_path}")
            return
        except Exception as e_cairo:
            print("Fehlender PNG-Export: Weder Qt noch 'cairosvg' konnten das Bild rendern.")
            print(f"Qt-Fehler: {e_qt}")
            print(f"CairoSVG-Fehler: {e_cairo}")
            print("Installiere entweder 'PySide6' oder 'cairosvg'.")
            sys.exit(2)

def main(infile, outfile=None):
    in_path = Path(infile)
    # Wenn kein Output angegeben, verwende Eingabenamen mit .png in gleichem Ordner
    if outfile is None:
        out_path = in_path.with_suffix('.png')
    else:
        out_path = Path(outfile)
    # Erzwinge PNG-Endung
    if out_path.suffix.lower() != '.png':
        out_path = out_path.with_suffix('.png')

    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    svg_text, has_elems, thumb_b64 = build_svg(in_path, out_dir)

    if has_elems:
        write_png(svg_text, out_path, out_dir)
    elif thumb_b64:
        # Fallback: schreibe eingebettetes LightBurn-Thumbnail PNG
        try:
            from PySide6.QtGui import QImage, QGuiApplication
            from PySide6.QtCore import QSize

            app = QGuiApplication.instance() or QGuiApplication([])
            
            raw = base64.b64decode(''.join(thumb_b64.split()))
            image = QImage()
            image.loadFromData(raw)

            width = image.width()
            height = image.height()
            
            min_size = 1080

            if width > height:
                if width < min_size:
                    scale = min_size / width
                    new_width = min_size
                    new_height = int(height * scale)
                else:
                    new_width = width
                    new_height = height
            else:
                if height < min_size:
                    scale = min_size / height
                    new_height = min_size
                    new_width = int(width * scale)
                else:
                    new_width = width
                    new_height = height
            
            resized_image = image.scaled(QSize(new_width, new_height))
            
            if not resized_image.save(str(out_path)):
                raise RuntimeError("Konnte skaliertes Thumbnail nicht speichern")

            print(f"PNG exportiert (skaliertes Thumbnail): {out_path}")
        except Exception as e:
            print(f"Konnte Thumbnail nicht schreiben oder skalieren: {e}")
            print("Keine erkennbaren Vektorelemente gefunden.")
            sys.exit(3)
    else:
        print("Keine erkennbaren Vektorelemente und kein Thumbnail gefunden.")
        sys.exit(3)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Verwendung:\n  python script.py input.lbrn2 [output.png]\n\nOhne output wird automatisch input.png erzeugt.")
        sys.exit(1)
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(sys.argv[1], sys.argv[2])