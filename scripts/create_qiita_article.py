#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


TAG_RULES = [
    (("fastapi",), "FastAPI"),
    (("mcp", "model context protocol"), "MCP"),
    (("django", "django-rest-framework", "drf"), "Django"),
    (("react", "react hook form", "react-hook-form"), "React"),
    (("next.js", "nextjs"), "Next.js"),
    (("nestjs", "nest.js"), "NestJS"),
    (("storybook",), "storybook"),
    (("terraform",), "Terraform"),
    (("cloudformation",), "CloudFormation"),
    (("github actions", "github-actions", "workflow"), "GitHubActions"),
    (("docker", "dockerfile", "docker-compose"), "Docker"),
    (("kubernetes", "kind", "argo", "argocd", "argo workflows"), "Kubernetes"),
    (("python", "pytest", "pydantic", "alembic"), "Python"),
    (("golang", "go ", "gin", "gorm", "echo"), "Go"),
    (("typescript",), "TypeScript"),
    (("javascript",), "JavaScript"),
    (
        (
            "aws",
            "lambda",
            "ecs",
            "s3",
            "rds",
            "route53",
            "cloudfront",
            "eventbridge",
            "sns",
            "sqs",
            "ecr",
            "alb",
            "vpc",
            "waf",
            "ses",
            "dynamodb",
            "cognito",
        ),
        "AWS",
    ),
    (
        (
            "gcp",
            "google cloud",
            "cloud run",
            "pub-sub",
            "pubsub",
            "bigquery",
            "gke",
            "gcs",
            "artifact registry",
            "firestore",
        ),
        "GoogleCloud",
    ),
    (("qiita",), "Qiita"),
]

DEFAULT_TAGS = ["Tips"]
FRONTMATTER_TEMPLATE = """---
title: {title}
tags:
{tags_block}
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: true
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
この記事では {title} について整理します

## 前提
- 動作確認に使う環境を記載してください
- 事前に必要なツールや権限を記載してください

## 構成

## 実装

## 実際に検証してみよう

## まとめ

## 参考
"""


def infer_tags(title: str, max_tags: int) -> list[str]:
    title_lower = f" {title.lower()} "
    tags: list[str] = []

    for keywords, tag in TAG_RULES:
        if any(keyword in title_lower for keyword in keywords):
            tags.append(tag)
        if len(tags) >= max_tags:
            break

    if not tags:
        return DEFAULT_TAGS[:max_tags]

    deduped: list[str] = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return deduped[:max_tags]


def sanitize_filename(title: str) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]", "-", title.strip())
    sanitized = re.sub(r"\s+", "-", sanitized)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-.")
    if not sanitized:
        raise ValueError("title produced an empty file name")
    return sanitized


def resolve_output_path(output_dir: Path, title: str) -> Path:
    base_name = sanitize_filename(title)
    candidate = output_dir / f"{base_name}.md"
    counter = 2

    while candidate.exists():
        candidate = output_dir / f"{base_name}-{counter}.md"
        counter += 1

    return candidate


def build_content(title: str, tags: list[str]) -> str:
    tags_block = "\n".join(f"  - {tag}" for tag in tags)
    return FRONTMATTER_TEMPLATE.format(title=title, tags_block=tags_block)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Qiita draft article from a title."
    )
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument(
        "--output-dir",
        default="public",
        help="Directory where the markdown file will be created",
    )
    parser.add_argument(
        "--max-tags",
        type=int,
        default=5,
        help="Maximum number of inferred tags",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tags = infer_tags(args.title, args.max_tags)
    output_path = resolve_output_path(output_dir, args.title)
    output_path.write_text(build_content(args.title, tags), encoding="utf-8")

    print(f"created: {output_path}")
    print(f"title: {args.title}")
    print(f"tags: {', '.join(tags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
