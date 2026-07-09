#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def parse_frontmatter(article_path: Path) -> dict[str, object]:
    lines = article_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, object] = {}
    index = 1
    current_list_key: str | None = None
    current_list: list[str] = []

    while index < len(lines):
        line = lines[index]
        index += 1

        if line.strip() == "---":
            if current_list_key is not None:
                data[current_list_key] = current_list
            break

        if current_list_key and line.startswith("  - "):
            current_list.append(normalize_scalar(line[4:].strip()))
            continue

        if current_list_key is not None:
            data[current_list_key] = current_list
            current_list_key = None
            current_list = []

        if ":" not in line:
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value == "":
            current_list_key = key
            current_list = []
            continue

        data[key] = normalize_scalar(value)

    return data


def normalize_scalar(value: str) -> object:
    if value in {"true", "false"}:
        return value == "true"
    if value == "null":
        return None
    if value == "''":
        return ""
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def build_markdown_table(rows: list[dict[str, str]]) -> str:
    header = "| File | Title | Private | Updated | Tags |"
    divider = "| --- | --- | --- | --- | --- |"
    body = [
        f"| {row['file']} | {row['title']} | {row['private']} | {row['updated_at']} | {row['tags']} |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List Qiita articles with ignorePublish: true as a markdown table."
    )
    parser.add_argument(
        "--articles-dir",
        default="public",
        help="Directory containing Qiita article markdown files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    articles_dir = Path(args.articles_dir)
    rows: list[dict[str, str]] = []

    for article_path in sorted(articles_dir.glob("*.md")):
        frontmatter = parse_frontmatter(article_path)
        if frontmatter.get("ignorePublish") is not True:
            continue

        tags = frontmatter.get("tags") or []
        rows.append(
            {
                "file": article_path.name,
                "title": str(frontmatter.get("title") or "-"),
                "private": "true" if frontmatter.get("private") is True else "false",
                "updated_at": str(frontmatter.get("updated_at") or "-"),
            "tags": ", ".join(str(tag) for tag in tags if tag) or "-",
        }
    )

    if not rows:
        print("No articles found with ignorePublish: true")
        return 0

    print(build_markdown_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
