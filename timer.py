#!/usr/bin/env python3
"""
Benchmark script for mandelbrot.py
Runs multiple scale factors, times each run, and fits a power law curve
"""

import subprocess
import time
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Scales to test
SCALES = [1, 2, 3, 4]

def run_mandelbrot(scale):
    """Run mandelbrot.py with given scale and return elapsed time"""
    print(f'\n{"="*60}')
    print(f'Running scale {scale}x...')
    print("="*60)
    
    start = time.time()
    
    # Run mandelbrot.py with scale as input
    process = subprocess.Popen(
        ['python3', 'mandelbrot.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Send scale factor
    process.stdin.write(f'{scale}\n')
    process.stdin.flush()
    
    # Monitor output and kill when web server starts
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        output_lines.append(line)
        print(line, end='')
        
        # Kill process once web server starts
        if 'Web server running at' in line or 'Opening browser to' in line:
            time.sleep(2)  # Give it 2 seconds to open browser
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            break
    
    elapsed = time.time() - start
    
    print(f'\nScale {scale}x completed in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)\n')
    
    return elapsed


def power_law(x, a, b):
    """Power law function: t = a * x^b"""
    return a * x**b


def main():
    print("Mandelbrot Benchmark Script")
    print("="*60)
    print(f"Will run scales: {SCALES}")
    print("This may take 10-15 minutes total...")
    print("="*60)
    
    # Run benchmarks
    results = []
    for scale in SCALES:
        try:
            elapsed = run_mandelbrot(scale)
            results.append((scale, elapsed))
        except KeyboardInterrupt:
            print("\n\nBenchmark interrupted by user!")
            if len(results) < 2:
                print("Need at least 2 data points for curve fitting. Exiting.")
                return
            print(f"Continuing with {len(results)} data points...")
            break
        except Exception as e:
            print(f"Error running scale {scale}x: {e}")
            continue
    
    if len(results) < 2:
        print("Not enough data points for curve fitting. Exiting.")
        return
    
    # Extract data
    scales = np.array([s for s, _ in results])
    times = np.array([t for _, t in results])
    
    # Print results table
    print('\n' + "="*60)
    print('RESULTS SUMMARY')
    print("="*60)
    print('Scale | Time (seconds) | Time (minutes)')
    print('-' * 45)
    for scale, t in results:
        print(f'{scale:5d} | {t:14.2f} | {t/60:13.2f}')
    
    # Fit power law curve
    print('\n' + "="*60)
    print('CURVE FITTING')
    print("="*60)
    
    try:
        params, covariance = curve_fit(power_law, scales, times)
        a, b = params
        
        print(f"\nBest fit: t = {a:.3f} × x^{b:.3f}")
        print(f"\nInterpretation:")
        if b < 1.5:
            print(f"  Sub-linear scaling (b={b:.2f}) - excellent efficiency!")
        elif b < 2.5:
            print(f"  Near-quadratic scaling (b={b:.2f}) - expected for pixel-based computation")
        else:
            print(f"  Super-quadratic scaling (b={b:.2f}) - potential bottleneck")
        
        # Predictions
        print(f"\nPredictions:")
        test_scales = [8, 10, 16, 20, 22]
        for test_scale in test_scales:
            predicted_time = power_law(test_scale, a, b)
            print(f"  {test_scale}x: {predicted_time/60:.1f} minutes ({predicted_time:.0f} seconds)")
        
        # Generate plot
        print("\nGenerating plot...")
        
        # Create fine-grained curve for plotting
        x_fit = np.linspace(min(scales), max(test_scales), 100)
        y_fit = power_law(x_fit, a, b)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(scales, times/60, s=100, c='red', zorder=5, label='Measured data')
        plt.plot(x_fit, y_fit/60, 'b-', linewidth=2, label=f'Fit: t = {a:.3f} × x^{b:.3f}')
        
        # Add predictions
        pred_scales = np.array(test_scales)
        pred_times = power_law(pred_scales, a, b)
        plt.scatter(pred_scales, pred_times/60, s=50, c='green', marker='^', 
                   zorder=4, label='Predictions', alpha=0.7)
        
        plt.xlabel('Scale Factor (x)', fontsize=12)
        plt.ylabel('Time (minutes)', fontsize=12)
        plt.title(f'Mandelbrot Runtime Scaling: t = {a:.3f} × x^{b:.3f}', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)
        plt.tight_layout()
        
        plot_filename = 'mandelbrot_timing.png'
        plt.savefig(plot_filename, dpi=150)
        print(f"Plot saved as: {plot_filename}")
        
        plt.show()
        
    except Exception as e:
        print(f"Error fitting curve: {e}")
        print("Raw data:")
        print(f"scales = {scales.tolist()}")
        print(f"times = {times.tolist()}")
    
    print("\n" + "="*60)
    print("Benchmark complete!")
    print("="*60)


if __name__ == '__main__':
    main()