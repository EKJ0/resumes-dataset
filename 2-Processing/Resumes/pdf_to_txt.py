"""
pdf_to_txt.py
Converts all PDF files in "Resumes PDF" to plain-text .txt files using OCR,
mirroring the exact subfolder structure inside a new "Resumes TXT" folder.

Works on both text-based and image-based (scanned) PDFs.

Requirements:
    pip install pdfminer.six pdf2image pytesseract
    Optional but recommended:
        pip install pymupdf

    System:
        Windows: install Tesseract OCR and either PyMuPDF or Poppler.
        Linux:   sudo apt install tesseract-ocr poppler-utils
"""

import os
import shutil
import sys

# Paths (edit these if needed)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(SCRIPT_DIR, "Resumes PDF")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "Resumes TXT")

# If you install these tools somewhere custom, set the paths here or use env vars:
#   setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
#   setx POPPLER_PATH "C:\path\to\poppler\Library\bin"
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "")
POPPLER_PATH = os.environ.get("POPPLER_PATH", "")

# Re-run files that previously contained only an OCR error message.
RETRY_ERROR_FILES = True

try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    from pdf2image import convert_from_path
    import pytesseract
except ImportError as e:
    print(f"Missing library: {e}")
    print("Run: pip install pdfminer.six pdf2image pytesseract")
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

COMMON_POPPLER_PATHS = [
    os.path.join(SCRIPT_DIR, "poppler", "Library", "bin"),
    os.path.join(SCRIPT_DIR, "poppler", "bin"),
    r"C:\Program Files\poppler\Library\bin",
    r"C:\Program Files\poppler\bin",
    r"C:\poppler\Library\bin",
    r"C:\poppler\bin",
]


def first_existing_path(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return ""


def configure_external_tools():
    """Find Tesseract/Poppler on Windows without requiring PATH edits."""
    global POPPLER_PATH

    tesseract_cmd = TESSERACT_CMD or shutil.which("tesseract")
    if not tesseract_cmd:
        tesseract_cmd = first_existing_path(COMMON_TESSERACT_PATHS)
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    if not POPPLER_PATH:
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm:
            POPPLER_PATH = os.path.dirname(pdftoppm)
        else:
            POPPLER_PATH = first_existing_path(COMMON_POPPLER_PATHS)


configure_external_tools()


def executable_exists(command: str) -> bool:
    if not command:
        return False
    if os.path.isabs(command) or os.path.dirname(command):
        return os.path.isfile(command)
    return shutil.which(command) is not None


def extract_text_based(pdf_path: str) -> str:
    """Try to pull embedded text from a PDF (fast, no OCR)."""
    try:
        text = pdfminer_extract(pdf_path) or ""
        return text.strip()
    except Exception:
        return ""


def render_pages(pdf_path: str):
    """Render PDF pages for OCR. Prefer PyMuPDF because it does not need Poppler."""
    if fitz is not None:
        pages = []
        zoom = 200 / 72
        matrix = fitz.Matrix(zoom, zoom)
        with fitz.open(pdf_path) as doc:
            for page in doc:
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pages.append(pix.pil_image())
        return pages

    if not POPPLER_PATH:
        raise RuntimeError(
            "Poppler was not found. Install Poppler and add its bin folder to PATH, "
            "set POPPLER_PATH at the top of this script, or run: pip install pymupdf"
        )
    return convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)


def extract_via_ocr(pdf_path: str) -> str:
    """Convert each page to an image, then run Tesseract OCR."""
    tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
    if not executable_exists(tesseract_cmd):
        raise RuntimeError(
            "Tesseract OCR was not found. Install it and add it to PATH, "
            "or set TESSERACT_CMD at the top of this script."
        )

    pages = render_pages(pdf_path)
    parts = []
    for page_img in pages:
        parts.append(pytesseract.image_to_string(page_img))
    return "\n".join(parts).strip()


def pdf_to_text(pdf_path: str) -> str:
    """Use embedded text if available, else fall back to OCR."""
    text = extract_text_based(pdf_path)
    if text:
        return text
    return extract_via_ocr(pdf_path)


def should_skip_existing(txt_path: str) -> bool:
    if not os.path.exists(txt_path):
        return False
    if not RETRY_ERROR_FILES:
        return True

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        previous_text = f.read(200)
    return not previous_text.startswith("[OCR ERROR:")


def convert_all():
    if not os.path.isdir(SOURCE_DIR):
        print(f"ERROR: Source folder not found:\n  {SOURCE_DIR}")
        sys.exit(1)

    converted = 0
    skipped = 0
    errors = 0

    for root, dirs, files in os.walk(SOURCE_DIR):
        dirs.sort()  # alphabetical subfolder order

        pdf_files = sorted(f for f in files if f.lower().endswith(".pdf"))
        if not pdf_files:
            continue

        rel_path = os.path.relpath(root, SOURCE_DIR)
        target_dir = os.path.join(OUTPUT_DIR, rel_path)
        os.makedirs(target_dir, exist_ok=True)

        for pdf_name in pdf_files:
            pdf_path = os.path.join(root, pdf_name)
            txt_name = os.path.splitext(pdf_name)[0] + ".txt"
            txt_path = os.path.join(target_dir, txt_name)
            rel_txt_path = os.path.relpath(txt_path, OUTPUT_DIR)

            if should_skip_existing(txt_path):
                print(f"  [skip]  {rel_txt_path}")
                skipped += 1
                continue
            if os.path.exists(txt_path):
                print(f"  [retry] {rel_txt_path}")

            try:
                text = pdf_to_text(pdf_path)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"  [ok]    {rel_txt_path}")
                converted += 1
            except Exception as e:
                print(f"  [ERROR] {pdf_name}: {e}")
                errors += 1

    print("\n" + "-" * 50)
    print(f"Done.  Converted: {converted}  |  Skipped: {skipped}  |  Errors: {errors}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
