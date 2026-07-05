---
title: '[初心者向け]Nest.jsでSwaggerを使ってAPIドキュメントを自動生成する方法について徹底解説!便利なデコレータの使用方法も解説'
tags:
  - Node.js
  - swagger
  - NestJS
private: false
updated_at: '2026-01-02T19:03:21+09:00'
id: 13f93355279b94ef7bb7
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Swaggerを使ってNest.jsのAPIのドキュメントを自動生成する方法について解説します

## 前提
- Nest.jsのアプリケーションを作成済み
- APIを作成済

## 必要なパッケージのインストール
@nestjs/swaggerをインストールします

```
npm install @nestjs/swagger
```

## Swaggerの設定
main.tsに以下のようにSwaggerの初期設定を行います
今回は127.0.0.1:8000/api/docsへアクセスするとSwaggerが起動します

```main.ts
import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  if (process.env.NODE_ENV === 'development') {
    // Swaggerの初期設定
    const config = new DocumentBuilder()
      .setTitle('Test API Project')
      .setDescription('Test API description')
      .setVersion('1.0')
      .build();
    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('api/docs/', app, document);
  }
  await app.listen(8000);
}
bootstrap();

```

以下のように表示させたら成功です

![スクリーンショット 2024-03-13 13.44.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eddff95e-fb6c-c6ae-2e45-3afe2318e204.png)

## nestjs/swaggerで作成したAPIドキュメントをymlに出力するには
以下のようにfs.writeFileSync()を使うと出力できます

```main.ts
import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';
import * as fs from 'fs';
import { dump } from 'js-yaml';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  if (process.env.NODE_ENV === 'development') {
    // Swaggerの初期設定
    const config = new DocumentBuilder()
      .setTitle('Test API Project')
      .setDescription('Test API description')
      .setVersion('1.0')
      .build();
    const document = SwaggerModule.createDocument(app, config);
    // main.tsと同じ階層でswagger-spec.yamlファイルとして出力する
    fs.writeFileSync('./swagger-spec.yaml', dump(document, {}));
    SwaggerModule.setup('api/docs/', app, document);
  }
  await app.listen(8000);
}
bootstrap();

```

## ApiTagsを使ったAPIの分類分け
APIを複数以上作成する際にタグで分類することによって探すのが容易になります
以下のようにApiTagsデコレータを使うことで実現できます

```app.controller.ts
import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';
import { ApiTags, ApiResponse } from '@nestjs/swagger';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @ApiTags('health')
  @Get('health')
  healthCheck(): { msg: string } {
    return this.appService.healthCheck();
  }
}

```

以下のようにタグによる分類ができたら成功です
![スクリーンショット 2024-03-13 13.45.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b3a23f49-307d-8058-6b9f-93a6c24d2ad4.png)

## ApiBody
APIを検証する際にリクエストが自動で補完されると入力の手間が省けて便利です
以下のようにApiBodyデコレータを使うことで実現できます

```app.controller.ts
import {
  Body,
  Controller,
  Post,
} from '@nestjs/common';
import { CreateUserDto } from './dtos/create-user.dto';
import { UsersService } from './users.service';
import { ApiTags, ApiBody } from '@nestjs/swagger';

@ApiTags('users')
@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {}

  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        email: {
          type: 'string',
          default: 'test@gmail.com',
        },
        password: {
          type: 'string',
          default: 'test',
        },
      },
    },
  })
  /**
   * ユーザを新規登録するAPI
   * @param body - ユーザの情報
   */
  @Post('/signup')
  createUser(@Body() body: CreateUserDto) {
    this.usersService.create(body.email, body.password);
  }
}
```

以下のようにリクエストボディが表示されたら成功です

![スクリーンショット 2024-03-13 15.07.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/103343b8-7e07-0522-4713-705c04508768.png)


## ApiResponse
ステータスコード、ケース別でレスポンス例を複数表示させることができます
以下のようにApiResponseデコレータを使うことで実現できます

```app.controller.ts
import {
  Body,
  Controller,
  Get,
  Param,
} from '@nestjs/common';
import { UsersService } from './users.service';
import { ApiTags, ApiResponse } from '@nestjs/swagger';


@ApiTags('users')
@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {}

  @ApiResponse({
    status: HttpStatus.OK,
    description: 'ユーザ詳細',
    content: {
      'application/json': {
        example: [
          {
            id: 1,
            email: 'test@gmail.com',
          },
        ],
      },
    },
  })
  @ApiResponse({
    status: HttpStatus.NOT_FOUND,
    description: '該当するユーザが存在しないとき',
    content: {
      'application/json': {
        example: [
          {
            message: '該当するIDを持つユーザが存在しません',
            error: 'Not Found',
            statusCode: 404,
          },
        ],
      },
    },
  })
  /**
   * ユーザを詳細表示するAPI
   * @param id - ユーザのID
   */
  @Get('/:id')
  async findUser(@Param('id') id: number) {
    const user = await this.usersService.findOne(id);
    if (!user) {
      throw new NotFoundException('該当するIDを持つユーザが存在しません');
    }
    return this.usersService.findOne(id);
  }
}
```

以下のように複数のレスポンス例が表示されたら成功です

![スクリーンショット 2024-03-13 15.10.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fe88f5ce-19a4-9ecd-4619-49c4046ee185.png)


## ApiBearerAuth
Bearer認証をSwaggerでもできるようにするためのデコレータです
Swagger内でログイン時に使用するJWTトークンなどを設定できるようにするためにはまず`addBearerAuth()`を`DocumentBuilder()`に追加します

```typescript
import helmet from 'helmet';
import { HttpStatus } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { NestExpressApplication } from '@nestjs/platform-express';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger'

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  const config = new DocumentBuilder()
    .setTitle("NestJS API")
    .setDescription('NestJS API desc')
    .setVersion("1.0")
    .addBearerAuth().build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);
  app.use(helmet());
  app.enableCors(
    {
      origin: '*',
      methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
      preflightContinue: false,
      optionsSuccessStatus: HttpStatus.NO_CONTENT,
      allowedHeaders: 'Content-Type, Accept',
      credentials: true,
    }
  );
  await app.listen(8000);
}
bootstrap();
```

このままではBearerトークンが必要なAPIに対してトークンをセットできないので下記のように`@ApiBearerAuth()`デコレータを設定して一度Swagger内で認証できれば自動でBearerトークンを設定できるようにします

```typescript
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Get user profile',
    content: {
      'application/json': {
        example: [
          {
            username: "john",
            userId: 1,
          },
        ],
      },
    },
  })
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @Get('profile')
  getProfile(@Request() req) {
    return req.user;
  }
```

まずは自作したログインAPIを実行してJWTトークンを発行します

![Screenshot 2026-01-02 at 19.01.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/65a657de-d40d-47e5-9223-56f6a19a0c5e.png)

発行したトークンをSwaggerのAuthorizeにセットします
![Screenshot 2026-01-02 at 19.01.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9d10468f-5fee-493c-a4bf-92ed019afcad.png)

認証が必要なAPIをcall時にJWTトークンがヘッダにセットされている上にcallできていることを確認できれば成功です
![Screenshot 2026-01-02 at 19.02.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79b7c6cc-bf0d-41c9-b925-d4446e481811.png)


## まとめ
@nestjs/swagger(Swagger)を使うとAPIドキュメントを自動生成できるので管理が格段に楽になることがわかりました
他に@nestjs/swaggerに関する便利機能があれば定期的に本記事を更新していきたいと思います

## 参考
https://docs.nestjs.com/openapi/introduction

https://docs.nestjs.com/openapi/types-and-parameters

https://wp-kyoto.net/export-swagger-api-def-from-nestjs/

https://docs.nestjs.com/openapi/security#bearer-authentication
