# md-lint-after-create

## Goal

Always run lint checks immediately after creating or editing a Markdown file.

## Required Commands

For a changed file `<file>.md`:

```bash
CI=true pnpm exec markdownlint-cli2 "<file>.md"
CI=true pnpm exec textlint "<file>.md"
```

## Workflow

1. Identify changed Markdown files
2. Run markdownlint for each target file
3. Run textlint for each target file
4. Fix all violations
5. Re-run both checks until they pass

## Guardrails

- Run file-scoped checks instead of whole-repo lint by default
- Do not ignore lint failures
- Never modify front matter `id` in existing articles
