---
title: Storybookのコンポーネントの情報をMCPサーバにしてみよう！
tags:
  - TypeScript
  - VSCode
  - MCP
  - storybook
  - copilot
private: false
updated_at: '2025-08-18T07:38:38+09:00'
id: c5ebff43a411bf0d26ab
organization_url_name: null
slide: false
---
## 概要
Storybookのコンポーネントの情報をMCPサーバ化する方法について解説します

## 前提
- Storybookを作成済み
- MCPサーバはTypescriptを使って構築します
- エディタはVSCodeを使用
- MCPクライアントはGitHub Copilotを使用

## ディレクトリ構成
以下のように
- .vscode/mcp.json
- mcp-serverフォルダ配下

にMCPサーバ関連の設定を行います
対象となるStorybookのコンポーネントはapplication/src/stories配下にあります
(実際のコンポーネントやCSSなどは説明の都合上省略してます)

```
tree
.
├── .vscode
│   └── mcp.json
├── application
│   ├── mcp-server
│   │   ├── dist
│   │   ├── node_modules
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── server.ts
│   │   └── tsconfig.json
│   ├── node_modules
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   └── src
│       └── stories
│           ├── Button.stories.ts
│           ├── Header.stories.ts
│           └── Page.stories.ts
└── README.md
```

## 実装
### mcp.jsonの設定
MCPクライアントからMCPサーバを起動させる設定を記載します
今回はローカル上でMCPサーバを直接起動させるので、type(MCPクライアントとMCPサーバ間の通信方法)はstdio(標準入出力、stdin/stdout)を指定します
後述の
また、今回はnodeを使うのでcommandはnodeです

```mcp.json
{
	"servers": {
		"storybook-mcp": {
			"type": "stdio",
			"command": "node",
			"args": ["${workspaceFolder}/application/mcp-server/dist/server.js"],
		}
	},
}

```

### MCPサーバの作成
今回はModel Context Protocolが提供しているTypescript版のSDKを使用します

https://github.com/modelcontextprotocol/typescript-sdk

MCPサーバ起動前に該当するStorybookの一覧を取得し、なければエラーを返します
server.registerToolでコンポーネントの一覧のリンクを返すメソッドを作成します
server.registerToolを通じてLLMがMCPサーバーを通してコンポーネントのresource_linkなどを取得することができます
コンテンツを全て返すのではなく、あくまで参照元を返すイメージです
こうすることで、大きなファイルや大量のリソースを扱うときに必要なリソースだけを選択的に読み取ることができ、パフォーマンスの向上につながるとのことです
今後も開発を続けていく中でリソースが増え続けることを想定して以下のような構成にしています

```server.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ResourceLink } from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const server = new McpServer({ name: "storybook-mcp", version: "1.0.0" });

// dist/server.jsから見たstoriesディレクトリのパス
const storiesDir = path.resolve(__dirname, "../../src/stories");

/**
 * storiesフォルダからコンポーネント一覧を取得する
 */
function loadStoryComponents(): { file: string; componentName: string }[] {
  if (!fs.existsSync(storiesDir)) {
    console.error(`Stories directory not found: ${storiesDir}`);
    process.exit(1);
  }

  const files = fs
    .readdirSync(storiesDir)
    .filter((f) => f.endsWith(".stories.ts") || f.endsWith(".stories.tsx"))
    .map((f) => ({
      file: f,
      componentName: f.replace(/\.stories\.tsx?$/, "")
    }));

  if (files.length === 0) {
    console.error(`No components found in: ${storiesDir}`);
    process.exit(1);
  }

  return files;
}

// ---- 初期化時にロード ----
const storyFiles = loadStoryComponents();

/**
 * storiesフォルダ内のコンポーネント一覧を返す
 */
server.registerTool(
  "getComponents",
  {
    title: "getComponents",
    description: "Get the list of Storybook story files under src/stories",
    inputSchema: {},
  },
  // パフォーマンスのため、resource_linkを使ってファイルのURIを返す
  async () => {
    const content: ResourceLink[] = storyFiles.map((f) => ({
      type: "resource_link",
      uri: `file://${path.join(storiesDir, f.file)}`,
      name: f.componentName,
      mimeType: "text/typescript",
      description: `Story file for component ${f.componentName}`,
    }));
    return {
      content
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### パッケージ群
以下のように必要なパッケージをインストールしましょう

```package.json
{
    "name": "storybook-mcp-server",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "build": "tsc",
        "start": "node dist/server.js",
        "dev": "node --loader ts-node/esm server.ts"
    },
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.17.3",
        "zod": "^3.25.76"
    },
    "devDependencies": {
        "@types/node": "^24.3.0",
        "ts-node": "^10.9.2",
        "typescript": "^5.9.2"
    }
}
```

## 実際に実行してみよう！
jsにコンパイルする必要があるので以下のコマンドを実行してからMCPサーバを起動させましょう

```
npm run build
```

MCPサーバの起動はmcp.jsonを開き、起動ボタンを押すことで実現できます
![Screenshot 2025-08-17 at 22.16.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/afd69f20-c5d3-4c12-b4c1-20c947117770.png)

以下のように起動していることが確認できました
![Screenshot 2025-08-17 at 22.19.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c290f1dd-e330-4abf-893f-5a353f4f9fcf.png)

また、コマンドパレットからMCPサーバの一覧を確認できます
![Screenshot 2025-08-17 at 22.20.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1a0997d5-f72c-466f-9fe5-85235d86a982.png)

Copilotを開き、Agentモードを選択します
![Screenshot 2025-08-17 at 22.21.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b1935862-38bc-4c58-b8fe-2bf268111aa3.png)

ツールの構成から今回作成したMCPサーバとgetComponentsがあることが確認できました
![Screenshot 2025-08-17 at 22.22.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a644a27d-80a9-4563-a352-515a607828f6.png)

試しに今回作成したgetComponentsを使ってStorybookのコンポーネントの一覧を取得し、Footerコンポーネントを作成させてみます
プロンプトはChatGPTに書かせてみました

```
あなたは MCP サーバーから取得した Storybook コンポーネント情報をもとに、新しい React コンポーネントを作るアシスタントです。

入力:
- MCP サーバーの "getComponents" から取得した `resource_link` 配列
- 各要素は `uri`, `name`, `mimeType`, `description` を持っています
- これらのリンク先にある Storybook ファイルを参照することで、既存コンポーネントの命名規則や構成パターンを確認できます

目的:
- この情報をもとに、新規コンポーネント `Footer` を作成する
- Footer コンポーネントは既存コンポーネントの命名規則や props 構成を踏襲する

ルール:
1. コンポーネント名は `Footer` とする
2. 既存コンポーネントの props の型やイベントハンドラのパターンを参考に、Footer に必要な props を設計する
3. TypeScript で型定義を含む React コンポーネントを生成する
4. 出力は **直接使えるコード** とする。説明文や解説は不要
5. Footer 内にボタンやリンクがあれば、適切にイベントハンドラ（onClick など）も追加する

出力形式:
- 1 ファイル分の TypeScript React コンポーネントコード
- ファイル名は `Footer.tsx` として保存可能な状態

指示:
- まず `getComponents` のリソースリンクを参照して、既存の命名規則や構成を把握する
- それを元に Footer コンポーネントを作成する
- コードのみを出力する
```

![Screenshot 2025-08-17 at 22.25.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/318e511c-2caf-4b0e-b6a2-9737843595eb.png)

このようにgetComponentsを実行し、application/src/stories配下のStorybookのresource_linkの取得に成功しました

![Screenshot 2025-08-17 at 22.25.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e2112574-57b4-44b3-a18b-a0dd6375c134.png)

コンポーネントもいい感じに作成できましたね
![Screenshot 2025-08-17 at 22.26.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a0f0263c-d3fb-4031-a1a6-598dee83aaaa.png)

## まとめ
今までのLLMだとプロジェクト全体のソースコードの構成やルールなどを踏まえたコーディングに課題がありましたが今後MCPサーバを自分でたてて生成AIの精度をより高めていくことが増えてきそうな気がしてます
今回の検証だとコンポーネントが少なかったですが今後大量のコンポーネントが増えたり複雑になってきたときによりLLMの精度も上がってメリットを感じやすくなるのでは？と勝手に思ってます

## 参考
https://github.com/modelcontextprotocol/typescript-sdk

https://zenn.dev/layerx/articles/7e9f87fca65e94

https://developers.play.jp/entry/2025/06/20/191042

https://zenn.dev/takuya77088/articles/f7149723b3b2f2
