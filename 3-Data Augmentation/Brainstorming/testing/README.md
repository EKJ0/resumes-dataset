# Resume Grouping Workspace

This folder groups the full cleaned resume dataset using the list of categories requested for bias exploration:

- inferred gender from first name
- explicit age mentions
- explicit nationality/citizenship/work-authorization mentions
- languages
- volunteering
- extracurricular activities
- education level and field
- writing style
- leadership language
- resume length

The current source is the full cleaned TXT dataset:

```text
2-Processing/Resumes/Cleaned Resumes TXT
```

That source contains 8,905 resumes. The older `input/Resume.csv` has only 2,484 rows and is not used by the new grouping pipeline.

## Main Script

```text
scripts/build_resume_groups.py
```

Run from the project root:

```powershell
.\.venv\Scripts\python.exe "3-Data Augmentation\Brainstorming\testing\scripts\build_resume_groups.py"
```

Or from this folder:

```powershell
..\..\..\.venv\Scripts\python.exe scripts\build_resume_groups.py
```

## Gender Grouping

Gender is inferred from the extracted first name and:

```text
2-Processing/First Names/first_names_clean.csv
```

The output column is deliberately named:

```text
inferred_gender_from_name
```

This is an estimate, not a confirmed protected attribute.

Default logic:

```text
if first-name gender_probability >= 0.85:
    male_high_confidence or female_high_confidence
else:
    unknown_or_low_confidence
```

You can change the threshold:

```powershell
.\.venv\Scripts\python.exe "3-Data Augmentation\Brainstorming\testing\scripts\build_resume_groups.py" --gender-threshold 0.90
```

## Outputs

- `input/source_manifest.csv`: all cleaned TXT files used as input
- `outputs/all_resume_group_features.csv`: one row per resume with all grouping columns
- `outputs/group_counts_summary.csv`: counts for all major groups
- `outputs/gender_group_summary.csv`: inferred-gender breakdowns
- `outputs/category_group_summary.csv`: category breakdowns
- `outputs/education_group_summary.csv`: education breakdowns
- `outputs/language_group_summary.csv`: language breakdowns
- `outputs/proxy_risk_summary.csv`: possible proxy-risk checks
- `outputs/README_RESULTS.md`: readable summary of the run

## Important Limit

These files group resumes. They do not prove hiring bias unless you add a real hiring outcome such as selected, rejected, interview, score, ranking, or job-fit decision.
