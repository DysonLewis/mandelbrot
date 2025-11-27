# Mandelbrot Set Generator

A high-performance, memory-efficient Mandelbrot set generator with multiple output formats, developed through iterative optimization for handling extremely high-resolution images.

## Files

- **`hw8_fits.py`** - Generates FITS file and PNG output. Satisfies the homework guideline
- **`hw8_deepzoom.py`** - Can generate much higher resolution images, at the cost of storage and time
- **`mandelbrot.cpp`** - C++ extension for fast Mandelbrot computation
- **`Makefile`** - Builds the C++ extension module

## Approximate Image File Sizes

Scaled on base resolution of 7680 x 10240 (78.6 megapixels):

### FITS Pipeline (`hw8_fits.py`)
| Multiplier | Resolution | FITS Output | PNG Output |
|------------|------------|-------------|------------|
| 1x | 7,680 × 10,240 | ~700 MB | ~50-100 MB |
| 10x | 76,800 × 102,400 | ~70 GB | ~5-10 GB | (This will not run)

### DeepZoom Pipeline (`hw8_deepzoom.py`)

This was the only way I could get greater than around 5x resolution to work. Directly converting the FITS -> .png needed to load the entire file (even if it's processed in chunks)
This quickly eats up memory, also very difficult to open the .png file. It seemed to crash around 50% I tried to open it in an image viewing program.

**Default resolution for hw8_deepzoom.py is 4x** This should run and display the final image in ~5 minutes

**DeepZoom files are significantly larger than other formats** due to the pyramid structure generating tiles at multiple zoom levels.

| Multiplier | Resolution | Peak Storage* | Final Output |
|------------|------------|---------------|--------------|
| 1x | 7,680 × 10,240 | ~0.7 GB | ~0.6 GB |
| 10x | 76,800 × 102,400 | ~70 GB | ~58 GB |
| 20x | 153,600 × 204,800 | ~280 GB | ~233 GB |

*Peak storage includes temporary raw RGB file, intermediate TIFF, and final DeepZoom output during processing. After cleanup, only DeepZoom files remain.

**Storage breakdown per multiplier:**
- Raw RGB file: `(ny × nx × 3)` bytes (temporary, deleted after processing)
- TIFF file: ~30% of raw size (temporary, deleted after processing)  
- DeepZoom pyramid: ~25% of raw size (final output, permanent)

The max resolution I was able to test was 17x base, I would have gone higher but did not have the diskspace available (I need to clean my HST data lol), I think it took like 25 minutes to run on my machine.
## Evolution of the Implementation

### Stage 1: Original Assignment (`hw8_template.py`)
- Basic Python implementation using NumPy's vectorized operations
- Multiprocessing for parallel computation
- Direct FITS file output using memory-mapped arrays
- Limited resolution due to Python computation overhead

### Stage 2: RGB Chunked Processing (`hw8_fits.py`)
- Converted FITS data to RGB in chunks during write
- Allowed slightly higher resolutions by processing data incrementally
- Added PNG output with pyvips for memory-efficient conversion
- **Bottleneck**: Python-based Mandelbrot computation was still too slow for very high resolutions

### Stage 3: C++ Acceleration (`mandelbrot.cpp`)
- Implemented core Mandelbrot calculation in C++
- Following the pattern from hw1 (which used a C wrapper for computations)
- Used C++ because I'm slightly more comfortable with it
- Processes meshgrid arrays in batches for cache locality
- Still generates FITS file, then converts to PNG

### Stage 4: DeepZoom Optimization (`hw8_deepzoom.py`)
- Initially tried loading entire RGB raw file into memory - failed at high resolutions
- Switched to streaming architecture:
  1. Compute Mandelbrot -> Write RGB chunks to raw file (memory-mapped)
  2. Stream raw file -> TIFF with pyramid structure (tiled, compressed)
  3. Stream TIFF -> DeepZoom pyramid (individual tile files)
- **Bottleneck**: Each intermediate file took significant disk space and processing time

### Stage 5: Direct RGB Pipeline (`hw8_deepzoom.py` - Final)
- Eliminated FITS generation entirely
- Direct pipeline: Mandelbrot computation -> RGB conversion -> Memory-mapped raw file -> DeepZoom
- Removed unnecessary intermediate TIFF conversion
- Maximum memory efficiency(I think?): processes everything in small chunks
- This was about as good as I can optimize for memory, most of it was spent searching on how to un-cook my ram usage, then how to use the libraries, and then waiting for it to run.


## Requirements

```bash
# Python packages
pip install numpy astropy pyvips matplotlib

# System libraries (for pyvips)
# Ubuntu/Debian:
sudo apt-get install libvips-dev

# macOS:
brew install vips
```

## Usage

### Build the C++ Extension
```bash
make
```

### Generate FITS + PNG
```bash
python hw8_fits.py
```
Outputs:
- `output.fits` - Raw iteration count data
- `mandelbrot.png` - Colored visualization

### Generate Interactive DeepZoom Viewer
```bash
python hw8_deepzoom.py
```
Outputs:
- `mandelbrot_deepzoom_files/` - Tile pyramid directory
- `mandelbrot_deepzoom.dzi` - DeepZoom descriptor
- `mandelbrot_viewer.html` - Interactive web viewer
- Automatically opens in browser with local web server

## Key Optimizations

### Memory Management
- **Memory-mapped arrays**: Never load full images into RAM
- **Chunked processing**: Process data in small column/row strips
- **Streaming conversions**: Read from one file while writing to another
- **Immediate cleanup**: Delete intermediate data and call garbage collector

### Performance
- **C++ computation**: Core algorithm runs at compiled speeds
- **Multiprocessing**: Parallelizes work across all CPU cores
- **Batch processing**: Improves cache locality in tight loops
- **Queue management**: Limits queue size to prevent memory buildup

### Disk Usage
- **Direct pipelines**: Minimize intermediate files
- **Compressed formats**: Use deflate compression for TIFF, PNG tiles for DeepZoom
- **Cleanup**: Remove temporary files immediately after use

## Configuration

Edit parameters at the top of `hw8_deepzoom.py` or `hw8_fits.py`:

```python
max_iter = 300          # Iteration limit
xmin, xmax = -2.5, 1.   # X-axis domain
ymin, ymax = -1., 1.    # Y-axis domain
ny, nx = 7680, 10240    # Resolution (height, width)
ncol = 64               # Columns per chunk
```
At base resolution, max_iter = 100 is fine, above 10x consider bumping it to ~500.
For extreme resolutions (100+ megapixels), increase `ncol` to reduce queue overhead.