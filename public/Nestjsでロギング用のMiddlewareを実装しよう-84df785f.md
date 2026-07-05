---
title: Nest.jsでロギング用のMiddlewareを実装しよう！
tags:
  - Node.js
  - logging
  - NestJS
private: false
updated_at: '2024-03-07T21:46:03+09:00'
id: 84df785fbdd05308c3fc
organization_url_name: null
slide: false
---
## 概要
ロギング用のMiddlewareを作成することでAPIを実行するたびに共通のログを出力できるのでとても便利で実装方法について解説します

## 前提
- Nest.jsのアプリケーションを作成済み

## ディレクトリ構成
```
tree
.
└── application
    ├── README.md
    ├── common
    │   └── logger.middleware.ts
    ├── nest-cli.json
    ├── package-lock.json
    ├── package.json
    └── src
        ├── app.controller.ts
        ├── app.module.ts
        ├── app.service.ts
        └── main.ts
```

## 実装
ロギング用のMiddlewareを実装する際に
- logger.middleware.ts
- main.ts

を作成および編集する必要があります

### logger.middleware.ts
今回作成するロギング用のMiddlewareのクラスです
レスポンスが帰ってきてからログを出力したいので

```typescript
response.on('finish', () => {
```
と記載します
また、
```typescript
this.logger.log(`${ip} ${method} ${originalUrl} ${statusCode}`);
```

の箇所で出力したいログの形式を指定します


```common/logger.middleware.ts
// logger.middleware.ts
import { Injectable, NestMiddleware, Logger } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

@Injectable()
export class LoggerMiddleware implements NestMiddleware {
  private readonly logger = new Logger('HTTP');

  use(request: Request, response: Response, next: NextFunction): void {
    const { ip, method, originalUrl } = request;
    response.on('finish', () => {
      const { statusCode } = response;
      this.logger.log(`${ip} ${method} ${originalUrl} ${statusCode}`);
    });
    next();
  }
}

```

## app.module.ts
Moduleに先ほど作成したLoggerMiddlewareを適用するよう設定します
今回は全てのAPIにLoggerMiddlerwareを適用させたいのでforRoutesで指定するルートをアスタリスク(*)にします

```src/app.module.ts
import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { LoggerMiddleware } from 'common/logger.middleware';

@Module({
  controllers: [AppController],
  providers: [AppService],
})
// LoggerMiddlewareの設定を全ルートで適用する
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(LoggerMiddleware).forRoutes('*');
  }
}

```

## APIを実行してみよう！
以下のようにAPIを実行した際にログが表示されたら成功です

```
2024-03-07 15:47:07 [Nest] 48498  - 03/07/2024, 6:47:07 AM     LOG [HTTP] ::ffff:192.168.65.1 POST /auth/signup 201
```

## 参考
https://docs.nestjs.com/middleware
