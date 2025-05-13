from flask import Flask, request, jsonify, send_file
import os
import cairosvg
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
from zipfile import ZipFile
from werkzeug.utils import secure_filename
from xml.etree import ElementTree as ET
from flask_cors import CORS
import uuid
import traceback
import time
import shutil
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
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

def convert_svg_to_gcode(svg_path, color, speed, output_folder=None):
    try:
        # Parse the SVG file to extract paths
        curves = parse_file(svg_path)
        
        # Create a G-code compiler with proper settings
        gcode_compiler = Compiler(
            lambda: CustomGcode(color), 
            movement_speed=speed, 
            cutting_speed=0, 
            pass_depth=1
        )
        
        # Append all curves to the compiler
        gcode_compiler.append_curves(curves)
        
        # Generate the output file path
        folder = output_folder if output_folder else UPLOAD_FOLDER
        gcode_filepath = os.path.join(folder, f"{color}.gcode")
        
        # Compile directly to file
        gcode_compiler.compile_to_file(gcode_filepath)
        
        return gcode_filepath
    except Exception as e:
        app.logger.error(f"Error processing SVG to G-code: {e}")
        return None

def convert_svg_to_png(svg_path, output_folder=None):
    folder = output_folder if output_folder else UPLOAD_FOLDER
    png_filepath = os.path.join(folder, 'original.png')
    cairosvg.svg2png(url=svg_path, write_to=png_filepath)
    return png_filepath

def split_svg_by_color(svg_path, output_folder=None):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        base_template = {}
        for key in root.attrib:
            base_template[key] = root.attrib[key]
        if 'xmlns' not in base_template:
            base_template['xmlns'] = svg_ns['svg']
        
        # Initialize color layers with template
        cmyk_colors = ['cyan', 'magenta', 'yellow', 'black']
        
        # Track all unique colors in the SVG
        color_set = set()
        
        # Extract all colors from fill attributes
        for element in root.findall('.//*[@fill]', namespaces=svg_ns):
            fill = element.get('fill')
            if fill and fill.lower() != 'none':
                color_set.add(fill)
                
        # If no fills found, try stroke attributes
        if not color_set:
            for element in root.findall('.//*[@stroke]', namespaces=svg_ns):
                stroke = element.get('stroke')
                if stroke and stroke.lower() != 'none':
                    color_set.add(stroke)
        
        # Create mapping of found colors to CMYK
        color_mapping = {}
        if len(color_set) > 0:
            # Sort colors to ensure consistent mapping
            sorted_colors = sorted(list(color_set))
            
            # Map colors to CMYK
            for i, color in enumerate(sorted_colors):
                color_mapping[color] = cmyk_colors[i % len(cmyk_colors)]
            
            app.logger.info(f"Found colors: {sorted_colors}")
            app.logger.info(f"Mapped to CMYK: {color_mapping}")
        else:
            # No colors found, fallback to treating paths by ID
            app.logger.info("No fill/stroke colors found, trying path IDs")
        
        # Initialize layers for each CMYK color
        layers = {}
        for color in cmyk_colors:
            layers[color] = ET.Element('svg', base_template)
        
        # Collect paths by color in a single pass
        color_paths = {color: [] for color in cmyk_colors}
        
        # Try to process paths with color fill/stroke first
        for element in root.findall('.//svg:path', namespaces=svg_ns):
            if element.get('fill') and element.get('fill').lower() != 'none':
                # Map this color to a CMYK color
                fill = element.get('fill')
                cmyk_color = color_mapping.get(fill)
                if cmyk_color:
                    # Create a copy of the element to avoid modification issues
                    path_copy = ET.Element('path')
                    for attr, value in element.attrib.items():
                        path_copy.set(attr, value)
                    # Set the id attribute to the CMYK color for the next conversion steps
                    path_copy.set('id', cmyk_color)
                    color_paths[cmyk_color].append(path_copy)
            elif element.get('stroke') and element.get('stroke').lower() != 'none':
                # Try stroke if no fill
                stroke = element.get('stroke')
                cmyk_color = color_mapping.get(stroke)
                if cmyk_color:
                    path_copy = ET.Element('path')
                    for attr, value in element.attrib.items():
                        path_copy.set(attr, value)
                    path_copy.set('id', cmyk_color)
                    color_paths[cmyk_color].append(path_copy)
            else:
                # Fallback to ID-based color matching
                color = element.attrib.get('id')
                if color in cmyk_colors:
                    path_copy = ET.Element('path')
                    for attr, value in element.attrib.items():
                        path_copy.set(attr, value)
                    color_paths[color].append(path_copy)
        
        # If still no paths found by color, just put all paths in black
        if all(len(paths) == 0 for paths in color_paths.values()):
            app.logger.info("No colored paths found, putting all in black layer")
            for element in root.findall('.//svg:path', namespaces=svg_ns):
                path_copy = ET.Element('path')
                for attr, value in element.attrib.items():
                    path_copy.set(attr, value)
                path_copy.set('id', 'black')
                color_paths['black'].append(path_copy)
        
        # Try to process other SVG elements (circle, rect, etc.) if paths weren't sufficient
        if all(len(paths) == 0 for paths in color_paths.values()):
            app.logger.info("No colored paths found, looking for other SVG elements")
            for elem_type in ['circle', 'rect', 'polygon', 'polyline', 'ellipse', 'line']:
                for element in root.findall(f'.//svg:{elem_type}', namespaces=svg_ns):
                    if element.get('fill') and element.get('fill').lower() != 'none':
                        fill = element.get('fill')
                        cmyk_color = color_mapping.get(fill)
                        if cmyk_color:
                            # Create a path copy instead (convert to path)
                            path_copy = ET.Element('path')
                            # Copy attributes that are relevant
                            for attr, value in element.attrib.items():
                                if attr not in ['cx', 'cy', 'r', 'rx', 'ry', 'width', 'height', 'x', 'y', 'points']:
                                    path_copy.set(attr, value)
                            # Set a default d attribute to make it a valid path
                            path_copy.set('d', f"M0,0 L1,1")  # Placeholder path
                            path_copy.set('id', cmyk_color)
                            color_paths[cmyk_color].append(path_copy)
                    elif element.get('stroke') and element.get('stroke').lower() != 'none':
                        stroke = element.get('stroke')
                        cmyk_color = color_mapping.get(stroke)
                        if cmyk_color:
                            path_copy = ET.Element('path')
                            for attr, value in element.attrib.items():
                                if attr not in ['cx', 'cy', 'r', 'rx', 'ry', 'width', 'height', 'x', 'y', 'points']:
                                    path_copy.set(attr, value)
                            path_copy.set('d', f"M0,0 L1,1")  # Placeholder path
                            path_copy.set('id', cmyk_color)
                            color_paths[cmyk_color].append(path_copy)
        
        # Now append paths to their respective SVG layers
        for color, paths in color_paths.items():
            for path in paths:
                layers[color].append(path)
        
        # Write SVG files and collect paths
        svg_layers = {}
        folder = output_folder if output_folder else UPLOAD_FOLDER
        for color, layer in layers.items():
            # Only create SVG file if there are paths for this color
            if len(color_paths[color]) > 0:
                layer_path = os.path.join(folder, f"{color}.svg")
                
                # Standard ElementTree serialization
                layer_tree = ET.ElementTree(layer)
                layer_tree.write(layer_path, encoding='unicode', xml_declaration=True)
                
                svg_layers[color] = layer_path
        
        # If no valid layers were created, log the issue
        if not svg_layers:
            app.logger.error(f"No valid SVG layers created from {svg_path}")
        
        return svg_layers
    except Exception as e:
        app.logger.error(f"Error in split_svg_by_color: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return {}

def convert_svg_to_separated_gcode(svg_path, speed, output_folder=None):
    """Convert a single SVG file into G-code and then separate by color."""
    try:
        # Set the output folder
        folder = output_folder if output_folder else UPLOAD_FOLDER
        
        # First extract color information from SVG elements
        tree = ET.parse(svg_path)
        root = tree.getroot()
        svg_ns = {'svg': 'http://www.w3.org/2000/svg'}
        
        # Extract CMYK colors from the SVG
        cmyk_colors = ['cyan', 'magenta', 'yellow', 'black']
        
        # Track colors by element ID
        element_colors = {}
        
        # Extract colors from fill/stroke attributes
        color_mapping = {}
        unique_colors = set()
        
        # First collect all unique colors from fill attributes
        for element in root.findall('.//*[@fill]', namespaces=svg_ns):
            fill = element.get('fill')
            if fill and fill.lower() != 'none':
                unique_colors.add(fill)
                element_id = element.get('id')
                if element_id:
                    element_colors[element_id] = fill
        
        # Then from stroke attributes if fill is not present
        if not unique_colors:
            for element in root.findall('.//*[@stroke]', namespaces=svg_ns):
                stroke = element.get('stroke')
                if stroke and stroke.lower() != 'none':
                    unique_colors.add(stroke)
                    element_id = element.get('id')
                    if element_id:
                        element_colors[element_id] = stroke
        
        # Map the unique colors to CMYK
        if unique_colors:
            sorted_colors = sorted(list(unique_colors))
            for i, color in enumerate(sorted_colors):
                color_mapping[color] = cmyk_colors[i % len(cmyk_colors)]
            app.logger.info(f"Found colors: {sorted_colors}")
            app.logger.info(f"Mapped to CMYK: {color_mapping}")
        else:
            app.logger.info("No fill/stroke colors found in SVG")
        
        # Parse the SVG file to extract paths using svg_to_gcode library
        curves = parse_file(svg_path)
        
        if not curves:
            app.logger.error(f"No valid curves found in SVG file: {svg_path}")
            return {}
            
        # Create a dictionary to store curves by color
        curves_by_color = {}
        
        # Initialize with 'black' as default
        curves_by_color['black'] = []
        
        # Group curves by color - we can't modify the curve objects directly
        for curve in curves:
            # We'll use a default color of black
            color = 'black'
            
            # Try to get ID information if available
            curve_id = getattr(curve, 'element_id', None)
            
            # If curve has an ID that maps to a color we detected
            if curve_id and curve_id in element_colors:
                original_color = element_colors[curve_id]
                # Map the original color to a CMYK color
                cmyk_color = color_mapping.get(original_color)
                if cmyk_color:
                    color = cmyk_color
            
            # If curve has an ID that directly matches a CMYK color
            elif curve_id and curve_id in cmyk_colors:
                color = curve_id
            
            # Add to the appropriate color group
            if color not in curves_by_color:
                curves_by_color[color] = []
            curves_by_color[color].append(curve)
        
        # Get all unique color IDs from curves after processing
        colors = list(curves_by_color.keys())
        
        # If no colors found, use black as default
        if not colors:
            app.logger.info("No colors found in curves, using 'black' as default")
            colors = ['black']
            curves_by_color['black'] = curves
        
        app.logger.info(f"Found the following colors in SVG after processing: {colors}")
        
        # Create a G-code file for each color
        gcode_files = {}
        
        for color in colors:
            # Get curves for this color
            color_curves = curves_by_color.get(color, [])
            
            # If no curves for this color, skip
            if not color_curves:
                continue
                
            # Create a G-code compiler with settings for this color
            gcode_compiler = Compiler(
                lambda: CustomGcode(color),
                movement_speed=speed,
                cutting_speed=0,
                pass_depth=1
            )
            
            # Append the filtered curves
            gcode_compiler.append_curves(color_curves)
            
            # Output path for this color's G-code
            gcode_filepath = os.path.join(folder, f"{color}.gcode")
            
            # Compile to file
            gcode_compiler.compile_to_file(gcode_filepath)
            
            # Add to the result
            gcode_files[color] = gcode_filepath
        
        # If we didn't find any color-specific curves, try compiling all curves as one color
        if not gcode_files:
            app.logger.info("No color-specific curves found, compiling all as 'black'")
            
            gcode_compiler = Compiler(
                lambda: CustomGcode('black'),
                movement_speed=speed,
                cutting_speed=0,
                pass_depth=1
            )
            
            gcode_compiler.append_curves(curves)
            
            gcode_filepath = os.path.join(folder, "black.gcode")
            gcode_compiler.compile_to_file(gcode_filepath)
            
            gcode_files['black'] = gcode_filepath
            
        return gcode_files
        
    except Exception as e:
        app.logger.error(f"Error in convert_svg_to_separated_gcode: {e}")
        app.logger.error(traceback.format_exc())
        return {}

@app.route('/api/convert', methods=['POST'])
def convert():
    if 'svg_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['svg_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    # Validate file extension
    if not file.filename.lower().endswith('.svg'):
        return jsonify({'success': False, 'message': 'File must be an SVG'}), 400

    # Start timing the conversion
    start_time = time.time()
    
    # Create a unique session ID for this conversion to avoid filename conflicts
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(session_folder, filename)
        file.save(filepath)

        # Retrieve parameters
        speed = int(request.form.get('speed', 155))
        
        # Generate PNG preview
        png_file = convert_svg_to_png(filepath, session_folder)
        
        # New approach: Convert directly to G-code and separate by color in one step
        app.logger.info("Converting SVG to G-code and separating by color")
        gcode_files_dict = convert_svg_to_separated_gcode(filepath, speed, session_folder)
        
        if not gcode_files_dict:
            # Fall back to old method if new method didn't work
            app.logger.info("Falling back to color-splitting method")
            svg_layers = split_svg_by_color(filepath, session_folder)
            if not svg_layers:
                # Clean up session folder
                shutil.rmtree(session_folder, ignore_errors=True)
                return jsonify({'success': False, 'message': 'No valid color layers found in SVG. Please check your SVG file has valid paths and color information.'}), 400
            
            # Process each color layer
            gcode_files = []
            
            # Using multiprocessing if available for faster conversion
            try:
                from multiprocessing import Pool
                from functools import partial
                
                # Create a partial function with fixed speed and session folder
                process_color = partial(convert_svg_to_gcode, speed=speed, output_folder=session_folder)
                
                # Create a list of (svg_path, color) tuples to process
                color_paths = [(svg_path, color) for color, svg_path in svg_layers.items()]
                
                # Process in parallel
                with Pool() as pool:
                    results = pool.starmap(process_color, color_paths)
                    
                # Filter out None results (errors)
                gcode_files = [f for f in results if f]
                
            except (ImportError, OSError):
                # Fall back to sequential processing
                for color, svg_path in svg_layers.items():
                    gcode_file = convert_svg_to_gcode(svg_path, color, speed, session_folder)
                    if gcode_file:
                        gcode_files.append(gcode_file)
        else:
            # Convert the dictionary to a list of files
            gcode_files = list(gcode_files_dict.values())
            app.logger.info(f"Generated G-code files for colors: {list(gcode_files_dict.keys())}")

        # Create zip file with results (both PNG and G-code files)
        if gcode_files:
            # Calculate processing time
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            
            zip_filename = f'files-{datetime.now().strftime("%Y%m%d%H%M%S")}.zip'
            zip_filepath = os.path.join(session_folder, zip_filename)
            
            # Use standard zipfile creation without specifying compression level
            with ZipFile(zip_filepath, 'w') as zipf:
                zipf.write(png_file, os.path.basename(png_file))
                for gcode_file in gcode_files:
                    zipf.write(gcode_file, os.path.basename(gcode_file))
                
                # Add a README with processing info
                info_file = os.path.join(session_folder, 'processing_info.txt')
                with open(info_file, 'w') as f:
                    f.write(f"Processing information:\n")
                    f.write(f"- Original file: {filename}\n")
                    f.write(f"- Processing time: {processing_time} seconds\n")
                    f.write(f"- Speed setting: {speed} mm/min\n")
                    f.write(f"- Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"- Total layers: {len(gcode_files)}\n")
                    f.write(f"- Colors: {list(gcode_files_dict.keys()) if gcode_files_dict else 'Generated from layers'}\n")
                
                zipf.write(info_file, os.path.basename(info_file))
                    
            return jsonify({
                'success': True, 
                'download_url': f'/api/download/{session_id}/{zip_filename}',
                'processing_time': processing_time,
                'colors': list(gcode_files_dict.keys()) if gcode_files_dict else list(svg_layers.keys()) if 'svg_layers' in locals() else ['black']
            })
        else:
            # Clean up session folder if no files were generated
            shutil.rmtree(session_folder, ignore_errors=True)
            return jsonify({'success': False, 'message': 'Error generating G-code. The SVG file may not contain valid path elements.'}), 400

    except cairosvg.surface.PNGSurface as e:
        # Handle specific error with PNG conversion
        shutil.rmtree(session_folder, ignore_errors=True)
        app.logger.error(f"Error converting SVG to PNG: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error rendering SVG: {str(e)}. The SVG file may contain unsupported features.'}), 400
    
    except Exception as e:
        # Clean up session folder in case of error
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