# Kobo Comic Optimizer

Kobo Comic Optimizer is a command-line tool for optimizing comics and manga for Kobo eReaders, designed primarily for macOS and Apple Silicon.

It can process PDF, CBZ, CBR, ZIP, RAR, and folders containing images, then create optimized CBZ or PDF files.

## Features

- PDF support
- CBZ and ZIP support
- CBR and RAR support
- Folders containing images
- Multiple inputs at once
- Natural sorting for files and pages
- Single merged output or separate output files
- Parallel page processing in single-file mode
- Parallel file processing in separate-files mode
- Automatic image resizing
- Optimized JPEG conversion
- Configurable JPEG compression through presets
- Progress indicators and elapsed-time tracking
- Final output validation
- Automatic handling of `__MACOSX`, `.DS_Store`, and `._` files
- Automatic isolated Python environment through `.venv`
- Automatic installation of required Python dependencies

---

## Requirements

### System

Designed primarily for:

- macOS
- Apple Silicon

### Python

Python 3 is required.

The application automatically creates and uses an isolated Python virtual environment named:

```text
.venv
```

The folder is created next to the script on first launch.

### Python dependencies

When needed, the script automatically installs:

- PyMuPDF
- Pillow

You do not need to install them manually with `pip`.

Using a virtual environment also avoids macOS/Homebrew issues related to:

```text
externally-managed-environment
```

---

## Optional dependencies for CBR and RAR

To process:

- CBR
- RAR

at least one compatible archive extractor must be available on the system.

The script checks for these tools in this order:

```text
7zz
7z
unar
unrar
```

On macOS, for example, you can install `p7zip` with Homebrew:

```bash
brew install p7zip
```

Or:

```bash
brew install unar
```

These dependencies are required only for RAR and CBR archives.

---

## Getting started

Place the script in a folder:

```text
KoboComicOptimizer_v3.py
```

Make it executable:

```bash
chmod +x KoboComicOptimizer_v3.py
```

Run it with:

```bash
./KoboComicOptimizer_v3.py
```

Or:

```bash
python3 KoboComicOptimizer_v3.py
```

On first launch, the application:

1. creates `.venv`
2. checks the required dependencies
3. installs PyMuPDF and Pillow if missing
4. restarts itself inside the isolated environment

Dependencies are not reinstalled on later runs unless needed.

---

## Supported formats

### Input

Documents and archives:

- PDF
- CBZ
- CBR
- ZIP
- RAR

Images:

- JPG
- JPEG
- PNG
- WEBP
- BMP
- GIF
- TIFF
- AVIF

Folders containing images are also supported.

### Output

The application can create:

- CBZ
- PDF

#### CBZ

CBZ is generally the recommended format for comics and manga on Kobo devices.

Images are stored without additional ZIP compression because JPEG files are already compressed.

#### PDF

The application builds a PDF from the optimized images.

---

## Usage

At startup you can provide:

- one file
- multiple files
- one folder
- multiple folders

You can also drag files and folders directly into the Terminal window.

The application detects supported content automatically and shows the processing order before starting.

---

## Quick start

The main menu includes:

```text
1) QUICK START — ENTER
```

Default settings:

```text
Preset: Kobo Small
Maximum side: 1000 px
JPEG quality: 50
Output: CBZ
Mode: Single file
```

Press `ENTER` to use these settings immediately.

---

## Presets

### Kobo Small

```text
Maximum side: 1000 px
JPEG quality: 50
```

### Kobo Standard

```text
Maximum side: 1400 px
JPEG quality: 60
```

### High Quality

```text
Maximum side: 1800 px
JPEG quality: 75
```

### Maximum Quality

```text
Maximum side: 2400 px
JPEG quality: 85
```

---

## Output modes

### Single file

All selected sources are collected in natural order and merged into a single CBZ or PDF.

Sources are collected sequentially to preserve page and volume order. The resulting pages are then optimized in parallel.

Parallelism is therefore applied to pages, not to different volumes while they are being collected.

### Separate files

Each source generates its own output file.

In this mode, multiple comics can be processed at the same time. Each individual file uses one internal process to avoid excessive parallelism.

Parallelism is therefore applied across different comics.

---

## PDF processing

PDF files are converted with PyMuPDF.

Each page is rendered to an image using a controlled `1.4x` scale, then resized according to the selected preset.

---

## Image optimization

During processing, the application:

1. applies EXIF orientation
2. converts images to RGB
3. handles transparency with a white background
4. resizes images that exceed the preset's maximum side
5. saves the result as JPEG

JPEG settings:

```text
Subsampling: 4:2:0
Optimize: enabled
Progressive: enabled
```

---

## Progress indicators

During processing, the application shows:

- processed pages
- completion percentage
- elapsed time

Example:

```text
Processed: 80/132 (60.6%) - 00:24
```

---

## Final validation

After processing, the application validates the generated file.

### CBZ

The archive is checked to make sure it contains valid image files.

### PDF

The PDF is checked to make sure it can be opened and contains at least one page.

If validation fails, the output file is deleted and an error is reported.

---

## Output naming

Output files are normally created in the same folder as the source.

The filename uses the suffix:

```text
_kobo
```

Example:

```text
Manga.cbz
```

becomes:

```text
Manga_kobo.cbz
```

If that filename already exists:

```text
Manga_kobo_2.cbz
Manga_kobo_3.cbz
```

and so on.

---

## File size

The final file size mainly depends on:

- original image dimensions
- input format
- selected preset
- JPEG quality
- compression already present in the original source

In some cases, an optimized file can be larger than the original. This can happen when the original already uses very efficient compression or when already optimized images are re-encoded.

The application reports the final comparison:

```text
Original:  XX.XX MB
Final:     XX.XX MB
Reduction: XX.X%
```

A negative reduction means that the output is larger than the original.

---

## Cancelling

Press:

```text
CTRL + C
```

to stop processing.

---

## Folder structure

After the first run, the folder will look similar to:

```text
Kobo Comic Optimizer/
│
├── KoboComicOptimizer_v3.py
├── readme.md
└── .venv/
```

The `.venv` folder is created automatically and contains the isolated Python environment used by the application.

You do not need to modify it manually.

---

## Notes

Temporary files are created automatically during processing and removed when the operation finishes.

Unnecessary macOS files and folders such as:

```text
__MACOSX
.DS_Store
._
```

are ignored.

---

## Compatibility

Designed primarily for:

- macOS
- Apple Silicon
- Kobo
- KOReader

A compatible extractor is required for CBR and RAR files.
