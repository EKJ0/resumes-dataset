import argparse
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "input" / "Resume.csv"
OUTPUT_DIR = ROOT / "outputs"

TEXT_COLUMN = "Resume_str"
ID_COLUMN = "ID"
CATEGORY_COLUMN = "Category"

PROTECTED_COLUMNS = ["gender", "ethnicity", "age_group", "nationality"]
CONTENT_COLUMNS = [
    "language_group",
    "language_count",
    "volunteering_present",
    "volunteering_type",
    "extracurricular_present",
    "extracurricular_type",
    "education_level",
    "education_institution_type",
    "education_field",
    "leadership_word_count",
    "leadership_language_group",
]
STYLE_COLUMNS = ["writing_style", "resume_word_count", "resume_length_group"]

LANGUAGES = [
    "english", "spanish", "french", "german", "italian", "portuguese",
    "arabic", "chinese", "mandarin", "japanese", "korean", "hindi",
    "urdu", "russian", "dutch", "turkish", "albanian", "greek",
    "polish", "romanian", "serbian", "croatian", "bosnian",
]

LEADERSHIP_TERMS = [
    "led", "lead", "leader", "leadership", "managed", "manager",
    "supervised", "supervisor", "directed", "coordinated", "owned",
    "oversaw", "mentored", "trained", "delegated", "headed",
]

ACTION_TERMS = [
    "developed", "created", "built", "implemented", "improved",
    "analyzed", "designed", "delivered", "launched", "organized",
    "achieved", "increased", "reduced", "optimized",
]

DEGREE_PATTERNS = [
    ("doctorate", r"\b(ph\.?d\.?|doctorate|doctoral)\b"),
    ("master", r"\b(master'?s?|m\.s\.|msc|m\.a\.|mba)\b"),
    ("bachelor", r"\b(bachelor'?s?|b\.s\.|bs\b|b\.a\.|ba\b|undergraduate)\b"),
    ("associate", r"\b(associate'?s?|a\.s\.|aa\b)\b"),
    ("high_school_or_equivalent", r"\b(high school|ged)\b"),
]

FIELD_PATTERNS = [
    ("computer_science_or_it", r"\b(computer science|information technology|software|data science|cybersecurity)\b"),
    ("business_or_management", r"\b(business administration|management|marketing|finance|accounting|mba)\b"),
    ("engineering", r"\b(engineering|mechanical|electrical|civil engineer)\b"),
    ("education", r"\b(education|teaching|curriculum)\b"),
    ("healthcare", r"\b(nursing|medicine|medical|healthcare|public health)\b"),
    ("arts_or_design", r"\b(arts?|design|graphic design|fine arts)\b"),
]


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


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
    if avg_sentence_words < 14:
        return "concise"
    if avg_sentence_words > 26:
        return "formal"
    return "balanced"


def education_level(text):
    lowered = text.lower()
    for level, pattern in DEGREE_PATTERNS:
        if re.search(pattern, lowered):
            return level
    if re.search(r"\b(education|university|college|degree|diploma)\b", lowered):
        return "education_mentioned_unknown_level"
    return "not_found"


def education_institution_type(text):
    lowered = text.lower()
    if re.search(r"\b(community college|junior college)\b", lowered):
        return "community_college"
    if re.search(r"\b(university|college|institute|school)\b", lowered):
        return "institution_mentioned_unknown_type"
    return "not_found"


def education_field(text):
    lowered = text.lower()
    for field, pattern in FIELD_PATTERNS:
        if re.search(pattern, lowered):
            return field
    if re.search(r"\b(degree|bachelor|master|ph\.?d\.?|university|college)\b", lowered):
        return "field_not_clear"
    return "not_found"


def volunteering_features(text):
    lowered = text.lower()
    if not re.search(r"\b(volunteer|volunteered|volunteering|community service|nonprofit|non-profit|charity)\b", lowered):
        return False, "none_found"
    if re.search(r"\b(board|committee|mentor|coach|tutor)\b", lowered):
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
    if re.search(r"\b(art|music|theater|drama|dance)\b", lowered):
        return True, "arts"
    if re.search(r"\b(student organization|club|society|fraternity|sorority)\b", lowered):
        return True, "clubs_or_academic"
    return True, "other"


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


def explicit_nationality(text):
    lowered = text.lower()
    if re.search(r"\b(nationality|citizenship|citizen of)\b", lowered):
        return "explicitly_stated_or_mentioned"
    if re.search(r"\bauthorized to work\b", lowered):
        return "work_authorization_mentioned"
    return "unknown"


def load_protected_labels(path):
    if not path:
        return None

    labels = pd.read_csv(path)
    if "resume_id" not in labels.columns:
        raise ValueError("Protected label file must contain a 'resume_id' column.")

    allowed = ["resume_id", *PROTECTED_COLUMNS]
    return labels[[column for column in allowed if column in labels.columns]].copy()


def apply_protected_labels(features, labels):
    if labels is None:
        return features

    merged = features.merge(labels, on="resume_id", how="left", suffixes=("", "_label"))
    for column in PROTECTED_COLUMNS:
        label_column = f"{column}_label"
        if label_column in merged.columns:
            merged[column] = merged[label_column].fillna(merged[column])
            merged.drop(columns=[label_column], inplace=True)
    return merged


def build_features(df, labels=None):
    records = []
    for _, row in df.iterrows():
        text = clean_text(row.get(TEXT_COLUMN, ""))
        words = word_count(text)
        action_count = count_terms(text, ACTION_TERMS)
        leadership_count = count_terms(text, LEADERSHIP_TERMS)
        language_group, language_count, languages_found = language_features(text)
        volunteering_present, volunteering_type = volunteering_features(text)
        extracurricular_present, extracurricular_type = extracurricular_features(text)

        records.append({
            "resume_id": row.get(ID_COLUMN),
            "resume_category": row.get(CATEGORY_COLUMN),
            "hiring_outcome": pd.NA,
            "outcome_kind": "not_provided",
            "gender": "not_collected",
            "ethnicity": "not_collected",
            "age_group": explicit_age_group(text),
            "nationality": explicit_nationality(text),
            "protected_attribute_source": "explicit_labels_only",
            "language_group": language_group,
            "language_count": language_count,
            "languages_found": languages_found,
            "volunteering_present": volunteering_present,
            "volunteering_type": volunteering_type,
            "extracurricular_present": extracurricular_present,
            "extracurricular_type": extracurricular_type,
            "education_level": education_level(text),
            "education_institution_type": education_institution_type(text),
            "education_field": education_field(text),
            "writing_style": writing_style(text, words, action_count),
            "leadership_word_count": leadership_count,
            "leadership_language_group": group_count(leadership_count, 3, 8),
            "resume_word_count": words,
            "resume_length_group": bucket_resume_length(words),
            "action_word_count": action_count,
        })

    features = pd.DataFrame(records)
    return apply_protected_labels(features, labels)


def normalize_outcome(series):
    positive = {"1", "yes", "true", "selected", "shortlisted", "interview", "interviewed", "hired", "pass"}
    negative = {"0", "no", "false", "rejected", "not_selected", "not shortlisted", "not_shortlisted", "fail"}

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any() and not numeric.dropna().isin([0, 1]).all():
        return numeric.astype("Float64"), "score"

    def convert(value):
        if pd.isna(value):
            return pd.NA
        text = str(value).strip().lower()
        if text in positive:
            return 1
        if text in negative:
            return 0
        return pd.NA

    return series.map(convert).astype("Float64"), "selection"


def summarize_audit(features, outcome_kind):
    group_columns = PROTECTED_COLUMNS + CONTENT_COLUMNS + STYLE_COLUMNS
    overall = features["hiring_outcome"].mean() if outcome_kind in {"selection", "score"} else pd.NA
    summaries = []

    for column in group_columns:
        grouped = features.groupby(column, dropna=False)
        summary = grouped.size().reset_index(name="resume_count").rename(columns={column: "group_value"})
        summary.insert(0, "group_type", column)

        if outcome_kind == "selection":
            rates = grouped["hiring_outcome"].mean().reset_index(name="selection_rate").rename(columns={column: "group_value"})
            summary = summary.merge(rates, on="group_value", how="left")
            summary["gap_from_overall"] = summary["selection_rate"] - overall
        elif outcome_kind == "score":
            rates = grouped["hiring_outcome"].mean().reset_index(name="average_score").rename(columns={column: "group_value"})
            summary = summary.merge(rates, on="group_value", how="left")
            summary["gap_from_overall"] = summary["average_score"] - overall
        else:
            summary["selection_rate"] = pd.NA
            summary["average_score"] = pd.NA
            summary["gap_from_overall"] = pd.NA

        summaries.append(summary)

    return pd.concat(summaries, ignore_index=True)


def summarize_categories(features):
    summaries = []
    for column in CONTENT_COLUMNS + STYLE_COLUMNS:
        summary = (
            features.groupby(["resume_category", column], dropna=False)
            .size()
            .reset_index(name="resume_count")
            .rename(columns={column: "group_value"})
        )
        summary.insert(1, "group_type", column)
        summaries.append(summary)
    return pd.concat(summaries, ignore_index=True)


def proxy_summary(features, min_group_size=30):
    rows = []
    proxy_columns = CONTENT_COLUMNS + STYLE_COLUMNS

    for protected in PROTECTED_COLUMNS:
        known = features[~features[protected].isin(["unknown", "not_collected", "not_inferable"])]
        group_sizes = known[protected].value_counts(dropna=True)
        comparable_groups = group_sizes[group_sizes >= min_group_size].index
        comparable = known[known[protected].isin(comparable_groups)]

        if comparable[protected].nunique(dropna=True) < 2:
            rows.append({
                "protected_attribute": protected,
                "proxy_feature": "all",
                "status": "not_testable",
                "detail": f"Fewer than two explicit protected groups have at least {min_group_size} resumes.",
            })
            continue

        for proxy in proxy_columns:
            table = pd.crosstab(comparable[protected], comparable[proxy], normalize="index")
            max_gap = (table.max(axis=0) - table.min(axis=0)).max()
            rows.append({
                "protected_attribute": protected,
                "proxy_feature": proxy,
                "status": "review" if max_gap >= 0.20 else "no_large_gap_found",
                "detail": f"largest_distribution_gap={max_gap:.3f}",
            })

    return pd.DataFrame(rows)


def write_notes(features, outcome_kind, outcome_column, protected_labels_path):
    known_protected = {
        column: int((~features[column].isin(["unknown", "not_collected", "not_inferable"])).sum())
        for column in PROTECTED_COLUMNS
    }
    lines = [
        "# Audit Notes",
        "",
        f"Total resumes processed: {len(features):,}",
        "",
        "## What This Pipeline Does",
        "",
        "Creates one row per resume with protected attributes, resume-content attributes, and style/format attributes.",
        "Protected attributes are kept for auditing only and are not decision features.",
        "",
        "## Protected Attribute Handling",
        "",
        "- Gender and ethnicity are not inferred from names, photos, schools, wording, or languages.",
        "- Age is grouped only when an explicit age phrase is present; otherwise it is `unknown`.",
        "- Nationality is flagged only when nationality, citizenship, or work authorization is explicitly mentioned; otherwise it is `unknown`.",
        "- For serious fairness testing, provide a separate protected-label CSV using `--protected-labels`.",
        "",
        "Known explicit protected values in this run:",
        *(f"- {column}: {count}" for column, count in known_protected.items()),
        "",
        "## Outcome Status",
        "",
    ]

    if outcome_kind == "selection":
        lines.extend([
            f"Outcome column used: `{outcome_column}`",
            "Selection rates and gaps from the overall rate were written to `fairness_audit_summary.csv`.",
        ])
    elif outcome_kind == "score":
        lines.extend([
            f"Outcome column used: `{outcome_column}`",
            "Average scores and gaps from the overall average were written to `fairness_audit_summary.csv`.",
        ])
    else:
        lines.extend([
            "No real hiring outcome column was provided.",
            "The outputs are ready for grouping and proxy review, but they cannot prove hiring bias until a shortlist, reject, interview, ranking, job-fit, or score column is added.",
        ])

    lines.extend([
        "",
        "## Files",
        "",
        "- `resume_feature_table.csv`: one row per resume using the requested audit schema",
        "- `fairness_audit_summary.csv`: group counts plus outcome rates/gaps when an outcome exists",
        "- `proxy_summary.csv`: checks whether content/style features vary strongly by explicit protected groups",
        "- `category_group_summary.csv`: descriptive category distribution only; category is not treated as a hiring outcome",
        "- `mitigation_recommendations.md`: Stage 2 mitigation guidance",
    ])

    if protected_labels_path:
        lines.extend(["", f"Protected labels file used: `{protected_labels_path}`"])

    (OUTPUT_DIR / "audit_notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mitigation_recommendations():
    lines = [
        "# Mitigation Recommendations",
        "",
        "Use this after the audit identifies gaps. These recommendations should be reviewed with legal, HR, and domain experts before deployment.",
        "",
        "## Do Not Use Directly",
        "",
        "- gender",
        "- ethnicity",
        "- age_group",
        "- nationality",
        "",
        "## Normalize Or Down-Weight Proxy Features",
        "",
        "- Normalize resume length so longer resumes do not automatically score higher.",
        "- Separate skills and experience evidence from writing polish.",
        "- Treat volunteering and extracurricular activities as optional context, not core qualification signals.",
        "- Review education prestige or institution type carefully because it can encode socioeconomic or nationality bias.",
        "- Compare leadership-language scoring across explicit protected groups before using it.",
        "",
        "## Safer Decision Features",
        "",
        "- required skills",
        "- years of relevant experience",
        "- certifications",
        "- project relevance",
        "- role-specific evidence",
        "- structured scoring rubrics tied to job requirements",
        "",
        "## Deployment Gate",
        "",
        "Before using any model or ranking system, rerun the audit with real hiring outcomes and protected labels collected through an appropriate consented process.",
    ]
    (OUTPUT_DIR / "mitigation_recommendations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create resume grouping features for bias auditing.")
    parser.add_argument("--input", default=str(INPUT_PATH), help="Path to Resume.csv")
    parser.add_argument("--outcome-column", default=None, help="Optional hiring outcome column")
    parser.add_argument("--protected-labels", default=None, help="Optional CSV with resume_id and explicit protected labels")
    parser.add_argument("--min-proxy-group-size", type=int, default=30, help="Minimum explicit records per protected group for proxy checks")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(args.input)
    labels = load_protected_labels(args.protected_labels)
    features = build_features(df, labels)

    outcome_kind = "not_provided"
    if args.outcome_column:
        if args.outcome_column not in df.columns:
            raise ValueError(f"Outcome column '{args.outcome_column}' was not found in the input CSV.")
        features["hiring_outcome"], outcome_kind = normalize_outcome(df[args.outcome_column])
        features["outcome_kind"] = outcome_kind

    audit_summary = summarize_audit(features, outcome_kind)

    features.to_csv(OUTPUT_DIR / "resume_feature_table.csv", index=False)
    features.to_csv(OUTPUT_DIR / "resume_group_features.csv", index=False)
    audit_summary.to_csv(OUTPUT_DIR / "fairness_audit_summary.csv", index=False)
    audit_summary.to_csv(OUTPUT_DIR / "group_summary.csv", index=False)
    summarize_categories(features).to_csv(OUTPUT_DIR / "category_group_summary.csv", index=False)
    proxy_summary(features, args.min_proxy_group_size).to_csv(OUTPUT_DIR / "proxy_summary.csv", index=False)
    write_notes(features, outcome_kind, args.outcome_column, args.protected_labels)
    write_mitigation_recommendations()

    print(f"Processed {len(features):,} resumes")
    print(f"Outcome kind: {outcome_kind}")
    print(f"Wrote outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
