from flask import Flask, request, jsonify, send_file
import os
import cairosvg
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from zipfile import ZipFile
from werkzeug.utils import secure_filename
from xml.etree import ElementTree as ET

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class CustomGcode(interfaces.Gcode):
    def __init__(self, color):
        super().__init__()
        self.color = color

    def start(self):
        return f"; Start of {self.color} layer\n" + super().start()

    def end(self):
        return super().end() + f"\n; End of {self.color} layer"

def convert_svg_to_gcode(svg_path, color, laser_power, speed, pass_depth):
    try:
        curves = parse_file(svg_path)
        gcode_compiler = Compiler(lambda: CustomGcode(color), movement_speed=speed, cutting_speed=laser_power, pass_depth=pass_depth)
        gcode_compiler.append_curves(curves)
        gcode_filepath = os.path.join(UPLOAD_FOLDER, f"{color}.gcode")
        gcode_compiler.compile_to_file(gcode_filepath)
        return gcode_filepath
    except Exception as e:
        app.logger.error(f"Error processing SVG to G-code: {e}")
        return None

def convert_svg_to_png(svg_path):
    png_filepath = os.path.join(UPLOAD_FOLDER, 'original.png')
    cairosvg.svg2png(url=svg_path, write_to=png_filepath)
    return png_filepath

def split_svg_by_color(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
    layers = {
        'black': ET.Element('svg', root.attrib),
        'yellow': ET.Element('svg', root.attrib),
        'cyan': ET.Element('svg', root.attrib),
        'magenta': ET.Element('svg', root.attrib)
    }

    for layer in layers.values():
        layer.set('xmlns', svg_ns['svg'])

    for element in root.findall('.//svg:path', namespaces=svg_ns):
        color = element.attrib.get('id')
        if color in layers:
            layers[color].append(element)

    svg_layers = {}
    for color, layer in layers.items():
        layer_tree = ET.ElementTree(layer)
        layer_path = os.path.join(UPLOAD_FOLDER, f"{color}.svg")
        layer_tree.write(layer_path, encoding='unicode', xml_declaration=True)
        svg_layers[color] = layer_path

    return svg_layers

@app.route('/api/convert', methods=['POST'])
def convert():
    if 'svg_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['svg_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Retrieve parameters
    mode = request.form.get('mode')
    laser_power = int(request.form.get('laser_power', 1000))
    speed = int(request.form.get('speed', 900))
    pass_depth = int(request.form.get('pass_depth', 5))

    # Generate G-code or Drawing based on mode
    try:
        if mode == 'drilling':
            gcode_file = convert_svg_to_gcode(filepath, 'drilling', laser_power, speed, pass_depth)
            png_file = convert_svg_to_png(filepath)
            if gcode_file:
                zip_filepath = os.path.join(UPLOAD_FOLDER, 'files.zip')
                with ZipFile(zip_filepath, 'w') as zipf:
                    zipf.write(png_file, os.path.basename(png_file))
                    zipf.write(gcode_file, os.path.basename(gcode_file))
                return jsonify({'success': True, 'download_url': f'/api/download/{os.path.basename(zip_filepath)}'})
            else:
                return jsonify({'success': False, 'message': 'Error generating G-code for drilling'}), 500

        elif mode == 'drawing':
            png_file = convert_svg_to_png(filepath)
            svg_layers = split_svg_by_color(filepath)
            gcode_files = []
            for color, svg_path in svg_layers.items():
                gcode_file = convert_svg_to_gcode(svg_path, color, laser_power, speed, pass_depth)
                if gcode_file:
                    gcode_files.append(gcode_file)

            if gcode_files:
                zip_filepath = os.path.join(UPLOAD_FOLDER, 'files.zip')
                with ZipFile(zip_filepath, 'w') as zipf:
                    zipf.write(png_file, os.path.basename(png_file))
                    for gcode_file in gcode_files:
                        zipf.write(gcode_file, os.path.basename(gcode_file))
                return jsonify({'success': True, 'download_url': f'/api/download/{os.path.basename(zip_filepath)}'})
            else:
                return jsonify({'success': False, 'message': 'Error generating G-code for drawing'}), 500

    except Exception as e:
        app.logger.error(f"Error in conversion process: {e}")
        return jsonify({'success': False, 'message': 'Internal server error during conversion'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    try:
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error sending file {filename}: {e}")
        return jsonify({'success': False, 'message': 'Error sending file'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
