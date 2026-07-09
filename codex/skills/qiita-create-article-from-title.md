# qiita-create-article-from-title

## Goal

Create a new Qiita draft article from a user-provided title, with a title-derived Markdown file name, matching front matter title, a reusable template body, and auto-inferred tags.

## Required Command

```bash
python3 scripts/create_qiita_article.py --title "<article title>"
```

## Workflow

1. Get the article title from the user
2. Run the helper script from the repository root
3. Review the generated file path and inferred tags
4. Keep the generated draft defaults: `private: true`, `ignorePublish: true`, `id: null`
5. Run file-scoped lint for the new file

## Generated Defaults

- File path: `public/<title-derived-name>.md`
- Front matter `title`: exactly the user-provided title
- Front matter `tags`: inferred from title keywords
- Body template:
  - `## 概要`
  - `## 対象読者`
  - `## 前提`
  - `## やりたいこと`
  - `## 手順`
  - `## 確認結果`
  - `## ハマりどころ`
  - `## まとめ`
  - `## 参考`

## Post-Create Checks

For the generated file `<file>.md`, run:

```bash
CI=true pnpm exec markdownlint-cli2 "public/<file>.md"
CI=true pnpm exec textlint "public/<file>.md"
```

## Guardrails

- Do not overwrite an existing article file
- Do not modify `id` in existing articles
- Do not publish or push to Qiita as part of article creation
- Only adjust inferred tags when the title context makes them clearly wrong
