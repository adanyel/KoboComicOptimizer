#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
============================================================
KOBO COMIC OPTIMIZER
macOS / Apple Silicon

Input:
- PDF
- CBZ / CBR
- ZIP / RAR
- Folders containing images

Output:
- CBZ
- PDF

Features:
- Automatic isolated Python environment (.venv)
- Automatic PyMuPDF + Pillow setup
- Quick start with ENTER
- Custom settings menu
- Back navigation
- Single file: pages optimized in parallel
- Separate files: comics processed in parallel
- Automatic smart compression
- Timer and progress indicators
- Final validation
============================================================
"""

import os
import sys
import re
import shutil
import zipfile
import tempfile
import subprocess
import multiprocessing as mp
import threading

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import time, sleep


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "Kobo Comic Optimizer"

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
VENV_DIR = SCRIPT_DIR / ".venv"

if sys.platform == "win32":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python3"


PRESETS = {
    "1": {
        "name": "Kobo Small",
        "max_side": 1000,
        "quality": 50,
    },
    "2": {
        "name": "Kobo Standard",
        "max_side": 1400,
        "quality": 60,
    },
    "3": {
        "name": "High Quality",
        "max_side": 1800,
        "quality": 75,
    },
    "4": {
        "name": "Maximum Quality",
        "max_side": 2400,
        "quality": 85,
    },
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".avif",
}


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".cbz",
    ".cbr",
    ".zip",
    ".rar",
}


IGNORE_NAMES = {
    ".ds_store",
    "thumbs.db",
}


IGNORE_FOLDERS = {
    "__macosx",
    ".git",
}


# ============================================================
# ISOLATED PYTHON ENVIRONMENT
# ============================================================

def running_inside_venv():

    return (
        getattr(sys, "base_prefix", sys.prefix)
        != sys.prefix
    )


def ensure_virtual_environment():

    if running_inside_venv():
        return

    print()
    print("=" * 60)
    print(APP_NAME)
    print("=" * 60)
    print()
    print("Checking Python environment...")

    try:

        if not VENV_PYTHON.exists():

            print("Creating isolated Python environment...")

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(VENV_DIR),
                ],
                check=True,
            )

        check = subprocess.run(
            [
                str(VENV_PYTHON),
                "-c",
                "import pymupdf; from PIL import Image",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if check.returncode != 0:

            print("Installing required dependencies...")

            subprocess.run(
                [
                    str(VENV_PYTHON),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "pip",
                ],
                check=True,
            )

            subprocess.run(
                [
                    str(VENV_PYTHON),
                    "-m",
                    "pip",
                    "install",
                    "PyMuPDF",
                    "Pillow",
                ],
                check=True,
            )

        print("✓ Environment ready.")
        print()
        print("Starting application...")
        print()

        os.execv(
            str(VENV_PYTHON),
            [
                str(VENV_PYTHON),
                str(SCRIPT_PATH),
            ] + sys.argv[1:],
        )

    except Exception as error:

        print()
        print("PYTHON CONFIGURATION ERROR")
        print()
        print(error)

        input("\nPress ENTER to close...")
        sys.exit(1)


ensure_virtual_environment()


# ============================================================
# IMPORT DEPENDENCIES
# ============================================================

try:

    import pymupdf

    from PIL import (
        Image,
        ImageOps,
    )

except ImportError as error:

    print()
    print("ERROR: unable to load dependencies.")
    print(error)

    input("\nPress ENTER to close...")
    sys.exit(1)


# ============================================================
# UTILITIES
# ============================================================

def clear():

    os.system("cls" if os.name == "nt" else "clear")


def line(character="=", length=60):

    print(character * length)


def header(text):

    print()
    line()
    print(text)
    line()
    print()


def pause():

    input("\nPress ENTER to continue...")


def format_size(size):

    size = float(size)

    for unit in ["B", "KB", "MB", "GB", "TB"]:

        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PB"


def format_time(seconds):

    seconds = int(seconds)

    minutes = seconds // 60
    seconds = seconds % 60

    if minutes >= 60:

        hours = minutes // 60
        minutes = minutes % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return f"{minutes:02d}:{seconds:02d}"


def natural_key(value):

    return [
        int(part)
        if part.isdigit()
        else part.lower()
        for part in re.split(r"(\d+)", str(value))
    ]


def is_ignored(path):

    path = Path(path)

    if path.name.lower() in IGNORE_NAMES:
        return True

    for part in path.parts:

        if part.lower() in IGNORE_FOLDERS:
            return True

        if part.startswith("._"):
            return True

    return False


def file_size(path):

    try:
        return Path(path).stat().st_size
    except Exception:
        return 0


# ============================================================
# TIMER
# ============================================================

def spinner_worker(stop_event, start, label):

    symbols = ["|", "/", "-", "\\"]
    index = 0

    while not stop_event.is_set():

        elapsed = format_time(time() - start)

        print(
            f"\r{symbols[index % 4]} "
            f"{label}... "
            f"{elapsed}",
            end="",
            flush=True,
        )

        index += 1
        sleep(0.2)


def start_spinner(label):

    stop_event = threading.Event()
    start = time()

    thread = threading.Thread(
        target=spinner_worker,
        args=(stop_event, start, label),
        daemon=True,
    )

    thread.start()

    return stop_event, start, thread


def stop_spinner(stop_event, start, thread):

    stop_event.set()
    thread.join(timeout=1)

    elapsed = format_time(time() - start)

    print(
        f"\r✓ Completed in {elapsed}                    "
    )


# ============================================================
# INPUT
# ============================================================

def normalize_dragged_arguments(arguments):

    results = []

    for item in arguments:

        if not item:
            continue

        item = str(item).strip()

        if item.startswith("'") and item.endswith("'"):
            item = item[1:-1]

        if item.startswith('"') and item.endswith('"'):
            item = item[1:-1]

        results.append(
            Path(os.path.expanduser(item))
        )

    return results


def collect_paths_from_input():

    if len(sys.argv) > 1:

        return normalize_dragged_arguments(
            sys.argv[1:]
        )

    header("DRAG FILES OR FOLDERS")

    print("You can drag:")
    print()
    print("• PDF")
    print("• CBZ / CBR")
    print("• ZIP / RAR")
    print("• Folders")
    print("• Multiple items at once")
    print()

    raw = input(
        "Drag files or folders here and press ENTER:\n> "
    ).strip()

    if not raw:
        return []

    import shlex

    try:
        parts = shlex.split(raw)
    except Exception:
        parts = [raw]

    return normalize_dragged_arguments(parts)


def expand_folder(folder):

    results = []
    image_found = False

    for root, dirs, files in os.walk(folder):

        dirs[:] = [
            directory
            for directory in dirs
            if directory.lower()
            not in IGNORE_FOLDERS
            and not directory.startswith("._")
        ]

        for filename in files:

            path = Path(root) / filename

            if is_ignored(path):
                continue

            suffix = path.suffix.lower()

            if suffix in SUPPORTED_EXTENSIONS:
                results.append(path)

            if suffix in IMAGE_EXTENSIONS:
                image_found = True

    if image_found:
        results.append(Path(folder))

    unique = []
    seen = set()

    for path in results:

        key = str(path.resolve())

        if key not in seen:
            seen.add(key)
            unique.append(path)

    return unique


def expand_inputs(paths):

    results = []

    for path in paths:

        if not path.exists():

            print(f"WARNING: not found: {path}")
            continue

        if path.is_dir():

            results.extend(
                expand_folder(path)
            )

        elif (
            path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        ):

            results.append(path)

    unique = []
    seen = set()

    for path in results:

        key = str(path.resolve())

        if key not in seen:
            seen.add(key)
            unique.append(path)

    unique.sort(
        key=lambda item: natural_key(item.name)
    )

    return unique


# ============================================================
# MENU
# ============================================================

def ask_main_menu():

    while True:

        clear()

        header(APP_NAME)

        print("RECOMMENDED DEFAULTS")
        print()
        print("Preset: Kobo Small")
        print("Maximum side: 1000 px")
        print("JPEG quality: 50")
        print("Output: CBZ")
        print("Mode: Single file")
        print("Smart compression: ENABLED")
        print()

        print("1) QUICK START — ENTER")
        print("2) Customize")
        print("0) Exit")
        print()

        choice = input("Choice [1]: ").strip()

        if choice in ("", "1"):

            return {
                "preset": PRESETS["1"],
                "output": "CBZ",
                "mode": "single",
            }

        if choice == "2":

            settings = custom_menu()

            if settings:
                return settings

        if choice == "0":
            return None


def custom_menu():

    # PRESET

    while True:

        clear()
        header("CUSTOMIZE — PRESET")

        for key, preset in PRESETS.items():

            print(
                f"{key}) {preset['name']} — "
                f"{preset['max_side']} px / "
                f"JPEG {preset['quality']}"
            )

        print()
        print("0) Back")

        choice = input("\nPreset [1]: ").strip()

        if choice == "0":
            return None

        if choice == "":
            choice = "1"

        if choice in PRESETS:

            preset = PRESETS[choice]
            break

    # OUTPUT

    while True:

        clear()
        header("CUSTOMIZE — FORMAT")

        print("1) CBZ — recommended")
        print("2) PDF")
        print()
        print("0) Back")

        choice = input("\nFormat [1]: ").strip()

        if choice == "0":
            return custom_menu()

        if choice in ("", "1"):
            output = "CBZ"
            break

        if choice == "2":
            output = "PDF"
            break

    # MODE

    while True:

        clear()
        header("CUSTOMIZE — MODE")

        print("1) Single file")
        print("2) Separate files")
        print()
        print("0) Back")

        choice = input("\nMode [1]: ").strip()

        if choice == "0":
            return custom_menu()

        if choice in ("", "1"):
            mode = "single"
            break

        if choice == "2":
            mode = "separate"
            break

    return {
        "preset": preset,
        "output": output,
        "mode": mode,
    }


# ============================================================
# ARCHIVES
# ============================================================

def find_archive_extractor():

    for command in [
        "7zz",
        "7z",
        "unar",
        "unrar",
    ]:

        if shutil.which(command):
            return command

    return None


def extract_zip(source, destination):

    with zipfile.ZipFile(source, "r") as archive:

        members = []

        for member in archive.infolist():

            if member.is_dir():
                continue

            path = Path(member.filename)

            if is_ignored(path):
                continue

            if path.suffix.lower() in IMAGE_EXTENSIONS:
                members.append(member)

        members.sort(
            key=lambda item:
            natural_key(item.filename)
        )

        for index, member in enumerate(members, 1):

            suffix = (
                Path(member.filename)
                .suffix
                .lower()
            )

            target = (
                destination /
                f"{index:06d}{suffix}"
            )

            with archive.open(member) as source_file:

                with open(target, "wb") as target_file:

                    shutil.copyfileobj(
                        source_file,
                        target_file,
                    )


def extract_rar(source, destination):

    extractor = find_archive_extractor()

    if not extractor:

        raise RuntimeError(
            "RAR/CBR is not supported: "
            "install 'unar' or '7zip'."
        )

    if extractor in ("7z", "7zz"):

        command = [
            extractor,
            "x",
            "-y",
            f"-o{destination}",
            str(source),
        ]

    elif extractor == "unar":

        command = [
            extractor,
            "-quiet",
            "-force-overwrite",
            "-output-directory",
            str(destination),
            str(source),
        ]

    else:

        command = [
            extractor,
            "x",
            "-o+",
            str(source),
            str(destination),
        ]

    stop_event, start, thread = start_spinner(
        "Extracting archive"
    )

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    stop_spinner(
        stop_event,
        start,
        thread,
    )

    if result.returncode != 0:

        raise RuntimeError(
            result.stderr
            or "RAR extraction error."
        )


# ============================================================
# PDF
# ============================================================

def extract_pdf(source, destination, max_side):

    print()
    print(f"Processing PDF: {source.name}")

    document = pymupdf.open(str(source))

    total = len(document)

    # Controlled rendering.
    # Avoids huge PNG files with Matrix(2,2).

    zoom = 1.4

    matrix = pymupdf.Matrix(
        zoom,
        zoom,
    )

    stop_event, start, thread = start_spinner(
        "Rendering PDF"
    )

    for index in range(total):

        page = document.load_page(index)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        output = (
            destination /
            f"{index + 1:06d}.jpg"
        )

        pix.save(str(output))

    stop_spinner(
        stop_event,
        start,
        thread,
    )

    document.close()

    print(f"✓ Rendered {total} pages.")


# ============================================================
# FOLDERS / IMAGES
# ============================================================

def copy_images_from_folder(
    source,
    destination,
):

    images = []

    for root, dirs, files in os.walk(source):

        dirs[:] = [
            directory
            for directory in dirs
            if directory.lower()
            not in IGNORE_FOLDERS
        ]

        for filename in files:

            path = Path(root) / filename

            if is_ignored(path):
                continue

            if (
                path.suffix.lower()
                in IMAGE_EXTENSIONS
            ):

                images.append(path)

    images.sort(
        key=lambda item:
        natural_key(
            str(item.relative_to(source))
        )
    )

    for index, image in enumerate(images, 1):

        target = (
            destination /
            f"{index:06d}"
            f"{image.suffix.lower()}"
        )

        shutil.copy2(image, target)


def find_images(folder):

    images = []

    for root, dirs, files in os.walk(folder):

        dirs[:] = [
            directory
            for directory in dirs
            if directory.lower()
            not in IGNORE_FOLDERS
        ]

        for filename in files:

            path = Path(root) / filename

            if is_ignored(path):
                continue

            if (
                path.suffix.lower()
                in IMAGE_EXTENSIONS
            ):

                images.append(path)

    images.sort(
        key=lambda item:
        natural_key(str(item))
    )

    return images


def extract_source(
    source,
    destination,
    max_side,
):

    suffix = source.suffix.lower()

    if source.is_dir():

        copy_images_from_folder(
            source,
            destination,
        )

        return

    if suffix == ".pdf":

        extract_pdf(
            source,
            destination,
            max_side,
        )

        return

    if suffix in (".cbz", ".zip"):

        extract_zip(
            source,
            destination,
        )

        return

    if suffix in (".cbr", ".rar"):

        extract_rar(
            source,
            destination,
        )

        return

    raise RuntimeError(
        f"Unsupported format: {source}"
    )


# ============================================================
# IMAGE OPTIMIZATION
# ============================================================

def process_image_task(task):

    source, destination, max_side, quality = task

    try:

        with Image.open(source) as image:

            image = ImageOps.exif_transpose(image)

            if image.mode in ("RGBA", "LA"):

                background = Image.new(
                    "RGB",
                    image.size,
                    "white",
                )

                alpha = image.getchannel("A")

                background.paste(
                    image,
                    mask=alpha,
                )

                image = background

            elif image.mode != "RGB":

                image = image.convert("RGB")

            width, height = image.size

            longest = max(width, height)

            if longest > max_side:

                ratio = max_side / longest

                new_size = (
                    max(
                        1,
                        int(width * ratio),
                    ),
                    max(
                        1,
                        int(height * ratio),
                    ),
                )

                image = image.resize(
                    new_size,
                    Image.Resampling.LANCZOS,
                )

            image.save(
                destination,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling="4:2:0",
            )

        return True, ""

    except Exception as error:

        return False, (
            f"{source}: {error}"
        )


def optimize_images(
    images,
    output_folder,
    max_side,
    quality,
    workers,
):

    total = len(images)

    if total == 0:

        raise RuntimeError(
            "No images found."
        )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        f"Pages found: {total}"
    )

    print()

    if workers > 1:

        print(
            f"Parallel processesng "
            f"({workers} processes)..."
        )

    else:

        print("Processing...")

    start = time()

    tasks = []

    for index, image in enumerate(images, 1):

        output = (
            output_folder /
            f"{index:06d}.jpg"
        )

        tasks.append(
            (
                str(image),
                str(output),
                max_side,
                quality,
            )
        )

    completed = 0
    errors = []

    if workers <= 1:

        for task in tasks:

            ok, message = process_image_task(task)

            completed += 1

            if not ok:
                errors.append(message)

            print(
                f"\rProcessed: "
                f"{completed}/{total} "
                f"({completed / total * 100:.1f}%) "
                f"- {format_time(time() - start)}",
                end="",
                flush=True,
            )

    else:

        with ProcessPoolExecutor(
            max_workers=workers
        ) as executor:

            futures = [
                executor.submit(
                    process_image_task,
                    task,
                )
                for task in tasks
            ]

            for future in as_completed(futures):

                ok, message = future.result()

                completed += 1

                if not ok:
                    errors.append(message)

                print(
                    f"\rProcessed: "
                    f"{completed}/{total} "
                    f"({completed / total * 100:.1f}%) "
                    f"- {format_time(time() - start)}",
                    end="",
                    flush=True,
                )

    print()

    if errors:

        raise RuntimeError(
            errors[0]
        )

    return find_images(output_folder)


# ============================================================
# OUTPUT
# ============================================================

def create_cbz(images, output_file):

    print()
    print("Creating CBZ...")

    stop_event, start, thread = start_spinner(
        "Creating archive"
    )

    with zipfile.ZipFile(
        output_file,
        "w",
        compression=zipfile.ZIP_STORED,
    ) as archive:

        for index, image in enumerate(images, 1):

            archive.write(
                image,
                arcname=f"{index:06d}.jpg",
            )

    stop_spinner(
        stop_event,
        start,
        thread,
    )


def create_pdf(images, output_file):

    print()
    print("Creating PDF...")

    pil_images = []

    stop_event, start, thread = start_spinner(
        "Creating PDF"
    )

    try:

        for image_path in images:

            image = (
                Image.open(image_path)
                .convert("RGB")
            )

            pil_images.append(
                image.copy()
            )

            image.close()

        first = pil_images[0]

        first.save(
            output_file,
            "PDF",
            save_all=True,
            append_images=pil_images[1:],
            resolution=100.0,
        )

    finally:

        stop_spinner(
            stop_event,
            start,
            thread,
        )

        for image in pil_images:

            try:
                image.close()
            except Exception:
                pass


def build_output(
    images,
    output_file,
    output_type,
):

    if output_type == "CBZ":

        create_cbz(
            images,
            output_file,
        )

    else:

        create_pdf(
            images,
            output_file,
        )


# ============================================================
# VALIDATION
# ============================================================

def verify_cbz(path):

    try:

        with zipfile.ZipFile(
            path,
            "r",
        ) as archive:

            bad = archive.testzip()

            images = [
                name
                for name in archive.namelist()
                if Path(name).suffix.lower()
                in IMAGE_EXTENSIONS
            ]

            return (
                bad is None
                and len(images) > 0,
                len(images),
            )

    except Exception:

        return False, 0


def verify_pdf(path):

    try:

        document = pymupdf.open(
            str(path)
        )

        pages = len(document)

        document.close()

        return pages > 0, pages

    except Exception:

        return False, 0


def verify_output(
    path,
    output_type,
):

    if output_type == "CBZ":

        return verify_cbz(path)

    return verify_pdf(path)


# ============================================================
# SMART COMPRESSION
# ============================================================

def optimize_with_smart_compression(
    images,
    temporary_root,
    preset,
    output_type,
    workers,
    original_size,
):

    header("STANDARD OPTIMIZATION")

    standard_dir = (
        temporary_root /
        "optimized_standard"
    )

    standard_images = optimize_images(
        images,
        standard_dir,
        preset["max_side"],
        preset["quality"],
        workers,
    )

    extension = (
        ".cbz"
        if output_type == "CBZ"
        else ".pdf"
    )

    standard_output = (
        temporary_root /
        f"standard{extension}"
    )

    build_output(
        standard_images,
        standard_output,
        output_type,
    )

    standard_size = file_size(
        standard_output
    )

    best_output = standard_output
    best_size = standard_size

    # ========================================================
    # IF THE RESULT IS LARGER,
    # AUTOMATICALLY TRY A MORE COMPACT VERSION
    # ========================================================

    if (
        original_size > 0
        and standard_size > original_size
    ):

        header(
            "ADDITIONAL SMART COMPRESSION"
        )

        print(
            "The standard result is larger "
            "than the original."
        )

        print(
            "Automatically trying a "
            "more compact version..."
        )

        aggressive_quality = max(
            35,
            preset["quality"] - 12,
        )

        aggressive_side = max(
            800,
            preset["max_side"] - 150,
        )

        aggressive_dir = (
            temporary_root /
            "optimized_compact"
        )

        aggressive_images = optimize_images(
            images,
            aggressive_dir,
            aggressive_side,
            aggressive_quality,
            workers,
        )

        aggressive_output = (
            temporary_root /
            f"compact{extension}"
        )

        build_output(
            aggressive_images,
            aggressive_output,
            output_type,
        )

        aggressive_size = file_size(
            aggressive_output
        )

        print()
        print(
            f"Standard: {format_size(standard_size)}"
        )

        print(
            f"Compact:  {format_size(aggressive_size)}"
        )

        if aggressive_size < best_size:

            best_output = aggressive_output
            best_size = aggressive_size

            print()
            print(
                "✓ Automatically selected "
                "the more compact version."
            )

        else:

            print()
            print(
                "✓ The standard version "
                "remains the best option."
            )

    return best_output, best_size


# ============================================================
# OUTPUT PATH
# ============================================================

def safe_output_path(
    directory,
    base_name,
    extension,
):

    output = (
        directory /
        f"{base_name}_kobo{extension}"
    )

    counter = 2

    while output.exists():

        output = (
            directory /
            f"{base_name}_kobo_"
            f"{counter}{extension}"
        )

        counter += 1

    return output


# ============================================================
# SINGLE SOURCE PROCESSING
# ============================================================

def process_single_source(
    source,
    preset,
    output_type,
    page_workers=1,
):

    start = time()

    original_size = file_size(source)

    with tempfile.TemporaryDirectory(
        prefix="kobo_comic_"
    ) as temporary:

        temporary_root = Path(temporary)

        source_folder = (
            temporary_root /
            "source"
        )

        source_folder.mkdir()

        extract_source(
            source,
            source_folder,
            preset["max_side"],
        )

        images = find_images(
            source_folder
        )

        if not images:

            raise RuntimeError(
                f"No images found in "
                f"{source.name}"
            )

        best_output, best_size = (
            optimize_with_smart_compression(
                images,
                temporary_root,
                preset,
                output_type,
                page_workers,
                original_size,
            )
        )

        extension = (
            ".cbz"
            if output_type == "CBZ"
            else ".pdf"
        )

        output = safe_output_path(
            source.parent,
            source.stem,
            extension,
        )

        shutil.copy2(
            best_output,
            output,
        )

        valid, pages = verify_output(
            output,
            output_type,
        )

        if not valid:

            try:
                output.unlink()
            except Exception:
                pass

            raise RuntimeError(
                "Invalid output file."
            )

    return {
        "source": source,
        "output": output,
        "pages": pages,
        "time": time() - start,
        "original_size": original_size,
        "final_size": file_size(output),
    }


# ============================================================
# SINGLE FILE
# ============================================================

def process_merged(
    files,
    preset,
    output_type,
    page_workers,
):

    start = time()

    first = files[0]

    original_size = sum(
        file_size(file)
        for file in files
        if file.is_file()
    )

    extension = (
        ".cbz"
        if output_type == "CBZ"
        else ".pdf"
    )

    if len(files) == 1:

        base_name = first.stem

    else:

        base_name = (
            f"{first.stem}_and_other_"
            f"{len(files)}_volumes"
        )

    output = safe_output_path(
        first.parent,
        base_name,
        extension,
    )

    with tempfile.TemporaryDirectory(
        prefix="kobo_merge_"
    ) as temporary:

        temporary_root = Path(temporary)

        all_source = (
            temporary_root /
            "all_source"
        )

        all_source.mkdir()

        global_index = 1

        header("CREATING SINGLE FILE")

        print(
            "Files are collected in order."
        )

        print(
            "Pages are optimized "
            "in parallel."
        )

        for file_index, source in enumerate(
            files,
            1,
        ):

            print()
            line("-")

            print(
                f"{file_index}/{len(files)} — "
                f"{source.name}"
            )

            line("-")

            source_temp = (
                temporary_root /
                f"source_{file_index:04d}"
            )

            source_temp.mkdir()

            extract_source(
                source,
                source_temp,
                preset["max_side"],
            )

            images = find_images(
                source_temp
            )

            if not images:

                raise RuntimeError(
                    f"No pages found in "
                    f"{source.name}"
                )

            for image in images:

                target = (
                    all_source /
                    f"{global_index:08d}"
                    f"{image.suffix.lower()}"
                )

                shutil.copy2(
                    image,
                    target,
                )

                global_index += 1

        all_images = find_images(
            all_source
        )

        best_output, best_size = (
            optimize_with_smart_compression(
                all_images,
                temporary_root,
                preset,
                output_type,
                page_workers,
                original_size,
            )
        )

        shutil.copy2(
            best_output,
            output,
        )

        valid, pages = verify_output(
            output,
            output_type,
        )

        if not valid:

            raise RuntimeError(
                "The output file is invalid."
            )

    return {
        "output": output,
        "pages": pages,
        "time": time() - start,
        "original_size": original_size,
        "final_size": file_size(output),
    }


# ============================================================
# SEPARATE FILES
# ============================================================

def separate_worker(arguments):

    source_string, preset, output_type = arguments

    return process_single_source(
        Path(source_string),
        preset,
        output_type,
        page_workers=1,
    )


def process_separate(
    files,
    preset,
    output_type,
):

    cpu_count = os.cpu_count() or 4

    workers = min(
        3,
        max(1, cpu_count // 3),
        len(files),
    )

    header("CREATING SEPARATE FILES")

    print(f"File: {len(files)}")
    print(
        f"Elaborazione parallela: "
        f"{workers} processes"
    )

    start = time()

    tasks = [
        (
            str(source),
            preset,
            output_type,
        )
        for source in files
    ]

    results = []
    errors = []
    completed = 0

    if workers == 1:

        for task in tasks:

            try:

                result = separate_worker(
                    task
                )

                results.append(result)

            except Exception as error:

                errors.append(str(error))

            completed += 1

            print(
                f"\rCompleted: "
                f"{completed}/{len(files)}",
                end="",
                flush=True,
            )

    else:

        with ProcessPoolExecutor(
            max_workers=workers
        ) as executor:

            futures = [
                executor.submit(
                    separate_worker,
                    task,
                )
                for task in tasks
            ]

            for future in as_completed(
                futures
            ):

                try:

                    result = future.result()

                    results.append(result)

                except Exception as error:

                    errors.append(str(error))

                completed += 1

                print(
                    f"\rCompleted: "
                    f"{completed}/{len(files)} "
                    f"- {format_time(time() - start)}",
                    end="",
                    flush=True,
                )

    print()

    return results, errors


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(
    original_size,
    final_size,
):

    header("STATISTICS")

    print(
        f"Original: {format_size(original_size)}"
    )

    print(
        f"Final:    {format_size(final_size)}"
    )

    if original_size > 0:

        reduction = (
            (
                original_size - final_size
            )
            / original_size
            * 100
        )

        print(
            f"Reduction: {reduction:.1f}%"
        )

    print()

    if final_size <= original_size:

        print(
            "✓ Optimization completed"
        )

    else:

        print(
            "WARNING: the final output "
            "è più grande than the original."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    clear()

    header(APP_NAME)

    paths = collect_paths_from_input()

    if not paths:

        print("No files received.")
        pause()
        return

    files = expand_inputs(paths)

    if not files:

        print(
            "ERROR: no supported input "
            "was found."
        )

        pause()
        return

    clear()

    header(f"FILES FOUND: {len(files)}")

    for index, file in enumerate(
        files,
        1,
    ):

        print(
            f"{index}) {file.name}"
        )

    print()

    input(
        "Press ENTER to confirm "
        "the order..."
    )

    settings = ask_main_menu()

    if not settings:

        print("Operation cancelled.")
        return

    preset = settings["preset"]
    output_type = settings["output"]
    mode = settings["mode"]

    clear()

    header("SUMMARY")

    print(f"File: {len(files)}")
    print(f"Preset: {preset['name']}")
    print(
        f"Maximum side: "
        f"{preset['max_side']} px"
    )
    print(
        f"JPEG quality: "
        f"{preset['quality']}"
    )
    print(f"Output: {output_type}")

    print(
        "Mode: "
        + (
            "Single file"
            if mode == "single"
            else "Separate files"
        )
    )

    print(
        "Smart compression: ENABLED"
    )

    print()

    input("Press ENTER to start...")

    total_start = time()

    try:

        # ====================================================
        # SINGLE FILE
        # ====================================================

        if mode == "single":

            cpu_count = os.cpu_count() or 8

            page_workers = min(
                6,
                max(
                    2,
                    cpu_count - 2,
                ),
            )

            result = process_merged(
                files,
                preset,
                output_type,
                page_workers,
            )

            header("VALIDATION COMPLETE")

            print(
                f"Output pages: "
                f"{result['pages']}"
            )

            print(
                "✓ Output file is valid"
            )

            print()

            print_statistics(
                result["original_size"],
                result["final_size"],
            )

            print()
            print("OUTPUT:")
            print(result["output"])

        # ====================================================
        # SEPARATE FILES
        # ====================================================

        else:

            results, errors = process_separate(
                files,
                preset,
                output_type,
            )

            original_size = sum(
                result["original_size"]
                for result in results
            )

            final_size = sum(
                result["final_size"]
                for result in results
            )

            header("VALIDATION COMPLETE")

            print(
                f"Files completed: "
                f"{len(results)}"
            )

            if not errors:

                print(
                    "✓ All files completed"
                )

            print_statistics(
                original_size,
                final_size,
            )

            if errors:

                header("ERRORS")

                for error in errors:

                    print(error)
                    print()

            print()
            print("CREATED OUTPUTS:")

            for result in sorted(
                results,
                key=lambda item:
                natural_key(
                    item["output"].name
                ),
            ):

                print(
                    result["output"]
                )

    except KeyboardInterrupt:

        print()
        print(
            "Operation cancelled by user."
        )

    except Exception as error:

        header("ERROR")

        print(error)

    elapsed = time() - total_start

    print()

    line()

    print(
        f"OPERATION COMPLETED "
        f"IN {format_time(elapsed)}"
    )

    line()

    try:

        input(
            "\nPress ENTER to close..."
        )

    except EOFError:

        pass


if __name__ == "__main__":

    mp.freeze_support()

    main()