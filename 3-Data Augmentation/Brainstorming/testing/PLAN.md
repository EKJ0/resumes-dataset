# Full Resume Grouping Plan

## Goal

Create a usable grouping dataset from all 8,905 cleaned resumes, not the smaller 2,484-row CSV.

Each resume becomes one row with:

- file identity
- original and cleaned job category
- inferred gender from first name
- explicit age/nationality signals
- resume-content features
- writing/style features

## Source Data

Primary resume source:

```text
2-Processing/Resumes/Cleaned Resumes TXT
```

First-name gender source:

```text
2-Processing/First Names/first_names_clean.csv
```

The older file below is kept only as a reference and is not used:

```text
3-Data Augmentation/Brainstorming/testing/input/Resume.csv
```

## Grouping Columns

### Sensitive Or Protected-Like Columns

These are for grouping and auditing only:

- `inferred_gender_from_name`
- `inferred_gender_confidence`
- `age_group_explicit`
- `nationality_or_citizenship_mentioned`
- `nationality_group_explicit`

Gender is inferred only from the extracted first name. Because this is not confirmed gender, it must stay labeled as inferred.

### Resume Content Columns

- `language_group`
- `language_count`
- `languages_found`
- `volunteering_present`
- `volunteering_type`
- `extracurricular_present`
- `extracurricular_type`
- `education_level`
- `education_field`
- `leadership_word_count`
- `leadership_language_group`

### Style And Format Columns

- `writing_style`
- `resume_word_count`
- `resume_length_group`
- `action_word_count`

## Best Practical Approach

Use high-confidence inferred gender groups:

```text
male_high_confidence
female_high_confidence
unknown_or_low_confidence
unknown_or_no_name
```

Default threshold:

```text
gender_probability >= 0.85
```

This gives useful grouping while keeping the limitations visible.

## What The Outputs Are For

Use `all_resume_group_features.csv` to filter or analyze resumes by any grouping column.

Use the summary files to answer questions such as:

- How many resumes are inferred male/female/unknown?
- Which categories have more unknown gender inference?
- Which resumes mention multiple languages?
- Which resumes mention volunteering or extracurriculars?
- Which education levels are most common by category?
- Does writing style or resume length differ by inferred gender?

## What The Outputs Are Not For

Do not use inferred gender, age, or nationality columns for hiring decisions.

Do not call this a final bias audit unless a real hiring outcome is added:

- selected/rejected
- shortlisted/not shortlisted
- interview/no interview
- model score
- ranking
- job-fit decision
