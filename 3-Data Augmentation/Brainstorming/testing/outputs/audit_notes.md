# Audit Notes

Total resumes processed: 2,484

## What This Pipeline Does

Creates one row per resume with protected attributes, resume-content attributes, and style/format attributes.
Protected attributes are kept for auditing only and are not decision features.

## Protected Attribute Handling

- Gender and ethnicity are not inferred from names, photos, schools, wording, or languages.
- Age is grouped only when an explicit age phrase is present; otherwise it is `unknown`.
- Nationality is flagged only when nationality, citizenship, or work authorization is explicitly mentioned; otherwise it is `unknown`.
- For serious fairness testing, provide a separate protected-label CSV using `--protected-labels`.

Known explicit protected values in this run:
- gender: 0
- ethnicity: 0
- age_group: 20
- nationality: 61

## Outcome Status

No real hiring outcome column was provided.
The outputs are ready for grouping and proxy review, but they cannot prove hiring bias until a shortlist, reject, interview, ranking, job-fit, or score column is added.

## Files

- `resume_feature_table.csv`: one row per resume using the requested audit schema
- `fairness_audit_summary.csv`: group counts plus outcome rates/gaps when an outcome exists
- `proxy_summary.csv`: checks whether content/style features vary strongly by explicit protected groups
- `category_group_summary.csv`: descriptive category distribution only; category is not treated as a hiring outcome
- `mitigation_recommendations.md`: Stage 2 mitigation guidance
