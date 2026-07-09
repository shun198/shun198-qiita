# qiita-list-ignore-publish

## Goal

List all Qiita article files whose front matter contains `ignorePublish: true` and present them as a Markdown table.

## Required Command

```bash
python3 scripts/list_ignore_publish_articles.py
```

## Workflow

1. Run the helper script from the repository root
2. Read `public/*.md`
3. Filter articles where `ignorePublish: true`
4. Return a Markdown table with file name, title, private flag, updated date, and tags

## Output Format

```markdown
| File | Title | Private | Updated | Tags |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... |
```

## Guardrails

- Treat this as a read-only inspection task
- Do not change article contents while listing
- If no matching files exist, report that clearly instead of failing
