from flask import Flask, request, jsonify, send_file
import os
import uuid
import traceback
import time
import shutil
from datetime import datetime
from functools import wraps
from flask_cors import CORS
from werkzeug.utils import secure_filename
from zipfile import ZipFile
from threading import Thread
from svg_utils import (
    convert_svg_to_gcode,
    convert_svg_to_png,
    split_svg_by_color,
    convert_svg_to_separated_gcode
)

# Timeout decorator to limit long-running operations
# (Kept if you want to use it for future route timeouts)
def timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [TimeoutError("Function timed out")]
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    result[0] = e
            thread = Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]
        return wrapper
    return decorator

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
SVG_PROCESSING_TIMEOUT = 30

@app.route('/api/convert', methods=['POST'])
def convert():
    if 'svg_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    file = request.files['svg_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    if not file.filename.lower().endswith('.svg'):
        return jsonify({'success': False, 'message': 'File must be an SVG'}), 400
    start_time = time.time()
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    processing_timeout = 30
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(session_folder, filename)
        file.save(filepath)
        speed = int(request.form.get('speed', 155))
        png_file = convert_svg_to_png(filepath, session_folder, app.logger)
        app.logger.info("Converting SVG to G-code and separating by color")
        detected_colors, gcode_files_dict = convert_svg_to_separated_gcode(filepath, speed, session_folder, app.logger)
        if not gcode_files_dict:
            app.logger.info("Falling back to color-splitting method")
            svg_layers = split_svg_by_color(filepath, session_folder, app.logger)
            if not svg_layers:
                shutil.rmtree(session_folder, ignore_errors=True)
                return jsonify({'success': False, 'message': 'No valid color layers found in SVG. Please check your SVG file has valid paths and color information.'}), 400
            gcode_files = []
            try:
                from multiprocessing import Pool
                from functools import partial
                process_color = partial(convert_svg_to_gcode, speed=speed, output_folder=session_folder, app_logger=app.logger)
                color_paths = [(svg_path, color) for color, svg_path in svg_layers.items()]
                with Pool() as pool:
                    results = pool.starmap(process_color, color_paths)
                gcode_files = [f for f in results if f]
            except (ImportError, OSError):
                for color, svg_path in svg_layers.items():
                    gcode_file = convert_svg_to_gcode(svg_path, color, speed, session_folder, app.logger)
                    if gcode_file:
                        gcode_files.append(gcode_file)
        else:
            if isinstance(gcode_files_dict, dict):
                gcode_files = list(gcode_files_dict.values())
                app.logger.info(f"Generated G-code files for colors: {list(gcode_files_dict.keys())}")
            else:
                app.logger.warning("gcode_files_dict is not a dictionary. Using empty list.")
                gcode_files = []
                gcode_files_dict = {}
        if gcode_files:
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            zip_filename = f'files-{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
            zip_filepath = os.path.join(session_folder, zip_filename)
            with ZipFile(zip_filepath, 'w') as zipf:
                zipf.write(png_file, os.path.basename(png_file))
                for gcode_file in gcode_files:
                    zipf.write(gcode_file, os.path.basename(gcode_file))
                info_file = os.path.join(session_folder, 'processing_info.txt')
                with open(info_file, 'w') as f:
                    f.write(f"Processing information:\n")
                    f.write(f"- Original file: {filename}\n")
                    f.write(f"- Processing time: {processing_time} seconds\n")
                    f.write(f"- Speed setting: {speed} mm/min\n")
                    f.write(f"- Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"- Total layers: {len(gcode_files)}\n")
                    if isinstance(gcode_files_dict, dict) and gcode_files_dict:
                        f.write(f"- Colors: {list(gcode_files_dict.keys())}\n")
                    elif 'svg_layers' in locals() and svg_layers:
                        f.write(f"- Colors: {list(svg_layers.keys())}\n") 
                    else:
                        f.write(f"- Colors: ['black']\n")
                zipf.write(info_file, os.path.basename(info_file))
            return jsonify({
                'success': True, 
                'download_url': f'/api/download/{session_id}/{zip_filename}',
                'processing_time': processing_time,
                'colors': list(gcode_files_dict.keys()) if isinstance(gcode_files_dict, dict) and gcode_files_dict 
                          else list(svg_layers.keys()) if 'svg_layers' in locals() and svg_layers 
                          else ['black']
            })
        else:
            shutil.rmtree(session_folder, ignore_errors=True)
            return jsonify({'success': False, 'message': 'Error generating G-code. The SVG file may not contain valid path elements.'}), 400
    except Exception as e:
        if 'cairosvg.surface.PNGSurface' in str(e.__class__):
            shutil.rmtree(session_folder, ignore_errors=True)
            app.logger.error(f"Error converting SVG to PNG: {e}")
            app.logger.error(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Error rendering SVG: {str(e)}. The SVG file may contain unsupported features.'}), 400
    except Exception as e:
        shutil.rmtree(session_folder, ignore_errors=True)
        app.logger.error(f"Error in conversion process: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Internal server error during conversion: {str(e)}'}), 500

@app.route('/api/download/<session_id>/<filename>')
def download_file(session_id, filename):
    filepath = os.path.join(UPLOAD_FOLDER, session_id, filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    try:
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error sending file {filename}: {e}")
        return jsonify({'success': False, 'message': 'Error sending file'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)