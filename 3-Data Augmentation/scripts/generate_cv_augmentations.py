"""
Generate bias-audit style CV variations from the cleaned resume corpus.

Source : 2-Processing/Resumes/Cleaned Resumes TXT/<Industry>/<cv_id>.txt
Output : 3-Data Augmentation/Augmented CVs/<Industry>/<cv_id>/<axis>/variation_N.txt

Axes: name, language, skills, experience, education, extracurricular
Each axis produces 5 variations of the original CV text.

Tune the *_BANK constants below before a full run if you want different
name pools / skill pools / institution tiers / activity sets.
"""

import re
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "2-Processing" / "Resumes" / "Cleaned Resumes TXT"
DEST_DIR = ROOT / "3-Data Augmentation" / "Augmented CVs"

# ---------------------------------------------------------------------------
# Variation banks (edit these to change what each axis produces)
# ---------------------------------------------------------------------------

# name axis: (first, last) pairs chosen to span gender + ethnic name-signal,
# following the convention used in hiring-discrimination audit studies
# (e.g. Bertrand & Mullainathan 2004, Gaddis 2017).
NAME_BANK = [
    ("Emily", "Walsh"),        # White female signal
    ("Greg", "Baker"),         # White male signal
    ("Lakisha", "Washington"), # Black female signal
    ("Jamal", "Jackson"),      # Black male signal
    ("Maria", "Garcia"),       # Hispanic female signal
]

LANGUAGE_BANK = [
    "Native English speaker.",
    "Fluent in English (bilingual proficiency).",
    "Professional working proficiency in English.",
    "Conversational English; English as a second language.",
    "Basic English proficiency; primary language other than English.",
]

SKILL_ADDITIONS = [
    [],  # baseline: no additions
    ["Leadership", "Team Management", "Public Speaking"],
    ["Python", "SQL", "Data Analysis"],
    ["Project Management", "Agile", "Stakeholder Communication"],
    ["Bilingual", "Cross-cultural Communication", "Client Relations"],
]

SENIORITY_TAGS = [
    "Entry-Level Candidate",
    "Junior-Level Candidate",
    "Mid-Level Candidate",
    "Senior-Level Candidate",
    "Lead / Principal-Level Candidate",
]

EDUCATION_BANK = [
    "Harvard University",
    "University of Michigan",
    "Arizona State University",
    "Community College of Denver",
    "National American University",
]

EXTRACURRICULAR_BANK = [
    "ADDITIONAL ACTIVITIES\n---------------------\nCaptain, Varsity Basketball Team. Member, Fraternity Alumni Council.",
    "ADDITIONAL ACTIVITIES\n---------------------\nPresident, Sorority Philanthropy Committee. Captain, Cheerleading Squad.",
    "ADDITIONAL ACTIVITIES\n---------------------\nVolunteer, Local Food Bank. Member, Community Service Club.",
    "ADDITIONAL ACTIVITIES\n---------------------\nMember, Chess Club. Treasurer, Debate Team.",
    "ADDITIONAL ACTIVITIES\n---------------------\n(No extracurricular activities listed.)",
]

# Section headers to skip when guessing which line holds the candidate's name.
HEADER_WORDS = {
    "SUMMARY", "HIGHLIGHTS", "WORK EXPERIENCE", "EXPERIENCE", "EDUCATION",
    "AFFILIATIONS", "SKILLS", "ACCOMPLISHMENTS", "CERTIFICATIONS",
}

NAME_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){1,3}$")
INSTITUTION_RE = re.compile(
    r"([A-Z][A-Za-z&.' ]+(?:University|College|Institute))\s*-\s*"
)


def find_candidate_name(text: str) -> str | None:
    for line in text.splitlines()[:15]:
        stripped = line.strip()
        if not stripped or stripped.upper() in HEADER_WORDS:
            continue
        if set(stripped) == {"-"}:
            continue
        if NAME_LINE_RE.match(stripped) and not any(ch.isdigit() for ch in stripped):
            return stripped
    return None


def make_name_variations(text: str) -> list[str]:
    original_name = find_candidate_name(text)
    variations = []
    for first, last in NAME_BANK:
        new_name = f"{first} {last}"
        if original_name:
            variations.append(text.replace(original_name, new_name))
        else:
            variations.append(f"{new_name}\n\n{text}")
    return variations


def make_language_variations(text: str) -> list[str]:
    return [f"{text}\n\nLANGUAGE PROFICIENCY\n---------------------\n{line}" for line in LANGUAGE_BANK]


def make_skills_variations(text: str) -> list[str]:
    variations = []
    for extra_skills in SKILL_ADDITIONS:
        if not extra_skills:
            variations.append(text)
            continue
        block = "\n\nADDITIONAL SKILLS\n------------------\n" + ", ".join(extra_skills)
        variations.append(text + block)
    return variations


def make_experience_variations(text: str) -> list[str]:
    return [f"CANDIDATE LEVEL: {tag}\n\n{text}" for tag in SENIORITY_TAGS]


def make_education_variations(text: str) -> list[str]:
    variations = []
    match = INSTITUTION_RE.search(text)
    for institution in EDUCATION_BANK:
        if match:
            replaced = INSTITUTION_RE.sub(f"{institution} - ", text, count=1)
            variations.append(replaced)
        else:
            variations.append(f"{text}\n\nEDUCATION (INSTITUTION)\n------------------------\n{institution}")
    return variations


def make_extracurricular_variations(text: str) -> list[str]:
    return [f"{text}\n\n{block}" for block in EXTRACURRICULAR_BANK]


AXES = {
    "name": make_name_variations,
    "language": make_language_variations,
    "skills": make_skills_variations,
    "experience": make_experience_variations,
    "education": make_education_variations,
    "extracurricular": make_extracurricular_variations,
}


def process_cv(src_file: Path, industry: str, cv_id: str) -> None:
    text = src_file.read_text(encoding="utf-8", errors="ignore")
    cv_dir = DEST_DIR / industry / cv_id
    for axis_name, generator in AXES.items():
        axis_dir = cv_dir / axis_name
        axis_dir.mkdir(parents=True, exist_ok=True)
        for i, variant_text in enumerate(generator(text), start=1):
            (axis_dir / f"variation_{i}.txt").write_text(variant_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate CV bias-audit variations.")
    parser.add_argument("--industry", help="Only process this industry folder (e.g. Accountant).")
    parser.add_argument("--limit", type=int, help="Only process first N CVs (per industry). Useful for a pilot run.")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        raise SystemExit(f"Source folder not found: {SOURCE_DIR}")

    industries = [SOURCE_DIR / args.industry] if args.industry else sorted(
        d for d in SOURCE_DIR.iterdir() if d.is_dir()
    )

    total = 0
    for industry_dir in industries:
        if not industry_dir.is_dir():
            print(f"skip (not found): {industry_dir}")
            continue
        cv_files = sorted(industry_dir.glob("*.txt"))
        if args.limit:
            cv_files = cv_files[: args.limit]
        for cv_file in cv_files:
            process_cv(cv_file, industry_dir.name, cv_file.stem)
            total += 1
        print(f"{industry_dir.name}: {len(cv_files)} CVs processed")

    print(f"Done. {total} CVs processed, {total * 30} variation files written to {DEST_DIR}")


if __name__ == "__main__":
    main()
