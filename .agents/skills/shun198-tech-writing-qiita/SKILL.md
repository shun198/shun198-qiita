---
name: shun198-tech-writing-qiita
description: このリポジトリ向けのQiita技術記事を構成、執筆、推敲し、タイトルやタグを選定する。初級から中級の読者へ再現可能な実装とデバッグ手順を説明する記事作成で使う。
---

# Tech Writing For Qiita

## Workflow

1. 想定読者を初級から中級に設定し、到達目標を明記する
2. 「背景、仕組み、実装、動作確認、デバッグ、まとめ」の順に構成する
3. コード例は最小再現と実運用例を分け、設計理由を説明する
4. 前提条件、実行環境、再現手順、失敗時の確認点を検証する
5. `shun198-md-lint-after-create`に従って記事を検証する

## Writing Rules

- です・ます調を使う
- 専門用語は初出時に短く説明する
- 断定には根拠または前提を添える
- 見出しはH2とH3を基本とし、H4以降を避ける

## Publication Safety

- 記事作成では`ignorePublish: true`を維持する
- publishやpushは`shun198-qiita-publish-with-approval`に従う
- 既存記事のFront Matterにある`id`を変更しない
