#!/usr/bin/env python3
# Benchmark script for SVG to Gcode conversion service

import os
import time
import requests
import pandas as pd
import glob
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Configuration
API_URL = "http://localhost:8080/api/convert"  # Adjust if needed
SPEED = 155  # Default speed
BENCHMARK_DIR = os.path.join(os.path.dirname(__file__), "benchmark")
RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results.csv")
MAX_WORKERS = 1  # Adjust based on your server capacity
TIMEOUT = 300  # 5 minutes timeout for larger files

# Ensure the benchmark directory exists
if not os.path.exists(BENCHMARK_DIR):
    raise FileNotFoundError(f"Benchmark directory not found: {BENCHMARK_DIR}")

def get_file_size_category(filepath):
    """Determine the file size category based on the directory name."""
    # Extract directory name from the filepath
    dir_name = os.path.basename(os.path.dirname(filepath))
    return dir_name

def convert_svg_file(filepath, speed=SPEED):
    """
    Send an SVG file to the conversion API and measure performance.
    
    Returns:
        dict: Results including success status, processing time, file size, etc.
    """
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath) / 1024  # Size in KB
    
    size_category = get_file_size_category(filepath)
    
    # Prepare the file and form data
    with open(filepath, 'rb') as f:
        file_data = {'svg_file': (filename, f, 'image/svg+xml')}
        form_data = {'speed': str(speed)}
        
        start_time = time.time()
        try:
            # Send the request to the API
            response = requests.post(
                API_URL, 
                files=file_data, 
                data=form_data,
                timeout=TIMEOUT
            )
            
            # Calculate total time including network latency
            total_time = time.time() - start_time
            
            # Parse the response
            if response.status_code == 200:
                result = response.json()
                # If API returns its own processing time, use that too
                api_time = result.get('processing_time', None)
                
                return {
                    'filename': filename,
                    'size_kb': filesize,
                    'size_category': size_category,
                    'total_time': total_time,
                    'api_time': api_time,
                    'success': result.get('success', False),
                    'status_code': response.status_code,
                    'message': result.get('message', None)
                }
            else:
                return {
                    'filename': filename,
                    'size_kb': filesize,
                    'size_category': size_category,
                    'total_time': total_time,
                    'api_time': None,
                    'success': False,
                    'status_code': response.status_code,
                    'message': f"HTTP Error: {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                'filename': filename,
                'size_kb': filesize,
                'size_category': size_category,
                'total_time': TIMEOUT,
                'api_time': None,
                'success': False,
                'status_code': None,
                'message': "Request timed out"
            }
            
        except Exception as e:
            return {
                'filename': filename,
                'size_kb': filesize,
                'size_category': size_category,
                'total_time': time.time() - start_time,
                'api_time': None,
                'success': False,
                'status_code': None,
                'message': str(e)
            }

def find_svg_files():
    """Find all SVG files in the benchmark directory."""
    svg_pattern = os.path.join(BENCHMARK_DIR, "**", "*.svg")
    return glob.glob(svg_pattern, recursive=True)

def run_benchmark(files=None, speed=SPEED):
    """
    Run the benchmark on all SVG files or a specified list.
    
    Args:
        files: List of file paths to benchmark. If None, all SVG files in the benchmark directory will be used.
        speed: Speed parameter to use for conversion.
        
    Returns:
        DataFrame containing the benchmark results.
    """
    if files is None:
        files = find_svg_files()
        
    if not files:
        print("No SVG files found for benchmarking")
        return pd.DataFrame()
    
    results = []
    
    print(f"Running benchmark on {len(files)} SVG files...")
    
    # If only one worker, use a simple loop with progress bar
    if MAX_WORKERS == 1:
        for filepath in tqdm(files, desc="Converting SVGs"):
            result = convert_svg_file(filepath, speed)
            results.append(result)
    else:
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks and get futures
            futures = [executor.submit(convert_svg_file, filepath, speed) for filepath in files]
            
            # Process results as they complete
            for future in tqdm(futures, desc="Converting SVGs"):
                result = future.result()
                results.append(result)
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    # Calculate additional statistics if we have results
    if not df.empty:
        # Sort by file size
        df = df.sort_values('size_kb')
        
        # Calculate success rate
        success_rate = df['success'].mean() * 100
        print(f"Overall success rate: {success_rate:.2f}%")
        
        # Print summary statistics by category
        print("\nPerformance by size category:")
        category_stats = df.groupby('size_category').agg({
            'total_time': ['mean', 'min', 'max', 'count'],
            'success': 'mean'
        })
        
        print(category_stats)
        
        # Save results to CSV
        df.to_csv(RESULTS_FILE, index=False)
        print(f"Results saved to {RESULTS_FILE}")
            
    return df

def plot_results(results_df):
    """Generate plots based on benchmark results."""
    if results_df.empty:
        print("No results to plot")
        return
    
    # Create a directory for plots if it doesn't exist
    plots_dir = os.path.join(os.path.dirname(__file__), "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # Plot 1: File size vs. Processing time
    plt.figure(figsize=(12, 6))
    successful = results_df[results_df['success'] == True]
    failed = results_df[results_df['success'] == False]
    
    plt.scatter(successful['size_kb'], successful['total_time'], 
                label='Successful', color='green', alpha=0.7)
    plt.scatter(failed['size_kb'], failed['total_time'], 
                label='Failed', color='red', alpha=0.7)
    
    plt.xscale('log')  # Log scale for file size
    plt.xlabel('File Size (KB)')
    plt.ylabel('Processing Time (seconds)')
    plt.title('SVG to Gcode Conversion Performance')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig(os.path.join(plots_dir, 'performance_by_size.png'))
    
    # Plot 2: Size category comparison
    plt.figure(figsize=(12, 6))
    category_times = results_df.groupby('size_category')['total_time'].mean()
    category_times.plot(kind='bar', color='skyblue')
    plt.xlabel('Size Category')
    plt.ylabel('Average Processing Time (seconds)')
    plt.title('Average Processing Time by Size Category')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig(os.path.join(plots_dir, 'performance_by_category.png'))
    
    print(f"Plots saved to {plots_dir}")

def main():
    """Main function to run the benchmark."""
    print("SVG to Gcode Conversion Benchmark")
    print("=" * 40)
    
    # Check if the API is available
    try:
        requests.get(API_URL.rsplit('/', 1)[0], timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to the API at {API_URL}")
        print("Make sure the Flask backend is running.")
        print("You can start it with 'docker-compose up' or by running Flask directly.")
        return
    except Exception as e:
        print(f"WARNING: API check failed: {e}")
        print("Continuing anyway...")
    
    # Run the benchmark
    results = run_benchmark()
    
    # Plot results if we have data
    if not results.empty:
        plot_results(results)

if __name__ == "__main__":
    main()