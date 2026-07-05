# qiita-article-filename-convention

## Goal

Create Qiita article files with human-readable names instead of UUID-like names.

## Naming Rules

1. Use `kebab-case`
2. Allow only lowercase letters, numbers, and hyphens
3. No leading/trailing hyphen
4. No consecutive hyphens
5. Keep slug reasonably short (about 60 chars)

## Workflow

1. Generate 3 slug candidates from the article title
2. Check duplicates in `public/*.md`
3. Pick one valid slug
4. Run `pnpm exec qiita new <slug>`
5. Update front matter (`title`, `tags`, `private`)

## Guardrails

- Do not create new articles with UUID-like names
- Do not use spaces or Japanese characters in file names
- Do not rename existing published files casually
- Do not edit existing article front matter `id`
