import os
import re
import math
import cairosvg
from xml.etree import ElementTree as ET
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
try:
    from matplotlib import colors as mcolors
except ImportError:
    mcolors = None

# Fallback map for common CSS color names when matplotlib is unavailable
CSS_COLOR_MAP = {
    'gold': (255, 215, 0),
    # add more named colors here as needed
}

UPLOAD_FOLDER = 'static/uploads'
CMYK_CHANNELS = ['cyan', 'magenta', 'yellow', 'black']


class CustomGcode(interfaces.Gcode):
    def __init__(self, color):
        super().__init__()
        self.color = color

    def start(self):
        return f"; Start of {self.color} layer\n" + super().start()

    def end(self):
        return super().end() + f"\n; End of {self.color} layer"



def normalize_color(color_str):
    """ '#RGB', '#RRGGBB', 'rgb(r,g,b)' or CSS name → (R,G,B) """
    if not color_str:
        return None
    s = color_str.strip().lower()
    # direct lookup for named CSS colors
    if s in CSS_COLOR_MAP:
        return CSS_COLOR_MAP[s]
    # hex notation
    if s.startswith('#'):
        h = s[1:]
        if len(h) == 3:
            h = ''.join(c*2 for c in h)
        if len(h) == 6:
            try:
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            except ValueError:
                return None
    # rgb(r,g,b) notation
    m = re.match(r'rgb\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)', s)
    if m:
        try:
            return tuple(int(float(m.group(i))) for i in (1, 2, 3))
        except ValueError:
            return None
    # matplotlib name lookup
    if mcolors:
        try:
            r, g, b = mcolors.to_rgb(s)
            return (int(r * 255), int(g * 255), int(b * 255))
        except Exception:
            return None
    return None

def rgb_to_cmyk(r, g, b):
    """Dominant-component heuristic."""
    if r >= g and r >= b:
        return 'magenta'
    elif g >= r and g >= b:
        return 'yellow'
    elif b >= r and b >= g:
        return 'cyan'
    else:
        return 'black'

def shape_to_path(elem):
    """
    Convert a basic SVG shape element into a <path> with a 'd' attribute.
    Circles/ellipses are approximated as 32-segment polygons.
    """
    tag = elem.tag.split('}')[-1]
    attr = dict(elem.attrib)
    path_attr = {}
    # carry over styling
    for k in ('fill','stroke','style','transform','id','class'):
        if k in attr:
            path_attr[k] = attr[k]

    d = None
    if tag == 'rect':
        x = float(attr.get('x', 0))
        y = float(attr.get('y', 0))
        w = float(attr.get('width', 0))
        h = float(attr.get('height', 0))
        d = f"M{x},{y} L{x+w},{y} L{x+w},{y+h} L{x},{y+h} Z"

    elif tag == 'line':
        x1 = float(attr.get('x1',0))
        y1 = float(attr.get('y1',0))
        x2 = float(attr.get('x2',0))
        y2 = float(attr.get('y2',0))
        d = f"M{x1},{y1} L{x2},{y2}"

    elif tag in ('polyline','polygon'):
        pts = attr.get('points','').strip()
        coords = re.split(r'[,\s]+', pts)
        pairs = []
        for i in range(0, len(coords)-1, 2):
            try:
                x = float(coords[i]); y = float(coords[i+1])
            except:
                continue
            pairs.append((x,y))
        if pairs:
            d = "M" + " L".join(f"{x},{y}" for x,y in pairs)
            if tag == 'polygon':
                d += " Z"

    elif tag == 'circle':
        cx = float(attr.get('cx',0))
        cy = float(attr.get('cy',0))
        r  = float(attr.get('r',0))
        pts = []
        for i in range(32):
            theta = 2*math.pi*(i/32)
            pts.append((cx + r*math.cos(theta), cy + r*math.sin(theta)))
        d = "M" + " L".join(f"{x:.3f},{y:.3f}" for x,y in pts) + " Z"

    elif tag == 'ellipse':
        cx = float(attr.get('cx',0))
        cy = float(attr.get('cy',0))
        rx = float(attr.get('rx',0))
        ry = float(attr.get('ry',0))
        pts = []
        for i in range(32):
            theta = 2*math.pi*(i/32)
            pts.append((cx + rx*math.cos(theta), cy + ry*math.sin(theta)))
        d = "M" + " L".join(f"{x:.3f},{y:.3f}" for x,y in pts) + " Z"

    if not d:
        return None

    p = ET.Element('path', path_attr)
    p.set('d', d)
    return p


def convert_svg_to_png(svg_path, output_folder=None, app_logger=None):
    folder = output_folder or UPLOAD_FOLDER
    os.makedirs(folder, exist_ok=True)
    png_out = os.path.join(folder, 'original.png')
    try:
        cairosvg.svg2png(url=svg_path, write_to=png_out)
    except Exception as e:
        if app_logger:
            app_logger.error(f"SVG→PNG failed: {e}, using placeholder")
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800,600), 'white')
        d = ImageDraw.Draw(img)
        d.text((10,10), "SVG Preview Unavailable", fill='black')
        d.text((10,30), os.path.basename(svg_path), fill='black')
        img.save(png_out)
    return png_out


def convert_svg_to_gcode(svg_path, color, speed, output_folder=None, app_logger=None):
    folder = output_folder or UPLOAD_FOLDER
    os.makedirs(folder, exist_ok=True)
    try:
        curves = parse_file(svg_path)
        comp = Compiler(lambda: CustomGcode(color),
                        movement_speed=speed,
                        cutting_speed=0,
                        pass_depth=1)
        comp.append_curves(curves)
        out_file = os.path.join(folder, f"{color}.gcode")
        comp.compile_to_file(out_file)
        return out_file
    except Exception as e:
        if app_logger:
            app_logger.error(f"G-code gen error [{color}]: {e}")
        return None


def convert_svg_to_separated_gcode(svg_path, speed, output_folder=None, app_logger=None):
    """
    Returns (detected_colors, gcode_files_dict).  Shapes are first
    converted to paths, so parse_file always finds curves.
    Guarantees at least one 'black' G-code if nothing else maps.
    """
    folder = output_folder or UPLOAD_FOLDER
    os.makedirs(folder, exist_ok=True)

    tree = ET.parse(svg_path)
    root = tree.getroot()
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}

    # prepare buckets
    layers = {c: [] for c in CMYK_CHANNELS}
    detected = []
    seen = set()

    def bucket(elem):
        """Take a <path> element, decide its CMYK layer, clone & store."""
        # prioritize stroke over fill
        col = elem.get('stroke')
        if not col or col.lower() == 'none':
            col = elem.get('fill')
        if col and col.lower() == 'none':
            col = None
        if not col and 'style' in elem.attrib:
            m = re.search(r'(?:stroke|fill)\s*:\s*([^;]+)', elem.attrib['style'])
            if m:
                col = m.group(1).strip()

        rgb   = normalize_color(col)
        layer = rgb_to_cmyk(*rgb) if rgb else 'black'

        if col and col not in seen:
            seen.add(col)
            detected.append({'original': col, 'mapped_to': layer})

        copy_attribs = dict(elem.attrib)
        p = ET.Element('path', copy_attribs)
        p.set('d', elem.get('d',''))
        layers[layer].append(p)

    # 1) bucket all real <path>
    for p in root.findall('.//svg:path', namespaces=svg_ns):
        if p.get('d'):
            bucket(p)

    # 2) always bucket shapes (converted → paths)
    for tag in ['rect','circle','ellipse','line','polyline','polygon']:
        for el in root.findall(f'.//svg:{tag}', namespaces=svg_ns):
            p = shape_to_path(el)
            if p:
                bucket(p)

    # 3) compile each non-empty layer
    gcode_files = {}
    for color, elems in layers.items():
        if not elems:
            continue
        wrapper = ET.Element('svg', {'xmlns': svg_ns['svg'], **root.attrib})
        for e in elems:
            wrapper.append(e)
        svg_out = os.path.join(folder, f"{color}.svg")
        ET.ElementTree(wrapper).write(svg_out, encoding='unicode', xml_declaration=True)

        g = convert_svg_to_gcode(svg_out, color, speed,
                                 output_folder=folder, app_logger=app_logger)
        if g:
            gcode_files[color] = g

    # 4) final fallback: compile original SVG → black
    if not gcode_files:
        if app_logger:
            app_logger.warning("No layers → falling back to single black output")
        black = convert_svg_to_gcode(svg_path, 'black', speed,
                                     output_folder=folder, app_logger=app_logger)
        if black:
            gcode_files['black'] = black
            if not detected:
                detected.append({'original': 'default', 'mapped_to': 'black'})

    return detected, gcode_files


def split_svg_by_color(svg_path, output_folder=None, app_logger=None):
    """
    Legacy fallback: emit one .svg per CMYK channel.
    Shapes are similarly converted → <path>.
    """
    folder = output_folder or UPLOAD_FOLDER
    os.makedirs(folder, exist_ok=True)

    tree = ET.parse(svg_path)
    root = tree.getroot()
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    layers = {c: [] for c in CMYK_CHANNELS}

    def bucket(elem):
        # prioritize stroke over fill
        col = elem.get('stroke')
        if not col or col.lower() == 'none':
            col = elem.get('fill')
        if col and col.lower() == 'none':
            col = None
        if not col and 'style' in elem.attrib:
            m = re.search(r'(?:stroke|fill)\s*:\s*([^;]+)', elem.attrib['style'])
            if m:
                col = m.group(1).strip()
        rgb   = normalize_color(col)
        layer = rgb_to_cmyk(*rgb) if rgb else 'black'
        path = elem if elem.tag.endswith('path') else shape_to_path(elem)
        if path is not None:
            layers[layer].append(path)

    # gather paths & shapes
    for p in root.findall('.//svg:path', namespaces=svg_ns):
        if p.get('d'):
            bucket(p)
    for tag in ['rect','circle','ellipse','line','polyline','polygon']:
        for el in root.findall(f'.//svg:{tag}', namespaces=svg_ns):
            bucket(el)

    # write out per-layer SVGs
    svg_layers = {}
    for color, elems in layers.items():
        if not elems:
            continue
        wrapper = ET.Element('svg', {'xmlns': svg_ns['svg'], **root.attrib})
        for e in elems:
            wrapper.append(e)
        out_svg = os.path.join(folder, f"{color}.svg")
        ET.ElementTree(wrapper).write(out_svg, encoding='unicode', xml_declaration=True)
        svg_layers[color] = out_svg

    return svg_layers
