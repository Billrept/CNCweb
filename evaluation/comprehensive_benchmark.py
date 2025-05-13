#!/usr/bin/env python3
# Comprehensive benchmarking script that runs multiple tests and generates a report

import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from benchmark import run_benchmark, find_svg_files, BENCHMARK_DIR
from optimize_speed import optimize_speed
import argparse
from datetime import datetime
import json

def generate_report(results_df, speed_results_df=None, output_dir=None):
    """Generate a comprehensive HTML report of benchmark results."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(BENCHMARK_DIR), "benchmark_reports")
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(output_dir, f"report_{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    
    # Generate plots for the report
    plots_dir = os.path.join(report_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # 1. Size vs. Time plot
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=results_df, x='size_kb', y='total_time', hue='success', 
                    palette={True: 'green', False: 'red'}, alpha=0.7)
    plt.xscale('log')
    plt.xlabel('File Size (KB)')
    plt.ylabel('Processing Time (seconds)')
    plt.title('SVG to Gcode Conversion Performance')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plots_dir, 'size_vs_time.png'))
    
    # 2. Category Performance
    plt.figure(figsize=(12, 6))
    category_times = results_df.groupby('size_category')['total_time'].mean()
    category_times.plot(kind='bar', color='skyblue')
    plt.xlabel('Size Category')
    plt.ylabel('Average Processing Time (seconds)')
    plt.title('Average Processing Time by Size Category')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'category_performance.png'))
    
    # 3. Success Rate by Category
    plt.figure(figsize=(12, 6))
    success_rates = results_df.groupby('size_category')['success'].mean() * 100
    success_rates.plot(kind='bar', color='lightgreen')
    plt.xlabel('Size Category')
    plt.ylabel('Success Rate (%)')
    plt.title('Conversion Success Rate by Size Category')
    plt.xticks(rotation=45)
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'success_rate.png'))
    
    # 4. Generate speed optimization plots if data is available
    if speed_results_df is not None and not speed_results_df.empty:
        plt.figure(figsize=(12, 8))
        for category in speed_results_df['size_category'].unique():
            category_data = speed_results_df[speed_results_df['size_category'] == category]
            avg_times = category_data.groupby('speed')['total_time'].mean()
            plt.plot(avg_times.index, avg_times.values, marker='o', label=category)
        
        plt.xlabel('Speed Setting (mm/min)')
        plt.ylabel('Average Processing Time (seconds)')
        plt.title('Speed Optimization by File Size Category')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(plots_dir, 'speed_optimization.png'))
    
    # Create an HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SVG to Gcode Conversion Benchmark Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333366; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .plot-container {{ margin: 20px 0; }}
            .section {{ margin: 30px 0; border: 1px solid #eee; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>SVG to Gcode Conversion Benchmark Report</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="section">
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Files Tested</td>
                    <td>{len(results_df)}</td>
                </tr>
                <tr>
                    <td>Overall Success Rate</td>
                    <td>{results_df['success'].mean() * 100:.2f}%</td>
                </tr>
                <tr>
                    <td>Average Processing Time</td>
                    <td>{results_df['total_time'].mean():.2f} seconds</td>
                </tr>
                <tr>
                    <td>Size Categories</td>
                    <td>{', '.join(results_df['size_category'].unique())}</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>Performance by File Size</h2>
            <div class="plot-container">
                <img src="plots/size_vs_time.png" alt="Size vs Time Performance" style="max-width: 100%;">
            </div>
        </div>
        
        <div class="section">
            <h2>Performance by Category</h2>
            <div class="plot-container">
                <img src="plots/category_performance.png" alt="Category Performance" style="max-width: 100%;">
            </div>
        </div>
        
        <div class="section">
            <h2>Success Rate by Category</h2>
            <div class="plot-container">
                <img src="plots/success_rate.png" alt="Success Rate by Category" style="max-width: 100%;">
            </div>
        </div>
    """
    
    # Add speed optimization results if available
    if speed_results_df is not None and not speed_results_df.empty:
        html_report += f"""
        <div class="section">
            <h2>Speed Optimization</h2>
            <div class="plot-container">
                <img src="plots/speed_optimization.png" alt="Speed Optimization" style="max-width: 100%;">
            </div>
        </div>
        """
    
    # Add detailed results tables
    html_report += f"""
        <div class="section">
            <h2>Detailed Results</h2>
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Size (KB)</th>
                    <th>Category</th>
                    <th>Processing Time (s)</th>
                    <th>Success</th>
                </tr>
    """
    
    for _, row in results_df.sort_values(['size_category', 'size_kb']).iterrows():
        success_color = "green" if row['success'] else "red"
        html_report += f"""
                <tr>
                    <td>{row['filename']}</td>
                    <td>{row['size_kb']:.2f}</td>
                    <td>{row['size_category']}</td>
                    <td>{row['total_time']:.2f}</td>
                    <td style="color: {success_color};">{row['success']}</td>
                </tr>
        """
    
    html_report += """
            </table>
        </div>
    </body>
    </html>
    """
    
    # Write the HTML report
    report_path = os.path.join(report_dir, "benchmark_report.html")
    with open(report_path, 'w') as f:
        f.write(html_report)
    
    # Save the raw data
    results_df.to_csv(os.path.join(report_dir, "benchmark_results.csv"), index=False)
    if speed_results_df is not None and not speed_results_df.empty:
        speed_results_df.to_csv(os.path.join(report_dir, "speed_results.csv"), index=False)
    
    print(f"Report generated: {report_path}")
    return report_path

def run_comprehensive_benchmark(run_speed_tests=True, max_files_per_category=3, speeds=None):
    """Run a comprehensive benchmark including regular conversion and speed tests."""
    start_time = time.time()
    print("Starting comprehensive benchmark...")
    
    # 1. Run standard benchmark on all files
    results_df = run_benchmark()
    
    # 2. Run speed optimization if requested
    speed_results_df = None
    if run_speed_tests:
        if speeds is None:
            speeds = [100, 155, 200, 300, 400]
        
        print("\nRunning speed optimization tests...")
        speed_results_df = optimize_speed(max_files=max_files_per_category, speeds=speeds)
    
    # 3. Generate report
    report_path = generate_report(results_df, speed_results_df)
    
    total_time = time.time() - start_time
    print(f"Comprehensive benchmark completed in {total_time:.2f} seconds")
    
    return report_path

def main():
    parser = argparse.ArgumentParser(description='Run comprehensive SVG to Gcode conversion benchmarks')
    parser.add_argument('--skip-speed-tests', action='store_true', 
                        help='Skip speed optimization tests')
    parser.add_argument('--max-files', type=int, default=3,
                        help='Maximum number of files to test from each category for speed tests')
    parser.add_argument('--speeds', type=int, nargs='+', default=[100, 155, 200, 300, 400],
                        help='List of speeds to test for optimization')
    
    args = parser.parse_args()
    
    run_comprehensive_benchmark(
        run_speed_tests=not args.skip_speed_tests,
        max_files_per_category=args.max_files,
        speeds=args.speeds
    )

if __name__ == "__main__":
    main()
