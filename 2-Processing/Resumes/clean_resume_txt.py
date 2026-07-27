"""
clean_resume_txt.py

Clean and lightly structure resume/CV text files for easier research reading.

By default, this script:
    - reads .txt files from "Resumes TXT"
    - writes cleaned copies to "Cleaned Resumes TXT"
    - preserves the original folder structure
    - leaves the original files untouched
    - creates a small before/after preview report

Usage:
    python clean_resume_txt.py
    python clean_resume_txt.py --limit 25
    python clean_resume_txt.py --input "Resumes TXT" --output "Cleaned Resumes TXT"
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = SCRIPT_DIR / "Resumes TXT"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "Cleaned Resumes TXT"
DEFAULT_PREVIEW_REPORT = SCRIPT_DIR / "cleaning_preview_report.txt"


SECTION_ALIASES = {
    "career objective": "CAREER OBJECTIVE",
    "certification": "CERTIFICATIONS",
    "certifications": "CERTIFICATIONS",
    "contact": "CONTACT",
    "education": "EDUCATION",
    "educational qualification": "EDUCATION",
    "educational qualifications": "EDUCATION",
    "employment history": "WORK EXPERIENCE",
    "experience": "WORK EXPERIENCE",
    "highlight": "HIGHLIGHTS",
    "highlights": "HIGHLIGHTS",
    "interests": "INTERESTS",
    "key skills": "KEY SKILLS",
    "objective": "OBJECTIVE",
    "personal details": "PERSONAL DETAILS",
    "professional experience": "WORK EXPERIENCE",
    "professional summary": "PROFESSIONAL SUMMARY",
    "profile": "PROFILE",
    "project": "PROJECTS",
    "projects": "PROJECTS",
    "publications": "PUBLICATIONS",
    "references": "REFERENCES",
    "research": "RESEARCH",
    "skills": "SKILLS",
    "summary": "SUMMARY",
    "technical skills": "TECHNICAL SKILLS",
    "tools": "TOOLS",
    "work experience": "WORK EXPERIENCE",
    "work history": "WORK EXPERIENCE",
}


BULLET_START_RE = re.compile(r"^\s*(?:[-*~•«]+|[eEoO0©¢°·]\s+|\+\s+|[0-9]+[.)]\s+)")
DATE_RANGE_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|\d{1,2})"
    r"[a-z]*[ ./-]*\d{2,4}\b|\b\d{4}\b",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
URL_RE = re.compile(r"\b(?:https?://|www\.|linkedin\.com|github\.com)\S+", re.IGNORECASE)


@dataclass
class CleanStats:
    input_files: int = 0
    output_files: int = 0
    empty_files: int = 0
    decode_errors: int = 0


def read_text(path: Path) -> str:
    """Read common OCR/text encodings without stopping the full batch."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "Could not decode file")


def normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = text.replace("—", " - ")
    text = text.replace("–", " - ")
    text = text.replace("•", "-")
    text = re.sub(r"[ \u00a0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalized_section_name(line: str) -> str | None:
    candidate = re.sub(r"[:|]+$", "", line.strip())
    candidate = re.sub(r"\s+", " ", candidate)
    key = candidate.lower()

    if key in SECTION_ALIASES:
        return SECTION_ALIASES[key]

    return None


def is_likely_heading(line: str) -> bool:
    return normalized_section_name(line) is not None


def is_likely_new_item(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if is_likely_heading(stripped):
        return True
    if BULLET_START_RE.match(stripped):
        return True
    if EMAIL_RE.search(stripped) or PHONE_RE.search(stripped) or URL_RE.search(stripped):
        return True
    if DATE_RANGE_RE.search(stripped) and len(stripped) < 100:
        return True
    return False


def clean_bullet(line: str) -> str:
    line = line.strip()
    if not line:
        return ""

    if BULLET_START_RE.match(line):
        line = BULLET_START_RE.sub("- ", line, count=1)

    line = re.sub(r"^\s*-\s*", "- ", line)
    return line


def should_join(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    if previous.startswith("- ") and not is_likely_new_item(current):
        return True
    if previous.endswith((".", ":", ";", "!", "?")):
        return False
    if is_likely_new_item(current):
        return False
    if len(previous) < 90 and len(current) < 90:
        return True
    return False


def build_readable_lines(text: str) -> list[str]:
    raw_lines = [clean_bullet(line) for line in normalize_text(text).split("\n")]
    lines: list[str] = []

    for raw in raw_lines:
        line = raw.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue

        heading = normalized_section_name(line)
        if heading:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(heading)
            lines.append("-" * len(heading))
            continue

        if lines and lines[-1] and should_join(lines[-1], line):
            lines[-1] = f"{lines[-1]} {line}".strip()
        else:
            lines.append(line)

    return trim_blank_lines(lines)


def trim_blank_lines(lines: list[str]) -> list[str]:
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()

    compacted: list[str] = []
    for line in lines:
        if line == "" and compacted and compacted[-1] == "":
            continue
        compacted.append(line)
    return compacted


def clean_resume_text(text: str) -> str:
    lines = build_readable_lines(text)
    return "\n".join(lines).strip() + "\n"


def text_preview(text: str, max_lines: int = 18) -> str:
    lines = normalize_text(text).split("\n")
    visible = [line for line in lines if line.strip()]
    return "\n".join(visible[:max_lines])


def clean_all_txt_files(
    input_dir: Path,
    output_dir: Path,
    preview_report: Path,
    limit: int | None = None,
    preview_count: int = 5,
    skip_existing: bool = False,
) -> CleanStats:
    stats = CleanStats()
    txt_files = sorted(input_dir.rglob("*.txt"))
    if limit is not None:
        txt_files = txt_files[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    preview_blocks: list[str] = []

    for source_path in txt_files:
        stats.input_files += 1
        relative_path = source_path.relative_to(input_dir)
        target_path = output_dir / relative_path
        if skip_existing and target_path.exists():
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            original = read_text(source_path)
        except UnicodeDecodeError:
            stats.decode_errors += 1
            continue

        if not original.strip():
            stats.empty_files += 1
            cleaned = ""
        else:
            cleaned = clean_resume_text(original)

        target_path.write_text(cleaned, encoding="utf-8")
        stats.output_files += 1

        if len(preview_blocks) < preview_count:
            preview_blocks.append(
                "\n".join(
                    [
                        "=" * 80,
                        f"FILE: {relative_path}",
                        "",
                        "BEFORE",
                        "------",
                        text_preview(original),
                        "",
                        "AFTER",
                        "-----",
                        text_preview(cleaned),
                    ]
                )
            )

    report = [
        "Resume TXT Cleaning Preview",
        "===========================",
        "",
        f"Input folder: {input_dir}",
        f"Output folder: {output_dir}",
        f"Files read: {stats.input_files}",
        f"Files written: {stats.output_files}",
        f"Empty files: {stats.empty_files}",
        f"Decode errors skipped: {stats.decode_errors}",
        "",
        *preview_blocks,
        "",
    ]
    preview_report.write_text("\n".join(report), encoding="utf-8")
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean resume/CV .txt files into a safer, research-friendly format."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_DIR),
        help='Folder containing original .txt files. Default: "Resumes TXT"',
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help='Folder for cleaned .txt files. Default: "Cleaned Resumes TXT"',
    )
    parser.add_argument(
        "--preview-report",
        default=str(DEFAULT_PREVIEW_REPORT),
        help='Path for before/after preview report. Default: "cleaning_preview_report.txt"',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only clean the first N files. Useful for testing before running the full dataset.",
    )
    parser.add_argument(
        "--preview-count",
        type=int,
        default=5,
        help="Number of before/after examples to include in the preview report.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Resume a previous run by skipping cleaned files that already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    preview_report = Path(args.preview_report).resolve()

    if not input_dir.exists():
        print(f"Input folder does not exist: {input_dir}")
        return 1

    stats = clean_all_txt_files(
        input_dir=input_dir,
        output_dir=output_dir,
        preview_report=preview_report,
        limit=args.limit,
        preview_count=args.preview_count,
        skip_existing=args.skip_existing,
    )

    print("Done.")
    print(f"Files read: {stats.input_files}")
    print(f"Files written: {stats.output_files}")
    print(f"Cleaned folder: {output_dir}")
    print(f"Preview report: {preview_report}")
    if stats.decode_errors:
        print(f"Skipped files with decode errors: {stats.decode_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
