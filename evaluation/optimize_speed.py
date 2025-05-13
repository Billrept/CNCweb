#!/usr/bin/env python3
# Speed optimization benchmark for SVG to Gcode conversion

import os
import pandas as pd
import matplotlib.pyplot as plt
from benchmark import convert_svg_file, find_svg_files, BENCHMARK_DIR
import argparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def test_speeds(filepath, speeds):
    """Test a single file with multiple speed settings."""
    results = []
    
    for speed in tqdm(speeds, desc=f"Testing speeds for {os.path.basename(filepath)}"):
        result = convert_svg_file(filepath, speed)
        result['speed'] = speed
        results.append(result)
    
    return results

def optimize_speed(file_pattern=None, speeds=None, max_files=3):
    """
    Test multiple speed settings to find the optimal conversion speed.
    
    Args:
        file_pattern: A pattern to filter files (e.g., '20-200KB' for that size category)
        speeds: List of speeds to test (default is [100, 155, 200, 300, 400])
        max_files: Maximum number of files to test from each category
        
    Returns:
        DataFrame with the results
    """
    if speeds is None:
        speeds = [100, 155, 200, 300, 400]
    
    # Find files to test
    all_files = find_svg_files()
    
    if file_pattern:
        test_files = [f for f in all_files if file_pattern in f]
    else:
        test_files = all_files
    
    # Get a sample of files from each category to avoid testing too many
    categories = {}
    for f in test_files:
        category = os.path.basename(os.path.dirname(f))
        if category not in categories:
            categories[category] = []
        categories[category].append(f)
    
    # Limit files per category
    selected_files = []
    for category, files in categories.items():
        # Take the first few files from each category
        selected_files.extend(files[:max_files])
    
    if not selected_files:
        print("No matching files found for testing")
        return pd.DataFrame()
    
    print(f"Testing {len(selected_files)} files with {len(speeds)} different speed settings")
    
    # Run the tests
    all_results = []
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        # For each file, test all speeds
        futures = [executor.submit(test_speeds, f, speeds) for f in selected_files]
        
        for future in futures:
            file_results = future.result()
            all_results.extend(file_results)
    
    # Combine all results
    results_df = pd.DataFrame(all_results)
    
    # Save results
    output_file = os.path.join(os.path.dirname(BENCHMARK_DIR), "speed_optimization_results.csv")
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    
    # Analyze and plot
    if not results_df.empty:
        # Group by speed and calculate average processing time
        speed_stats = results_df.groupby(['speed', 'size_category']).agg({
            'total_time': ['mean', 'min', 'max', 'count'],
            'success': 'mean'
        }).reset_index()
        
        # Plot for each size category
        plots_dir = os.path.join(os.path.dirname(BENCHMARK_DIR), "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        for category in results_df['size_category'].unique():
            category_data = results_df[results_df['size_category'] == category]
            
            plt.figure(figsize=(10, 6))
            pivot_data = category_data.pivot_table(
                index='speed', 
                values='total_time', 
                aggfunc=['mean', 'min', 'max']
            )
            
            pivot_data.plot(kind='line', marker='o')
            plt.xlabel('Speed Setting (mm/min)')
            plt.ylabel('Processing Time (seconds)')
            plt.title(f'Speed Optimization for {category} Files')
            plt.grid(True, alpha=0.3)
            
            plt.savefig(os.path.join(plots_dir, f'speed_optimization_{category}.png'))
        
        # Combined plot for all categories
        plt.figure(figsize=(12, 8))
        for category in results_df['size_category'].unique():
            category_data = results_df[results_df['size_category'] == category]
            avg_times = category_data.groupby('speed')['total_time'].mean()
            plt.plot(avg_times.index, avg_times.values, marker='o', label=category)
        
        plt.xlabel('Speed Setting (mm/min)')
        plt.ylabel('Average Processing Time (seconds)')
        plt.title('Speed Optimization by File Size Category')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(os.path.join(plots_dir, 'speed_optimization_all.png'))
        print(f"Plots saved to {plots_dir}")
    
    return results_df

def main():
    parser = argparse.ArgumentParser(description='Optimize SVG to Gcode conversion speed')
    parser.add_argument('--pattern', help='Pattern to filter files (e.g., "20-200KB")')
    parser.add_argument('--speeds', type=int, nargs='+', default=[100, 155, 200, 300, 400],
                        help='List of speeds to test')
    parser.add_argument('--max-files', type=int, default=3,
                        help='Maximum number of files to test from each category')
    
    args = parser.parse_args()
    
    optimize_speed(args.pattern, args.speeds, args.max_files)

if __name__ == "__main__":
    main()
