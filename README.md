# Mandelbrot Set DeepZoom Generator

A high-performance, memory-efficient Mandelbrot set generator that creates interactive zoomable visualizations using the DeepZoom tile pyramid format. Optimized for extremely high-resolution rendering through parallel processing and streaming algorithms.

## Overview

This project originated as a homework assignment exploring parallel computing and image processing techniques. The original assignment focused on generating Mandelbrot set images in FITS and PNG formats. This standalone version extends that work with a complete DeepZoom implementation, enabling smooth interactive exploration of the fractal at arbitrary zoom levels.

**Original Assignment Features:**
- C++ extension for fast Mandelbrot computation
- Memory-mapped array processing for handling large images
- Multiprocessing with work queues
- FITS file output for scientific data
- Direct PNG generation

**What's New in This Version:**
- **Interactive DeepZoom viewer** with OpenSeadragon integration
- **Complete tile pyramid generation** with multiple zoom levels
- **Lanczos downsampling** for high-quality lower resolution tiles
- **Strip-by-strip streaming processing** to minimize peak storage usage
- **Automated web server** for instant visualization
- **User-configurable resolution** via interactive prompts
- **Optimized C++ image processing** for vertical flips and tile splitting
- **Progress tracking** with tqdm progress bars

## Files

- **`mandelbrot.py`** - Main generator with DeepZoom pipeline
- **`mandelbrot.cpp`** - C++ extension for Mandelbrot computation
- **`image_processor.cpp`** - C++ extension for image transformations
- **`Makefile`** - Build script for C++ extensions

## Output Structure

The generator creates:
- `mandelbrot_deepzoom_files/` - Tile pyramid directory containing PNG tiles organized by zoom level
- `mandelbrot_deepzoom.dzi` - DeepZoom descriptor (XML metadata)
- `mandelbrot_viewer.html` - Interactive web viewer
- Automatic browser launch with local web server on port 8000

## Quality of Life Features

### Interactive Scale Selection

When you run the generator, it will prompt you for a scale factor and show you:
- **Final resolution** in pixels
- **Estimated processing time** based on empirical measurements
- **Peak temporary storage** needed during processing
- **Final DeepZoom storage size** for the complete pyramid

This allows you to make an informed decision before starting the generation process. The estimates are calculated using power-law models fitted to actual benchmark data:

- **Processing time**: `t = 12.977 × scale^1.804` (in seconds)
- **Final storage**: `size = 9.58017 × scale^1.69713` (in MB)

### Performance & Storage Reference

**Default resolution is 4x (30,720 × 40,960 pixels)**

DeepZoom creates a pyramid with tiles at multiple zoom levels. The Mandelbrot set compresses extremely well due to large solid-color regions and smooth gradients, resulting in surprisingly small file sizes.

| Scale | Resolution | Processing Time* | Peak Temp Storage** | DeepZoom Storage*** |
|-------|------------|------------------|---------------------|------------------|
| 1x | 7,680 × 10,240 | ~13 sec | ~75 MB | ~10 MB |
| 2x | 15,360 × 20,480 | ~45 sec | ~150 MB | ~31 MB |
| 4x | 30,720 × 40,960 | ~3 min | ~300 MB | ~101 MB |
| 6x | 46,080 × 61,440 | ~6 min | ~450 MB | ~196 MB |
| 8x | 61,440 × 81,920 | ~11 min | ~600 MB | ~309 MB |
| 10x | 76,800 × 102,400 | ~17 min | ~750 MB | ~441 MB |
| 15x | 115,200 × 153,600 | ~44 min | ~1.1 GB | ~928 MB |
| 20x | 153,600 × 204,800 | ~80 min | ~1.5 GB | ~1.5 GB |
| 30x | 230,400 × 307,200 | ~3.2 hours | ~2.2 GB | ~3.2 GB |
| 40x | 307,200 × 409,600 | ~5.5 hours | ~3.0 GB | ~5.3 GB |
| 50x | 384,000 × 512,000 | ~8.5 hours | ~3.8 GB | ~7.8 GB |

*Processing time measured on an 8-core/16-thread system (11th gen Intel I7) with 16GB of ram and a PCIEgen4x4 NVME SSD at 750 iterations.

**Peak storage is just one horizontal strip worth of temporary `.npy` chunk files (~64 files × 256 pixels high), which are immediately deleted after tile generation. This streaming approach dramatically reduces peak storage compared to storing the entire raw image.

***Final storage past 20x is unverified.
### Progress Tracking

The generator provides real-time progress information:
- **Strip-by-strip progress** showing overall completion
- **Chunk processing within each strip** with nested progress bar
- **Pyramid level generation** with tile count tracking
- Clear visual indication of which phase is running

### Automatic Cleanup

Temporary files are deleted immediately after use:
- Chunk `.npy` files are removed as soon as each strip's tiles are generated
- Only the final DeepZoom pyramid and metadata files remain
- No manual cleanup required

## Requirements

### Python Packages
```bash
pip install numpy matplotlib pillow tqdm
```

### C++ Compiler
- GCC or Clang with C++11 support
- Python development headers

On Ubuntu/Debian:
```bash
sudo apt-get install python3-dev build-essential
```

On macOS (with Xcode Command Line Tools):
```bash
xcode-select --install
```

## Installation & Usage

### 1. Build the C++ Extensions
```bash
make
```

### 2. Run the Generator
```bash
python mandelbrot.py
```

You'll be prompted to enter an image scale factor (press Enter for default 4x). The generator will show you estimates for processing time, peak storage, and final file size before starting.

The generator will:
1. Process the image in horizontal strips (256 pixels high each)
   - For each strip: compute Mandelbrot chunks in parallel
   - Save temporary .npy files for the strip
   - Assemble strip and generate maximum resolution tiles
   - Delete temporary files immediately
2. Build the pyramid of downsampled zoom levels
3. Generate the HTML viewer
4. Launch a local web server and open your browser

### 3. Explore the Visualization

Use your mouse to:
- **Drag** to pan around the set
- **Scroll** to zoom in/out
- Navigate smoothly across zoom levels

Press **Ctrl+C** in the terminal to stop the web server when done.

## Configuration

Key parameters in `mandelbrot.py`:

```python
max_iter = 750              # Iteration limit for escape test
color_reference = 100       # Color normalization reference
im_scale = 4                # Resolution multiplier (prompt at runtime)
xmin, xmax = -2.5, 1.       # Real axis bounds
ymin, ymax = -1., 1.        # Imaginary axis bounds
ny, nx = im_scale*7680, im_scale*10240  # Final resolution

TILE_SIZE = 256             # Tile dimensions (256 or 512)
ncol = 64                   # Number of computation chunks per strip
```

### Tuning Tips

- **Higher resolution**: Increase `im_scale` when prompted (requires more time and storage)
- **Better detail at deep zoom**: Increase `max_iter` (750-1000 for high resolutions)
- **Faster processing**: Set `TILE_SIZE = 512` (fewer tiles but uses more memory per strip)
- **Lower memory per strip**: Reduce `ncol` (default: 64 chunks per strip)

## Technical Details

### Streaming Processing Pipeline

The generator uses a strip-by-strip streaming approach to minimize peak memory and storage usage:

1. **Strip Division**: Image is divided into horizontal strips of 256 pixels height
2. **Per-Strip Processing**:
   - Spawn worker processes for parallel Mandelbrot computation
   - Compute 64 vertical chunks covering the strip's height
   - Save chunks as temporary .npy files
   - Load chunks via memory-mapping (avoids loading entire chunks into RAM)
   - Assemble strip and generate tiles
   - Delete all temporary .npy files for the strip
3. **Next Strip**: Repeat for next 256-pixel horizontal strip
4. **Pyramid Building**: Generate downsampled zoom levels from completed tiles

**Key Benefits:**
- Peak storage is only ~64 chunks × 256 pixels instead of full image
- Memory usage remains constant regardless of total image size
- Temporary files exist for seconds rather than entire processing duration
- Enables rendering of extremely high resolution images on modest hardware

### Key Optimizations

**Memory Management:**
- Strip-by-strip processing with immediate cleanup
- Memory-mapped chunk files to avoid loading entire arrays
- Fresh worker processes per strip prevent memory leaks
- Controlled worker pool sizes to limit memory footprint

**Performance:**
- C++ extensions for compute-intensive operations
- Multiprocessing across all available CPU cores
- Batch processing for cache efficiency
- Progress tracking without performance impact

**Image Quality:**
- Lanczos-3 resampling for downsampled pyramid levels
- Smooth coloring algorithm to eliminate banding
- Custom colormap with perceptually smooth gradients

### Color Palette

The default colormap transitions through:
Dark purple → Deep blue → Cyan → Green → Yellow → Orange → Red → Gray

Colors are normalized to a reference iteration count for consistency across different `max_iter` values.

## Troubleshooting

**"Module not found" error:**
Run `make` to compile the C++ extensions.

**Out of memory:**
- Reduce `im_scale` 
- Reduce `ncol` (number of chunks per strip)
- Close other applications
- The streaming pipeline should handle most memory issues automatically

**Port 8000 already in use:**
The generator will show an error but you can manually run:
```bash
python3 -m http.server 8000
```
Then open `http://localhost:8000/mandelbrot_viewer.html`

**Slow performance:**
- Check CPU usage during computation phase (should be near 100%)
- Ensure SSD is used for temporary files (not network drive)
- Consider reducing resolution for initial tests
- Each strip spawns fresh workers, so slight overhead vs. single worker pool

## License

This project evolved from an academic assignment and is provided as-is for educational purposes.
