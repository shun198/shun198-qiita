---
title: NestjsでSession認証を使ったログイン/ログアウトAPIを実装しよう！
tags:
  - Express
  - PostgreSQL
  - TypeScript
  - prisma
  - NestJS
private: false
updated_at: '2024-04-17T15:40:25+09:00'
id: 6c481a3aeaf6c8c7d7ad
organization_url_name: null
slide: false
---
## 概要
Nest.jsでSession認証を実装した記事が思ってたより少なかったのでSessionを使ったログイン/ログアウトAPIの実装方法について解説したいと思います

## 前提
- Nest.jsのプロジェクトを作成済み
- ORMはPrismaを使用
- express-sessionを使ってセッション情報を保持します
- passport.jsのLocalStrategyを使って社員番号とパスワードで認証します
- セッション情報をDBに保存するのでPostgresを使用します

## ディレクトリ構成
```
.
├── .env
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
│   ├── auth
│   │   ├── auth.controller.spec.ts
│   │   ├── auth.controller.ts
│   │   ├── auth.module.ts
│   │   └── dto
│   │       └── loginUser.dto.ts
│   ├── common
│   │   ├── bcrypt.ts
│   │   ├── localStrategy.ts
│   │   └── validators.ts
│   ├── main.ts
│   ├── prisma
│   │   ├── prisma.module.ts
│   │   └── prisma.service.ts
│   └── user
├── tsconfig.build.json
└── tsconfig.json
```

## パッケージのインストール
必要なパッケージをインストールします

```
npm install express-session connect-pg-simple @nestjs/passport passport passport-local 
npm install @types/passport-local @types/express --save-dev
```

## UserのModelの作成
shema.prismaにUserのModelのschemaを記載します

```ts:schema.prisma
// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

// Looking for ways to speed up your queries, or scale easily with your serverless or edge functions?
// Try Prisma Accelerate: https://pris.ly/cli/accelerate-init

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id              Int             @id @default(autoincrement())
  name            String          @db.VarChar(255)
  employee_number String          @unique @db.VarChar(8)
  email           String          @unique
  password        String          @db.VarChar(255)
  role            Role            @default(ADMIN)
  is_active       Boolean         @default(true)
  is_verified     Boolean         @default(false)
  is_superuser    Boolean         @default(false)
  createdAt       DateTime        @default(now())
  updatedAt       DateTime        @updatedAt
}

enum Role {
  ADMIN
  GENERAL
}

```

## main.ts
main.tsにセッションの設定を行います
express-sessionではデフォルトでメモリ上にセッション情報を保持します
しかし、メモリでの管理はセッション情報を開放し忘れてメモリリークを発生してしまうリスクがあったり、マルチスレッドではセッション情報を保持できなかったりとNest.jsに限らず本番環境では非推奨とされています
Redisを使って保存する手もありますがコストが高いので今回はPostgresを使ったセッション情報を保持する方法について解説します
Postgresにセッション情報を保持する際は公式がCompatible Session Storesとして紹介した`connect-pg-simple`を使います

https://www.npmjs.com/package/connect-pg-simple

```main.ts
import { NestFactory } from '@nestjs/core';
import * as session from 'express-session';
import * as passport from 'passport';
import * as pgSession from 'connect-pg-simple';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { Request, Response, NextFunction } from 'express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('api');
  const pgSessionStore = pgSession(session);
  app.use(
    session({
      store: new pgSessionStore({
        // prismaで設定したDATABASE_URLを指定
        conString: process.env.DATABASE_URL,
        // テーブルが存在しなければ新規作成する
        createTableIfMissing: true,
      }),
      secret: process.env.SECRET_KEY,
      resave: false,
      saveUninitialized: false,
      // セッション情報を1h保持
      cookie: {
        maxAge: 60 * 60 * 1000,
      },
    }),
  );
  app.use(passport.initialize());
  app.use(passport.session());
  app.useGlobalPipes(new ValidationPipe());
  if (process.env.NODE_ENV === 'development') {
    const config = new DocumentBuilder()
      .setTitle('CRM API Project')
      .setDescription('CRM API description')
      .setVersion('1.0')
      .build();
    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('api/docs/', app, document);
    // Swaggerによるキャッシュ制御を無効にする
    app.use((req: Request, res: Response, next: NextFunction) => {
      res.header('Cache-Control', 'no-cache, no-store, must-revalidate');
      res.header('Pragma', 'no-cache');
      res.header('Expires', '0');
      next();
    });
  }
  await app.listen(8000);
}
bootstrap();

```

また、記事によってSerializerを使用してセッション情報を保持していますがDBに保存しているので今回は不要です

## ログイン/ログアウトAPIの作成
以下のコマンドを実行して
- module
- controller

を作成します
```
nest generate module auth
nest generate controller auth
```

### auth.module.ts
ModuleにPassportModuleをimportし、session認証を有効化します
また、providerに後ほど作成するLocalStrategyを追加します

```auth.module.ts
import { Module } from '@nestjs/common';
import { AuthController } from './auth.controller';
import { PrismaModule } from '../prisma/prisma.module';
import { PassportModule } from '@nestjs/passport';
import { PrismaService } from '../prisma/prisma.service';
import { LocalStrategy } from '../common/localStrategy';

@Module({
  imports: [PrismaModule, PassportModule.register({ session: true })],
  controllers: [AuthController],
  providers: [PrismaService, LocalStrategy],
})
export class AuthModule {}

```

### auth.controller.ts
ログイン/ログアウトAPIのルートを作成するためのcontrollerを作成します
ログインAPI内でrequest.session.userにuser情報を保持するようにします
また、ログアウトAPIを実行するとセッションを削除するよう設定します

```auth.controller.ts
import {
  Body,
  Controller,
  Post,
  HttpCode,
  HttpStatus,
  Req,
  Res,
} from '@nestjs/common';
import { LogInUserDto } from './dto/loginUser.dto';
import { ApiTags } from '@nestjs/swagger';
import { LocalStrategy } from '../common/localStrategy';

@ApiTags('login')
@Controller()
export class AuthController {
  constructor(private localStrategy: LocalStrategy) {}

  @HttpCode(HttpStatus.OK)
  @Post('login')
  async logIn(
    @Body() logInUserDto: LogInUserDto,
    @Req() request: any,
    @Res() response: any,
  ) {
    const user = await this.localStrategy.validate(
      logInUserDto.employee_number,
      logInUserDto.password,
    );
    request.session.user = user;
    response.status(HttpStatus.OK).json({ name: user.name, role: user.role });
  }

  @Post('logout')
  @HttpCode(HttpStatus.OK)
  async logout(@Req() request: any): Promise<void> {
    request.session.destroy();
  }
}

```

### loginUser.dto.ts
数字8桁の社員番号のみ許容するようバリデーションを行います
詳細は以下の記事を参考にしてください

https://qiita.com/shun198/items/44acafce057b4baf8486

```loginUser.dto.ts
import { IsString, MaxLength, Validate } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { IsEmployeeNumber } from '../../common/validators';

export class LogInUserDto {
  @ApiProperty({ description: '社員番号', example: '00000001' })
  @IsString()
  @Validate(IsEmployeeNumber)
  employee_number: string;

  @ApiProperty({ description: 'パスワード', example: 'test' })
  @IsString()
  @MaxLength(255)
  password: string;
}

```

## LocalStrategy
LocalStrategyを使ってユーザの認証を行います
今回はPassportStrategyを継承したクラスを作成します
PassportStrategyを使用する際はusernameとpasswordで認証しますが
```typescript
  constructor(private authService: AuthService) {
    super({ usernameField: 'employee_number' });
  }
```
と記載することでusernameFieldを社員番号にoverrideできます
社員番号からユーザが登録されているか確認し、パスワードが一致していればユーザを返し、一致していなければエラーメッセージを返します

```localStrategy.py
import { Strategy } from 'passport-local';
import { PassportStrategy } from '@nestjs/passport';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { comparePassword } from '../common/bcrypt';

@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy) {
  constructor(private prismaService: PrismaService) {
    super({ usernameField: 'employee_number' });
  }

  async validate(employee_number: string, password: string): Promise<any> {
    const user = await this.prismaService.user.findUnique({
      where: { employee_number },
    });
    const matched = await comparePassword(password, user.password);
    if (user && matched) {
      return user;
    } else {
      throw new UnauthorizedException(
        '社員番号またはパスワードが間違っています',
      );
    }
  }
}

```

```bcrypt.ts
import * as bcrypt from 'bcrypt';

export async function encodePassword(rawPassword: string): Promise<string> {
  const SALT = bcrypt.genSaltSync();
  return bcrypt.hashSync(rawPassword, SALT);
}

export async function comparePassword(
  rawPassword: string,
  hashedPassword: string,
): Promise<boolean> {
  return bcrypt.compareSync(rawPassword, hashedPassword);
}

```

## 実際にログイン/ログアウトしてみよう！
ログインAPIを実行し、以下のようにユーザ名とロールを返したら成功です
![スクリーンショット 2024-04-17 15.08.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4583a51e-fe7c-0090-9426-51c25446aafb.png)

![スクリーンショット 2024-04-17 15.09.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2de992d8-dd5b-e51b-d7d7-c8e35293b63b.png)

Postgres内にsessionテーブルが作成され、セッション情報が登録されていたら成功です
```
postgres=# SELECT * FROM session;
| sid | sess | expire |      
|-----+------+--------|
|htc0SrcLtN4g-IiNTJ9OImGazDwQT-iq | {"cookie":{"originalMaxAge":3600000,"expires":"2024-04-17T07:09:02.353Z","httpOnly":true,"path":"/"},"user":{"id":1,"name":"テストユーザゼロイチ","employee_number":"00000001","email":"test_user_01@example.com","password":"$2b$10$QZeDhxirxG2icjJk6iWkze2AnQfgr1POraYh18xjadwOhmfBRzcIK","role":"ADMIN","is_active":true,"is_verified":true,"is_superuser":false,"createdAt":"2024-04-16T04:54:39.728Z","updatedAt":"2024-04-16T05:08:34.791Z"}} | 2024-04-17 07:09:03|
```

間違ったパスワードでログインし、エラーメッセージを返したら成功です
![スクリーンショット 2024-04-17 15.34.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a04fed75-e090-dc4c-f34b-57873aa6fe35.png)

ログアウトAPIを実行し、セッション情報が削除されたら成功です
![スクリーンショット 2024-04-17 15.37.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/43c007e1-b763-ccce-1349-4ef98ec718b1.png)

```
postgres=# SELECT * FROM session;
| sid | sess | expire |
|-----+------+--------|
(0 rows)
```

## まとめ
JWTでの認証方法が多い中あえてSession認証を使って実装してみました
もしかしたら考慮ができてない部分もあるかと思うので指摘等いただけると幸いです

## 参考
https://docs.nestjs.com/techniques/session

https://github.com/expressjs/session

https://github.com/voxpelli/node-connect-pg-simple

https://zenn.dev/yuuan/articles/e38805e9af2d92

https://medium.com/@musanziwilfried/nestjs-session-based-authentication-65d431870f93

https://github.com/voxpelli/node-connect-pg-simple?tab=readme-ov-file#connection-options

https://github.com/nestjs/nest/issues/4918

