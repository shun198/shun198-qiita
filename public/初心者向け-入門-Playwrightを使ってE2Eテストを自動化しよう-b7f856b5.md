---
title: '[初心者向け] [入門] Playwrightを使ってE2Eテストを自動化しよう！'
tags:
  - TypeScript
  - GitHubActions
  - Playwright
private: false
updated_at: '2026-06-21T14:01:44+09:00'
id: b7f856b55f872f5913f5
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Microsoftが開発したWebブラウザの自動操作・テスト用オープンソースフレームワークとしてPlaywrightが有名です
Playwrightを使えばUI上のE2Eテストなどを自動化できるので今回はPlaywrightの使用方法について解説します

## 前提
- Playwrightをインストール済み
- Typescript/React/Next.jsをある程度使用したことがある

## ディレクトリ構成
```
.
├── README.md
├── app
│   ├── error
│   │   └── page.tsx
│   ├── layout.tsx
│   ├── page.tsx
│   └── thanks
│       └── page.tsx
├── next-env.d.ts
├── next.config.mjs
├── package-lock.json
├── package.json
├── playwright-report
├── playwright.config.js
├── tests
│   ├── error.spec.ts
│   └── form.spec.ts
└── tsconfig.json
```

## 今回テストするUI
テスト用に簡易的なUIを作成しました
構成としては以下のとおりです
- お問い合わせフォーム
- 遷移テスト用のサンクスページ
- スクショ取得テスト用のエラーページ

![Screenshot 2026-06-21 at 10.10.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/667b779e-c057-495d-8297-2e03b6e78af8.png)


### お問い合わせフォーム
```app/page.tsx
"use client";

import Link from "next/link";
import { useState } from "react";
import type { ComponentProps } from "react";

type FormSubmitEvent = Parameters<
  NonNullable<ComponentProps<"form">["onSubmit"]>
>[0];

export default function Page() {
  const [submittedName, setSubmittedName] = useState("");

  const handleSubmit = (event: FormSubmitEvent) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const name = formData.get("name");
    setSubmittedName(typeof name === "string" ? name : "");
  };

  return (
    <main style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>お問い合わせフォーム</h1>
      <p>Playwright の練習用に作成したシンプルなフォームです。</p>
      <p>
        ページ遷移テスト用に{" "}
        <Link href="/thanks">サンクスページへ</Link>
      </p>
      <p>
        エラー画面テスト用に <Link href="/error">エラーページへ</Link>
      </p>

      <form onSubmit={handleSubmit} aria-label="contact form">
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="name">名前</label>
          <br />
          <input id="name" name="name" type="text" required />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label htmlFor="email">メールアドレス</label>
          <br />
          <input id="email" name="email" type="email" required />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label htmlFor="message">メッセージ</label>
          <br />
          <textarea id="message" name="message" rows={4} required />
        </div>

        <fieldset style={{ marginBottom: 12 }}>
          <legend>お問い合わせ種別</legend>
          <label htmlFor="contact-general">
            <input
              id="contact-general"
              name="contactType"
              type="radio"
              value="general"
              required
            />{" "}
            一般
          </label>
          <br />
          <label htmlFor="contact-support">
            <input id="contact-support" name="contactType" type="radio" value="support" />{" "}
            サポート
          </label>
        </fieldset>

        <div style={{ marginBottom: 12 }}>
          <label htmlFor="agree">
            <input id="agree" name="agree" type="checkbox" required /> 利用規約に同意する
          </label>
        </div>

        <button type="submit">送信</button>
      </form>

      {submittedName ? (
        <p role="status" style={{ marginTop: 20 }}>
          {submittedName}さん、お問い合わせありがとうございます。
        </p>
      ) : null}
    </main>
  );
}
```

```app/layout.tsx
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Playwright Practice Form",
  description: "Simple Next.js form for Playwright practice"
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
```

### 遷移テスト用のサンクスページ
```app/thanks/page.tsx
import Link from "next/link";

export default function ThanksPage() {
  return (
    <main style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>サンクスページ</h1>
      <p>ページ遷移の確認用に用意したページです。</p>
      <Link href="/">フォームページに戻る</Link>
    </main>
  );
}
```

### スクショ取得テスト用のエラーページ
```app/error/page.tsx
import Link from "next/link";

export default function ErrorPage() {
  return (
    <main style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>エラーが発生しました</h1>
      <p>しばらく時間をおいてから再度お試しください。</p>
      <Link href="/">フォームページに戻る</Link>
    </main>
  );
}
```

## Playwrightのconfig
テスト実行時にフォームアプリを起動するようwebServerの設定を行います
また、テストコードは/testsに配置しているのでtestDirの設定も行います

```playwright.config.js
// @ts-check
const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["list"], ["html", { open: "never" }]],
  webServer: {
    command: "npm run dev -- --hostname 0.0.0.0 --port 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  },
  use: {
    baseURL: "http://127.0.0.1:3000",
    headless: true,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
```

## フォームのテスト
```tests/form.spec.ts
import { expect, test } from "@playwright/test";

test.describe("お問い合わせフォーム", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("サンクスページへ遷移できる", async ({ page }) => {
    await page.getByRole("link", { name: "サンクスページへ" }).click();

    await expect(page).toHaveURL("/thanks");
    await expect(page.getByRole("heading", { name: "サンクスページ" })).toBeVisible();
  });

  test("初期表示では完了メッセージが出ていない", async ({ page }) => {
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test("フォーム送信後に完了メッセージが表示される", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("Playwright の練習中です。");
    await page.getByLabel("一般").check();
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();

    await expect(page.getByRole("status")).toContainText(
      "田中太郎さん、お問い合わせありがとうございます。"
    );
  });

  test("必須項目が空だと送信されない", async ({ page }) => {
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("名前未入力の送信テスト");
    await page.getByLabel("一般").check();
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();

    const nameIsValid = await page
      .getByLabel("名前")
      .evaluate((element) => (element as HTMLInputElement).checkValidity());
    expect(nameIsValid).toBe(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test("メール形式が不正だと送信されない", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("invalid-mail");
    await page.getByLabel("メッセージ").fill("メール形式エラーのテスト");
    await page.getByLabel("一般").check();
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();

    const emailIsValid = await page
      .getByLabel("メールアドレス")
      .evaluate((element) => (element as HTMLInputElement).checkValidity());
    expect(emailIsValid).toBe(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test("連続送信すると最新の名前でメッセージが更新される", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("1回目");
    await page.getByLabel("一般").check();
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();
    await expect(page.getByRole("status")).toContainText(
      "田中太郎さん、お問い合わせありがとうございます。"
    );

    await page.getByLabel("名前").fill("佐藤花子");
    await page.getByLabel("メッセージ").fill("2回目");
    await page.getByRole("button", { name: "送信" }).click();
    await expect(page.getByRole("status")).toContainText(
      "佐藤花子さん、お問い合わせありがとうございます。"
    );
  });

  test("利用規約の同意チェックが未選択だと送信されない", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("チェックボックス必須のテスト");
    await page.getByLabel("一般").check();
    await page.getByRole("button", { name: "送信" }).click();

    const agreeIsValid = await page
      .getByLabel("利用規約に同意する")
      .evaluate((element) => (element as HTMLInputElement).checkValidity());
    expect(agreeIsValid).toBe(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });

  test("お問い合わせ種別が未選択だと送信されない", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("ラジオボタン必須のテスト");
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();

    const contactTypeIsValid = await page
      .getByLabel("一般")
      .evaluate((element) => (element as HTMLInputElement).checkValidity());
    expect(contactTypeIsValid).toBe(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });
});
```

1つずつ解説していきます

### beforeEach
テストを実行する前に実施しない共通処理を書く際に使用します
今回だとルートページに遷移する共通処理を定義してます

```ts
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });
```

https://playwright.dev/docs/api/class-test#test-before-each

PlaywrightにはPageクラスがあり、このクラス内のメソッドで特定のページへ遷移したり、DOM内の要素を取得することができます

https://playwright.dev/docs/api/class-page

例えば下記テストだとPageクラスのgetByRoleメソッドでサンクスページリンクというリンクをクリックし、
- /thanksへ遷移すること
- /thanks内のheadingというRoleが存在すること

を期待するテストになります

```ts
  test("サンクスページへ遷移できる", async ({ page }) => {
    await page.getByRole("link", { name: "サンクスページへ" }).click();

    await expect(page).toHaveURL("/thanks");
    await expect(page.getByRole("heading", { name: "サンクスページ" })).toBeVisible();
  });
```

クリックメソッド、toHaveURLなどのPageに関するassertion関数の詳細は以下の通りです

https://playwright.dev/docs/api/class-locator#locator-click

https://playwright.dev/docs/api/class-pageassertions#page-assertions-to-have-url

該当するLabelを取得する場合はPageクラスのgetByLabelメソッドから取得できます

https://playwright.dev/docs/api/class-framelocator#frame-locator-get-by-label

チェックボックスにチェックをつけるはcheck()メソッド、文字列を入力する場合はfill()メソッド、ボタンをクリックする場合はclick()メソッドを使用します

https://playwright.dev/docs/api/class-locator#locator-check

https://playwright.dev/docs/api/class-locator#locator-fill

https://playwright.dev/docs/api/class-locator#locator-click

```ts
  test("フォーム送信後に完了メッセージが表示される", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("Playwright の練習中です。");
    await page.getByLabel("一般").check();
    await page.getByLabel("利用規約に同意する").check();
    await page.getByRole("button", { name: "送信" }).click();

    await expect(page.getByRole("status")).toContainText(
      "田中太郎さん、お問い合わせありがとうございます。"
    );
  });
```

下記テストでは`利用規約に同意する`にチェックがついていないことをevaluateメソッドを使ってJS(checkValidityメソッド)を実行することで確認してます

また、toHaveCountでstatusを持つDOMが0件であることを確認してます

https://developer.mozilla.org/ja/docs/Web/API/HTMLInputElement/checkValidity

https://playwright.dev/docs/api/class-locatorassertions#locator-assertions-to-have-count

```ts
  test("利用規約の同意チェックが未選択だと送信されない", async ({ page }) => {
    await page.getByLabel("名前").fill("田中太郎");
    await page.getByLabel("メールアドレス").fill("taro@example.com");
    await page.getByLabel("メッセージ").fill("チェックボックス必須のテスト");
    await page.getByLabel("一般").check();
    await page.getByRole("button", { name: "送信" }).click();

    const agreeIsValid = await page
      .getByLabel("利用規約に同意する")
      .evaluate((element) => (element as HTMLInputElement).checkValidity());
    expect(agreeIsValid).toBe(false);
    await expect(page.getByRole("status")).toHaveCount(0);
  });
```

## エラーページのテスト
```tests/error.spec.ts
import { expect, test } from "@playwright/test";

type ErrorCategory = "retry_later" | "maintenance" | "unknown";

function classifyErrorMessage(message: string): ErrorCategory {
  if (/時間をおいて|再度お試し/.test(message)) {
    return "retry_later";
  }

  if (/メンテナンス|保守/.test(message)) {
    return "maintenance";
  }

  return "unknown";
}

test.describe("エラー画面", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/error");
  });

  test("エラーメッセージが表示される", async ({ page }) => {
    await expect(page).toHaveURL("/error");
    await expect(page.getByRole("heading", { name: "エラーが発生しました" })).toBeVisible();
    await expect(page.getByText("しばらく時間をおいてから再度お試しください。")).toBeVisible();
  });

  test("フォームページに戻れる", async ({ page }) => {
    await page.getByRole("link", { name: "フォームページに戻る" }).click();

    await expect(page).toHaveURL("/");
    await expect(page.getByRole("heading", { name: "お問い合わせフォーム" })).toBeVisible();
  });

  test("エラー文言に応じて処理を分岐しスクリーンショットを保存できる", async ({ page }, testInfo) => {
    const errorMessage = (await page.locator("main p").first().innerText()).trim();
    const errorCategory = classifyErrorMessage(errorMessage);

    const screenshotPath = testInfo.outputPath(`error-content-${errorCategory}.png`);
    await page.locator("main").screenshot({ path: screenshotPath });
    await testInfo.attach("error-content", {
      path: screenshotPath,
      contentType: "image/png"
    });

    switch (errorCategory) {
      case "retry_later":
        await expect(page.getByRole("link", { name: "フォームページに戻る" })).toBeVisible();
        break;
      case "maintenance":
        await expect(page.getByRole("heading", { name: "エラーが発生しました" })).toBeVisible();
        break;
      default:
        throw new Error(
          `未対応のエラー文言です。分類を追加してください: "${errorMessage}"`
        );
    }
  });
});
```

こちらもform.spec.ts同様Playwrightの基本メソッドを使用してます

screenshotメソッドを使って画面のスクリーンショットを取得し、test-results配下にpngファイルとして保存します

https://playwright.dev/docs/api/class-page#page-screenshot

```ts
    const errorMessage = (await page.locator("main p").first().innerText()).trim();
    const errorCategory = classifyErrorMessage(errorMessage);

    const screenshotPath = testInfo.outputPath(`error-content-${errorCategory}.png`);
    await page.locator("main").screenshot({ path: screenshotPath });
    await testInfo.attach("error-content", {
      path: screenshotPath,
      contentType: "image/png"
    });
```

下記がスクリーンショットです

![Screenshot 2026-06-21 at 13.55.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/72d6b02d-989e-49e3-b1f0-8036d12682dc.png)

## 便利機能
```
playwright test --ui
```

を実行することで下記のようにブラウザ上でPlaywrightのテストを実行できます
filter actionsからbeforeHooksで何を実行しているか、テストごとの所要時間がわかって便利です

![Screenshot 2026-06-21 at 13.56.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3fcb3c28-b629-4981-ba5d-a6caeeee695a.png)

また、Microsoftが公式で出しているVSCodeの拡張機能があります

![Screenshot 2026-06-21 at 13.59.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0f85dd0a-b521-4d84-9a95-b18e96f2543d.png)

この拡張機能でbreakpointを使ったPlaywrightのテストのdebugができます

![Screenshot 2026-06-21 at 13.58.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b4b88956-dea4-476c-93b0-197cbb2483fe.png)

![Screenshot 2026-06-21 at 13.58.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f84e780d-af40-4f1a-8795-2d416f14b92a.png)

## GitHub PagesへPlaywrightの実行結果をuploadするには
下記actionsを使って実行結果をGitHub Pagesへuploadすることができます
playwright test実行時に生成されるplaywright-report/配下のindex.htmlやスクリーンショットなどのdataがartifactとしてuploadされ、GitHub Pagesへ展開される仕組みになってます

https://github.com/actions/upload-pages-artifact

https://github.com/actions/deploy-pages

```yaml:.github/workflows/playwright-report-pages.yml
name: Playwright Report to GitHub Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test-and-build-report:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version-file: package.json
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browser
        run: npx playwright install --with-deps chromium

      - name: Run Playwright tests
        id: playwright
        continue-on-error: true
        run: npm run test

      - name: Upload Playwright report artifact
        if: always()
        uses: actions/upload-pages-artifact@v5
        with:
          path: playwright-report

      - name: Mark job failed when tests fail
        if: steps.playwright.outcome == 'failure'
        run: exit 1

  deploy:
    needs: test-and-build-report
    if: always()
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v5

```

Settings -> PagesのBuild and deploymentのSourceからGitHub Actionsを選択し、GitHub Pagesを有効化しましょう

![Screenshot 2026-06-21 at 9.58.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4407500b-0bf7-46c4-b13d-535b84e61fd6.png)

以下のようにワークフローが実行され、テスト内容をGitHub Pagesで閲覧できれば成功です

![Screenshot 2026-06-21 at 10.03.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e613e308-b37d-47a7-8e6a-608247bc3da5.png)

![Screenshot 2026-06-21 at 10.04.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5c900de0-b2b2-49a1-a1dc-e873b466cd4b.png)

## まとめ
UI上のテストをコード化できるPlaywrightを使ってみてとても便利だと感じましたし、PlaywrightのMCPや録画した内容をコード化する機能などもあるので触ってみて便利だなと思った機能はこの記事に順次追記、更新していきたいと思います

## 参考
https://playwright.dev/

https://github.com/microsoft/playwright
