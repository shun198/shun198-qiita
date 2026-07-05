# tech-writing-qiita

## Goal

Write a Qiita-ready technical article for beginner-to-mid readers, with reproducible steps and practical value.

## Publication Safety Rules

- Never publish publicly (`private: false`)
- Create drafts only (`private: true`) when using Qiita API
- Let the user do the final public publish step manually
- Never modify article front matter `id` values

## Steps

1. Set target audience (default: beginner to mid) and expected outcome
2. Use structure: background -> mechanism -> implementation -> debugging/pitfalls -> summary
3. Separate minimal repro from production-ready examples and explain design choices
4. Add one reader-value line per section
5. Validate assumptions, environment prerequisites, and reproducible steps

## Style Rules

- Use Japanese polite style ("です/ます") consistently
- Explain technical terms briefly at first mention
- Pair strong claims with assumptions or rationale

## Heading Rules

- Use H2/H3 as the default heading depth
- H2 for main sections, H3 for steps/notes/caveats
- Avoid H4+ unless absolutely necessary

## Output Sections

- Title
- What you will learn
- Target audience
- Problem statement
- Mechanism highlights
- Implementation
- Verification
- Debugging / Pitfalls
- Summary
- Suggested tags
- References

## Topic Priorities

- Python / FastAPI
- Terraform
- GitHub Actions
- README / documentation improvements
- Testing and debugging practices

## Tag Priority

1. Python
2. FastAPI
3. Terraform
4. GitHubActions
5. テスト
6. ドキュメント
7. Linux
