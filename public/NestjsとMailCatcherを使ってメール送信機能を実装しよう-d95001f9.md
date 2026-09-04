---
title: Nest.jsとMailCatcherを使ってメール送信機能を実装しよう！
tags:
  - mailcatcher
  - docker-compose
  - NestJS
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: d95001f94aecfc01be92
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Nest.jsとMailCatcherを使ってメール送信機能を実装する方法について解説します
今回は招待メールを送信するAPIを作成します

## 前提
- Nest.jsのアプリケーションを作成済み

## ディレクトリ構成
```
tree
.
├── .eslintrc.js
├── .gitignore
├── .prettierrc
├── nest-cli.json
├── package-lock.json
├── package.json
├── prisma
│   ├── migrations
│   ├── schema.prisma
│   └── seed.ts
├── src
│   ├── app.controller.spec.ts
│   ├── app.controller.ts
│   ├── app.module.ts
│   ├── app.service.ts
│   ├── email
│   │   ├── email.module.ts
│   │   ├── email.service.ts
│   │   └── templates
│   │       └── welcome.hbs
│   ├── main.ts
│   ├── prisma
│   │   ├── prisma.module.ts
│   │   └── prisma.service.ts
│   └── user
│       ├── dto
│       │   └── inviteUser.dto.ts
│       ├── user.controller.ts
│       ├── user.module.ts
│       └── user.service.ts
├── tsconfig.build.json
└── tsconfig.json
```

以下のファイルを実装します
- compose.yaml
- email.module.ts
- email.service.ts
- welcome.hbs
- nest-cli.json
- inviteUser.dto.ts
- main.ts
- user.service.ts
- user.controller.ts

## 実装
### compose.yaml
Mailサーバ用のコンテナを作成する際にMailCatcherを使用します

#### mailcatcherとは
> MailCatcher runs a super simple SMTP server which catches any message sent to it to display in a web interface. 

公式ドキュメントに記載されている通り簡易的なSMTPサーバでMailCatcherに送信されたメールをWebインターフェイス(Webブラウザ)に表示させることができます
本番環境ではAWSのSESを使うのでローカルでメール送信テストを行いたいときはMailCatcherを使ってみましょう

> Run mailcatcher, set your favourite app to deliver to smtp://127.0.0.1:1025 instead of your default SMTP server, then check out http://127.0.0.1:1080 to see the mail that's arrived so far.

公式ドキュメントに記載されている通り
MailCatcherのイメージを指定して
- SMTP用の1025番ポート
- Webブラウザで閲覧する用の1080番ポート
 
の2種類のポートを解放します

```compose.yaml
services:
  mail:
    container_name: mail
    image: schickling/mailcatcher
    ports:
      - "1080:1080"
      - "1025:1025"
```

### email.module.ts
メール送信機能用のModuleの設定を行います
今回はMailCatcherを使用しているのでホストはlocalhost、portがMailCatcherのSMTP用のポートである1025を使用します

```email/email.module.ts
import { Module } from '@nestjs/common';
import { EmailService } from './email.service';
import { MailerModule } from '@nestjs-modules/mailer';
import { join } from 'path';
import { HandlebarsAdapter } from '@nestjs-modules/mailer/dist/adapters/handlebars.adapter';

@Module({
  imports: [
    MailerModule.forRoot({
      transport: {
        host: 'localhost',
        port: Number('1025'),
        secure: false,
      },
      defaults: {
        from: '"No Reply" <no-reply@example.com>',
      },
      template: {
        dir: join(__dirname, 'templates'),
        adapter: new HandlebarsAdapter(),
        options: {
          strict: true,
        },
      },
    }),
  ],
  providers: [EmailService],
  exports: [EmailService],
})
export class EmailModule {}

```

### email.service.ts
招待メールを送信する用のメソッドを作成します
宛先はリクエスト内のメールアドレス、テンプレートは後述するwelcome.hbsを使用します

```email/email.service.ts
import { MailerService } from '@nestjs-modules/mailer';
import { Injectable } from '@nestjs/common';
import { InviteUserDto } from 'src/user/dto/inviteUser.dto';

@Injectable()
export class EmailService {
  constructor(private readonly mailerService: MailerService) {}

  async welcomeEmail(data: InviteUserDto) {
    const subject = `ようこそ`;

    await this.mailerService.sendMail({
      to: data.email,
      subject,
      template: './welcome',
    });
  }
}

```

### welcome.hbs
招待メール用のテンプレートを作成します

```email/templates/welcome.hbs
<p>ようこそ</p>

```

### nest-cli.json
このままだとhbsファイルはコンパイルされた際、distフォルダ内に格納されません
メールが送信されなくなってしまうので以下のように設定します

```nest-cli.json
{
  "collection": "@nestjs/schematics",
  "sourceRoot": "src",
  "compilerOptions": {
    "assets": [
      {
        "include": "**/email/templates/**/*",
        "outDir": "dist/src",
        "watchAssets": true
      }
    ]
  }
}

```

### inviteUser.dto.ts
リクエスト内の入れたメールアドレスのバリデーションを行います
今回は
- Emailの形式なのか
- 最大値が254文字

のバリデーションを適用させます

```user/dto/inviteUser.dto.ts
import { IsEmail, MaxLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class InviteUserDto {
  @ApiProperty()
  @IsEmail()
  @MaxLength(254)
  email: string;
}

```

### main.ts
先ほど作成した
- EmailModule
- EmailService

をimportします

```main.ts
import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ConfigModule } from '@nestjs/config';
import { UserService } from './user/user.service';
import { UserController } from './user/user.controller';
import { UserModule } from './user/user.module';
import { EmailModule } from './email/email.module';
import { EmailService } from './email/email.service';

@Module({
  imports: [
    ConfigModule.forRoot({ envFilePath: '../.env' }),
    UserModule,
    EmailModule,
  ],
  controllers: [AppController, UserController],
  providers: [AppService, UserService, EmailService],
})
export class AppModule {}

```

### user.service.ts
emailServiceを使ってメールを送信します

```user.service.ts
import { Injectable } from '@nestjs/common';
import { EmailService } from '../email/email.service';
import { InviteUserDto } from './dto/inviteUser.dto';

@Injectable()
export class UserService {
  constructor(
    private readonly emailService: EmailService,
  ) {}

  async send_invite_user_email(data: InviteUserDto) {
    this.emailService.welcomeEmail(data);
  }
}

```

### user.controller.ts
UserService内のメール送信メソッドを実行できるようコントローラの設定を行います

```user.controller.ts
import { Controller, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { Post, Body } from '@nestjs/common';
import { UserService } from './user.service';
import { InviteUserDto } from './dto/inviteUser.dto';

@ApiTags('users')
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post('send_invite_user_email')
  @HttpCode(HttpStatus.OK)
  send_invite_user_email(@Body() inviteUserDto: InviteUserDto) {
    return this.userService.send_invite_user_email(inviteUserDto);
  }
}

```

## 実際にメールを送信してみよう！
メールを送信します
リクエスト内にメールアドレスを入力し、リクエストを送信します

![スクリーンショット 2024-03-30 15.43.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3d5da413-d737-a600-dc8b-047c6844f6b6.png)

127.0.0.1:1080へアクセスし、以下のようにメールが送信されたら成功です
![スクリーンショット 2024-03-30 15.46.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9541b2cc-5294-669c-4828-7391b297477f.png)


## 参考
https://zenn.dev/yuu104/articles/8b8d7363b5dd5f

https://github.com/nest-modules/mailer/issues/42#issuecomment-910165521

https://blog.stackademic.com/implementing-email-service-in-nestjs-a-step-by-step-guide-42e03ef1fb05

https://github.com/bhagyajitjagdev/nestjs-email

