import argparse
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[2]
RESUME_ROOT = PROJECT_ROOT / "2-Processing" / "Resumes" / "Cleaned Resumes TXT"
FIRST_NAMES_PATH = PROJECT_ROOT / "2-Processing" / "First Names" / "first_names_clean.csv"
OUTPUT_DIR = ROOT / "outputs"
INPUT_DIR = ROOT / "input"

DEFAULT_GENDER_THRESHOLD = 0.85

LANGUAGES = [
    "english", "spanish", "french", "german", "italian", "portuguese",
    "arabic", "chinese", "mandarin", "japanese", "korean", "hindi",
    "urdu", "russian", "dutch", "turkish", "albanian", "greek",
    "polish", "romanian", "serbian", "croatian", "bosnian", "vietnamese",
    "thai", "hebrew", "farsi", "persian", "bengali", "punjabi",
]

LEADERSHIP_TERMS = [
    "led", "lead", "leader", "leadership", "managed", "manager",
    "supervised", "supervisor", "directed", "coordinated", "owned",
    "oversaw", "mentored", "trained", "delegated", "headed", "guided",
    "administered", "chaired", "founded",
]

ACTION_TERMS = [
    "developed", "created", "built", "implemented", "improved",
    "analyzed", "designed", "delivered", "launched", "organized",
    "achieved", "increased", "reduced", "optimized", "managed",
    "coordinated", "supported", "maintained",
]

NAME_STOPWORDS = {
    "summary", "profile", "objective", "resume", "curriculum", "vitae",
    "professional", "experience", "work", "education", "skills", "details",
    "contact", "phone", "email", "address", "career", "highlights",
    "accomplishments", "certifications",
}

DEGREE_PATTERNS = [
    ("doctorate", r"\b(ph\.?d\.?|doctorate|doctoral)\b"),
    ("master", r"\b(master'?s?|m\.s\.|msc|m\.a\.|mba|m\.b\.a\.)\b"),
    ("bachelor", r"\b(bachelor'?s?|b\.s\.|bs\b|b\.a\.|ba\b|undergraduate)\b"),
    ("associate", r"\b(associate'?s?|a\.s\.|aa\b)\b"),
    ("high_school_or_equivalent", r"\b(high school|ged)\b"),
]

FIELD_PATTERNS = [
    ("computer_science_or_it", r"\b(computer science|information technology|software|data science|cybersecurity|computer engineering)\b"),
    ("business_or_management", r"\b(business administration|business management|management|marketing|finance|accounting|mba)\b"),
    ("engineering", r"\b(engineering|mechanical|electrical|civil engineer|industrial engineering)\b"),
    ("education", r"\b(education|teaching|curriculum|pedagogy)\b"),
    ("healthcare", r"\b(nursing|medicine|medical|healthcare|public health|pharmacy)\b"),
    ("arts_or_design", r"\b(arts?|design|graphic design|fine arts|visual communication)\b"),
    ("law_or_legal", r"\b(law|legal studies|juris doctor|paralegal)\b"),
]


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def canonical_category(category):
    text = category.strip()
    text = re.sub(r"\s+resumes?$", "", text, flags=re.IGNORECASE)
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    aliases = {
        "Managment": "Management",
        "Consult": "Consultant",
        "DataScience": "Data Science",
        "BusinessAnalyst": "Business Analyst",
        "CivilEngineer": "Civil Engineer",
        "DevOpsEngineer": "DevOps Engineer",
        "ElectricalEngineer": "Electrical Engineer",
        "HealthFitness": "Health Fitness",
        "JavaDeveloper": "Java Developer",
        "MechanicalEngineer": "Mechanical Engineer",
        "OperationManager": "Operations Manager",
        "PythonDeveloper": "Python Developer",
        "SAPDeveloper": "SAP Developer",
        "WebDesigning": "Web Designing",
        "NSE": "Network Security Engineer",
        "PBO": "BPO",
        "Building Construction": "Construction",
        "Food Beverages": "Food",
        "DotNet Developer": ".NET Developer",
        "DOT": ".NET Developer",
        "SQL": "SQL Developer",
        "React": "React Developer",
        "Public": "Public Relations",
        "Digital": "Digital Media",
        "Design": "Designer",
        "IT": "Information Technology",
        "HR": "Human Resources",
    }
    return aliases.get(text, text).title()


def read_resume(path):
    return path.read_text(encoding="utf-8", errors="ignore")


def build_manifest(resume_root):
    records = []
    for path in sorted(resume_root.rglob("*.txt")):
        original_category = path.parent.name
        records.append({
            "resume_id": f"{original_category}/{path.stem}",
            "file_name": path.name,
            "file_stem": path.stem,
            "file_path": str(path),
            "original_category": original_category,
            "clean_category": canonical_category(original_category),
        })
    return pd.DataFrame(records)


def load_first_names(path):
    names = pd.read_csv(path)
    names["name_key"] = names["name"].astype(str).str.strip().str.lower()
    names = names.sort_values(["gender_probability", "top_country_probability"], ascending=False)
    names = names.drop_duplicates("name_key")
    keep_columns = ["name_key", "name", "predicted_gender", "gender_probability"]
    return names[keep_columns].set_index("name_key").to_dict("index")


def possible_name_lines(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = [text[:160]]
    return lines[:6]


def extract_first_name(text):
    for line in possible_name_lines(text):
        line = re.sub(r"[\|,;:/\\]+", " ", line)
        tokens = re.findall(r"[A-Za-z][A-Za-z'-]{1,30}", line)
        tokens = [token for token in tokens if token.lower() not in NAME_STOPWORDS]
        if tokens:
            return tokens[0].title()
    return ""


def infer_gender(first_name, names_lookup, threshold):
    if not first_name:
        return {
            "inferred_gender_from_name": "unknown_or_no_name",
            "inferred_gender_confidence": pd.NA,
            "gender_match_name": "",
            "gender_source": "not_inferred",
        }

    row = names_lookup.get(first_name.lower())
    if row is None:
        return {
            "inferred_gender_from_name": "unknown_or_no_name",
            "inferred_gender_confidence": pd.NA,
            "gender_match_name": "",
            "gender_source": "not_inferred",
        }

    confidence = float(row["gender_probability"])
    gender = str(row["predicted_gender"]).strip().lower()
    if confidence >= threshold and gender in {"male", "female"}:
        group = f"{gender}_high_confidence"
        source = "first_name_high_confidence"
    else:
        group = "unknown_or_low_confidence"
        source = "first_name_low_confidence"

    return {
        "inferred_gender_from_name": group,
        "inferred_gender_confidence": confidence,
        "gender_match_name": row["name"],
        "gender_source": source,
    }


def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


def bucket_resume_length(count):
    if count < 300:
        return "short"
    if count < 700:
        return "medium"
    if count < 1200:
        return "long"
    return "very_long"


def count_terms(text, terms):
    lowered = text.lower()
    return sum(len(re.findall(rf"\b{re.escape(term)}\b", lowered)) for term in terms)


def group_count(count, low_max, medium_max):
    if count == 0:
        return "none"
    if count <= low_max:
        return "low"
    if count <= medium_max:
        return "medium"
    return "high"


def language_features(text):
    lowered = text.lower()
    found = sorted({lang for lang in LANGUAGES if re.search(rf"\b{re.escape(lang)}\b", lowered)})
    if len(found) == 0:
        group = "none_found"
    elif len(found) == 1 and found[0] == "english":
        group = "english_only"
    elif len(found) == 1:
        group = "one_non_english_language"
    else:
        group = "multilingual"
    return group, len(found), ";".join(found)


def volunteering_features(text):
    lowered = text.lower()
    if not re.search(r"\b(volunteer|volunteered|volunteering|community service|nonprofit|non-profit|charity)\b", lowered):
        return False, "none_found"
    if re.search(r"\b(board|committee|mentor|coach|tutor|fundraising|fundraiser)\b", lowered):
        return True, "leadership_or_service"
    if re.search(r"\b(charity|nonprofit|non-profit|community service)\b", lowered):
        return True, "community_or_nonprofit"
    return True, "volunteering_mentioned"


def extracurricular_features(text):
    lowered = text.lower()
    if not re.search(r"\b(extracurricular|club|clubs|student organization|society|fraternity|sorority|athletics|sports team)\b", lowered):
        return False, "none_found"
    if re.search(r"\b(athletics|sports team|varsity|intramural)\b", lowered):
        return True, "sports"
    if re.search(r"\b(art|music|theater|theatre|drama|dance)\b", lowered):
        return True, "arts"
    if re.search(r"\b(student organization|club|society|fraternity|sorority)\b", lowered):
        return True, "clubs_or_academic"
    return True, "other"


def education_level(text):
    lowered = text.lower()
    for level, pattern in DEGREE_PATTERNS:
        if re.search(pattern, lowered):
            return level
    if re.search(r"\b(education|university|college|degree|diploma)\b", lowered):
        return "education_mentioned_unknown_level"
    return "not_found"


def education_field(text):
    lowered = text.lower()
    for field, pattern in FIELD_PATTERNS:
        if re.search(pattern, lowered):
            return field
    if re.search(r"\b(degree|bachelor|master|ph\.?d\.?|university|college)\b", lowered):
        return "field_not_clear"
    return "not_found"


def explicit_age_group(text):
    lowered = text.lower()
    match = re.search(r"\b([1-7][0-9])\s*(?:years old|year old|yrs old|yo)\b", lowered)
    if not match:
        return "unknown"
    age = int(match.group(1))
    if age < 25:
        return "under_25"
    if age < 35:
        return "25_34"
    if age < 45:
        return "35_44"
    return "45_plus"


def nationality_features(text):
    lowered = text.lower()
    if re.search(r"\b(nationality|citizenship|citizen of)\b", lowered):
        return True, "nationality_or_citizenship_mentioned"
    if re.search(r"\bauthorized to work\b", lowered):
        return True, "work_authorization_mentioned"
    return False, "none_found"


def writing_style(text, words, action_count):
    if words == 0:
        return "empty"
    sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
    avg_sentence_words = words / sentence_count
    action_density = action_count / words
    if words < 300:
        return "concise"
    if words > 1200 or avg_sentence_words > 35:
        return "detailed"
    if action_density > 0.025:
        return "keyword_heavy"
    if avg_sentence_words > 26:
        return "formal"
    return "balanced"


def build_features(manifest, names_lookup, gender_threshold):
    records = []

    for row in manifest.itertuples(index=False):
        text = clean_text(read_resume(Path(row.file_path)))
        first_name = extract_first_name(text)
        gender_info = infer_gender(first_name, names_lookup, gender_threshold)
        words = word_count(text)
        action_count = count_terms(text, ACTION_TERMS)
        leadership_count = count_terms(text, LEADERSHIP_TERMS)
        language_group, language_count, languages_found = language_features(text)
        volunteering_present, volunteering_type = volunteering_features(text)
        extracurricular_present, extracurricular_type = extracurricular_features(text)
        nationality_present, nationality_group = nationality_features(text)

        records.append({
            "resume_id": row.resume_id,
            "file_name": row.file_name,
            "file_path": row.file_path,
            "original_category": row.original_category,
            "clean_category": row.clean_category,
            "first_name_extracted": first_name,
            **gender_info,
            "age_group_explicit": explicit_age_group(text),
            "nationality_or_citizenship_mentioned": nationality_present,
            "nationality_group_explicit": nationality_group,
            "language_group": language_group,
            "language_count": language_count,
            "languages_found": languages_found,
            "volunteering_present": volunteering_present,
            "volunteering_type": volunteering_type,
            "extracurricular_present": extracurricular_present,
            "extracurricular_type": extracurricular_type,
            "education_level": education_level(text),
            "education_field": education_field(text),
            "writing_style": writing_style(text, words, action_count),
            "leadership_word_count": leadership_count,
            "leadership_language_group": group_count(leadership_count, 3, 8),
            "resume_word_count": words,
            "resume_length_group": bucket_resume_length(words),
            "action_word_count": action_count,
        })

    return pd.DataFrame(records)


def count_summary(df, group_columns):
    rows = []
    total = len(df)
    for column in group_columns:
        counts = df[column].value_counts(dropna=False).reset_index()
        counts.columns = ["group_value", "resume_count"]
        counts.insert(0, "group_type", column)
        counts["share_of_all_resumes"] = counts["resume_count"] / total
        rows.append(counts)
    return pd.concat(rows, ignore_index=True)


def two_way_summary(df, row_group, compare_columns):
    rows = []
    for column in compare_columns:
        grouped = df.groupby([row_group, column], dropna=False).size().reset_index(name="resume_count")
        grouped["within_group_share"] = grouped["resume_count"] / grouped.groupby(row_group)["resume_count"].transform("sum")
        grouped.insert(1, "feature", column)
        grouped = grouped.rename(columns={column: "feature_value"})
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True)


def proxy_risk_summary(df, min_group_size):
    compare_columns = [
        "language_group", "volunteering_present", "volunteering_type",
        "extracurricular_present", "extracurricular_type", "education_level",
        "education_field", "writing_style", "leadership_language_group",
        "resume_length_group",
    ]
    gender_col = "inferred_gender_from_name"
    valid_groups = df[gender_col].value_counts()
    valid_groups = valid_groups[valid_groups >= min_group_size].index.tolist()
    comparable = df[df[gender_col].isin(valid_groups)]

    rows = []
    if comparable[gender_col].nunique() < 2:
        return pd.DataFrame([{
            "protected_or_sensitive_group": gender_col,
            "proxy_feature": "all",
            "status": "not_testable",
            "detail": f"Fewer than two inferred gender groups have at least {min_group_size} resumes.",
        }])

    for column in compare_columns:
        table = pd.crosstab(comparable[gender_col], comparable[column], normalize="index")
        max_gap = float((table.max(axis=0) - table.min(axis=0)).max())
        rows.append({
            "protected_or_sensitive_group": gender_col,
            "proxy_feature": column,
            "status": "review" if max_gap >= 0.20 else "no_large_gap_found",
            "detail": f"largest_distribution_gap={max_gap:.3f}",
        })
    return pd.DataFrame(rows)


def write_results_readme(features, gender_threshold, min_group_size):
    gender_counts = features["inferred_gender_from_name"].value_counts(dropna=False)
    category_count = features["clean_category"].nunique()
    lines = [
        "# Resume Grouping Results",
        "",
        f"Total resumes grouped: {len(features):,}",
        f"Cleaned categories: {category_count:,}",
        f"Gender inference threshold: {gender_threshold:.2f}",
        f"Minimum proxy-check group size: {min_group_size:,}",
        "",
        "## Gender Inference",
        "",
        "Gender is inferred from the extracted first name and `first_names_clean.csv` only when the confidence is high enough.",
        "This is not a confirmed protected attribute. Use it for exploratory grouping, not hiring decisions.",
        "",
        "Gender groups:",
    ]
    for group, count in gender_counts.items():
        lines.append(f"- {group}: {count:,}")

    lines.extend([
        "",
        "## Main Outputs",
        "",
        "- `all_resume_group_features.csv`: one row per resume with every grouping column",
        "- `source_manifest.csv`: every cleaned TXT file used as input",
        "- `group_counts_summary.csv`: counts for all major grouping fields",
        "- `gender_group_summary.csv`: gender-by-feature summary",
        "- `category_group_summary.csv`: category-by-feature summary",
        "- `education_group_summary.csv`: education-level counts and category cross-tabs",
        "- `language_group_summary.csv`: language counts and category cross-tabs",
        "- `proxy_risk_summary.csv`: possible proxy-risk flags based on inferred gender",
        "",
        "## Caution",
        "",
        "The files group resumes; they do not measure hiring bias unless you add a real hiring outcome such as selected, rejected, interview, score, or ranking.",
    ])
    (OUTPUT_DIR / "README_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Group all cleaned resume TXT files using content, style, and inferred gender features.")
    parser.add_argument("--resume-root", default=str(RESUME_ROOT), help="Folder containing cleaned TXT resumes")
    parser.add_argument("--first-names", default=str(FIRST_NAMES_PATH), help="first_names_clean.csv path")
    parser.add_argument("--gender-threshold", type=float, default=DEFAULT_GENDER_THRESHOLD, help="Minimum first-name confidence for male/female group")
    parser.add_argument("--min-proxy-group-size", type=int, default=30, help="Minimum group size for proxy-risk comparisons")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    INPUT_DIR.mkdir(exist_ok=True)

    manifest = build_manifest(Path(args.resume_root))
    first_names = load_first_names(args.first_names)
    features = build_features(manifest, first_names, args.gender_threshold)

    manifest.to_csv(INPUT_DIR / "source_manifest.csv", index=False)
    features.to_csv(OUTPUT_DIR / "all_resume_group_features.csv", index=False)

    group_columns = [
        "inferred_gender_from_name", "clean_category", "age_group_explicit",
        "nationality_group_explicit", "language_group", "volunteering_present",
        "volunteering_type", "extracurricular_present", "extracurricular_type",
        "education_level", "education_field", "writing_style",
        "leadership_language_group", "resume_length_group",
    ]
    count_summary(features, group_columns).to_csv(OUTPUT_DIR / "group_counts_summary.csv", index=False)

    compare_columns = [
        "clean_category", "language_group", "volunteering_present",
        "extracurricular_present", "education_level", "education_field",
        "writing_style", "leadership_language_group", "resume_length_group",
    ]
    two_way_summary(features, "inferred_gender_from_name", compare_columns).to_csv(OUTPUT_DIR / "gender_group_summary.csv", index=False)
    two_way_summary(features, "clean_category", [
        "inferred_gender_from_name", "language_group", "volunteering_present",
        "extracurricular_present", "education_level", "writing_style",
        "leadership_language_group", "resume_length_group",
    ]).to_csv(OUTPUT_DIR / "category_group_summary.csv", index=False)
    two_way_summary(features, "education_level", ["clean_category", "inferred_gender_from_name", "education_field"]).to_csv(OUTPUT_DIR / "education_group_summary.csv", index=False)
    two_way_summary(features, "language_group", ["clean_category", "inferred_gender_from_name", "languages_found"]).to_csv(OUTPUT_DIR / "language_group_summary.csv", index=False)
    proxy_risk_summary(features, args.min_proxy_group_size).to_csv(OUTPUT_DIR / "proxy_risk_summary.csv", index=False)
    write_results_readme(features, args.gender_threshold, args.min_proxy_group_size)

    print(f"Grouped {len(features):,} resumes")
    print(f"Wrote outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
