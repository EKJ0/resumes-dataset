# Mitigation Recommendations

Use this after the audit identifies gaps. These recommendations should be reviewed with legal, HR, and domain experts before deployment.

## Do Not Use Directly

- gender
- ethnicity
- age_group
- nationality

## Normalize Or Down-Weight Proxy Features

- Normalize resume length so longer resumes do not automatically score higher.
- Separate skills and experience evidence from writing polish.
- Treat volunteering and extracurricular activities as optional context, not core qualification signals.
- Review education prestige or institution type carefully because it can encode socioeconomic or nationality bias.
- Compare leadership-language scoring across explicit protected groups before using it.

## Safer Decision Features

- required skills
- years of relevant experience
- certifications
- project relevance
- role-specific evidence
- structured scoring rubrics tied to job requirements

## Deployment Gate

Before using any model or ranking system, rerun the audit with real hiring outcomes and protected labels collected through an appropriate consented process.
