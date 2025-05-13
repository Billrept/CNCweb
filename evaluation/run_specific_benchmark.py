#!/usr/bin/env python3
# Benchmark script for testing specific SVG files or categories

import os
import sys
import argparse
from benchmark import run_benchmark, plot_results, find_svg_files, BENCHMARK_DIR

def main():
    parser = argparse.ArgumentParser(description='Run SVG to Gcode conversion benchmarks on specific files or categories')
    parser.add_argument('--category', choices=['1-5KB', '20-200KB', '0.5-2MB'], 
                        help='Specific size category to benchmark')
    parser.add_argument('--file', help='Specific SVG file to benchmark (path relative to benchmark directory)')
    parser.add_argument('--speed', type=int, default=155, help='Speed parameter for conversion')
    parser.add_argument('--workers', type=int, default=1, help='Number of concurrent workers')
    parser.add_argument('--no-plot', action='store_true', help='Skip generating plots')
    
    args = parser.parse_args()
    
    files = None
    
    # Determine which files to benchmark
    if args.file:
        file_path = os.path.join(BENCHMARK_DIR, args.file)
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return 1
        files = [file_path]
        print(f"Running benchmark on single file: {args.file}")
    elif args.category:
        category_dir = os.path.join(BENCHMARK_DIR, args.category)
        if not os.path.exists(category_dir):
            print(f"Error: Category directory not found: {category_dir}")
            return 1
        files = [f for f in find_svg_files() if args.category in f]
        print(f"Running benchmark on category: {args.category} ({len(files)} files)")
    else:
        print("Running benchmark on all files")
        # Use default behavior of run_benchmark (all files)
    
    # Run the benchmark
    results = run_benchmark(files=files, speed=args.speed)
    
    # Plot results unless disabled
    if not args.no_plot and not results.empty:
        plot_results(results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
