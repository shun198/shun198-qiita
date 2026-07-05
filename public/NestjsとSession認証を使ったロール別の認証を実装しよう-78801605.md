---
title: Nest.jsとSession認証を使ったロール別の認証を実装しよう！
tags:
  - Express
  - Guard
  - NestJS
private: false
updated_at: '2024-04-17T16:52:22+09:00'
id: 7880160597096af11cda
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Nest.jsのguardを使ってセッションで認証したユーザの
- 管理者
- 一般

の2種類のロール別の認証を実装する方法について解説します

## 前提
- Nest.jsのアプリケーションを作成済み
- セッション認証を実装済み

セッション認証の実装方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/6c481a3aeaf6c8c7d7ad

## Modelの設定
UserにRoleという権限を付与するようschema定義します

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

## guardの実装
管理者のみ許可するAdminAuthGuardとログインユーザを許可するUserAuthGuardの2種類のguardを実装します

### 管理者のみ許可する場合
request内のsessionオブジェクトからユーザが存在している上に管理者のロールを持っているかどうかを確認します
管理者ユーザであることが確認できたらユーザのオブジェクトを返します

```admin-auth.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
  ForbiddenException,
} from '@nestjs/common';
import { Observable } from 'rxjs';

@Injectable()
export class AdminAuthGuard implements CanActivate {
  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request = context.switchToHttp().getRequest();
    const user = request.session && request.session.user;
    if (!user) {
      throw new UnauthorizedException(
        'ログインしていないため、この操作を実行する権限がありません',
      );
    }
    if (user.role !== 'ADMIN') {
      throw new ForbiddenException(
        '管理者ユーザではないため、この操作を実行する権限がありません',
      );
    }
    return user;
  }
}

```

### ログインユーザを許可する場合
request内のsessionオブジェクトからユーザが存在しているかどうかを確認します
管理者ユーザであることが確認できたらユーザのオブジェクトを返します
```user-auth.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common';
import { Observable } from 'rxjs';
@Injectable()
export class UserAuthGuard implements CanActivate {
  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request = context.switchToHttp().getRequest();
    const user = request.session && request.session.user;
    if (!user) {
      throw new UnauthorizedException(
        'ログインしていないため、この操作を実行する権限がありません',
      );
    }
    return user;
  }
}

```

## 実際に検証してみよう！
ユーザを一覧表示する簡単なAPIを使って検証します
まず、ログインせずにAPIを実行しようとするとエラーメッセージを返すことが確認できます

![スクリーンショット 2024-04-17 16.33.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/18b36b57-35a5-e1a5-4034-6418d4edf8b9.png)

UseGuardsとAdminAuthGuardを使って管理者ユーザのみ使用できるか確認します

```user.controller.ts
import {
  Get,
  Controller,
  HttpStatus,
  UseGuards,
} from '@nestjs/common';
import { ApiTags, ApiResponse } from '@nestjs/swagger';
import { UserService } from './user.service';
import { AdminAuthGuard } from 'src/guards/admin-auth.guard';

@ApiTags('users')
@Controller('admin/users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @UseGuards(AdminAuthGuard)
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'ユーザを一覧表示',
    content: {
      'application/json': {
        example: [
          {
            id: 1,
            name: 'テストユーザゼロイチ',
            employee_number: '00000001',
            email: 'test_user_01@example.com',
            is_active: true,
            is_verified: true,
            createdAt: '2024-03-08T00:33:27.790Z',
            updatedAt: '2024-03-08T00:33:27.790Z',
          },
        ],
      },
    },
  })
  findAll() {
    return this.userService.findAll();
  }
}
```

管理者ユーザでログインします
![スクリーンショット 2024-04-17 16.34.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e16d504a-f77a-19c8-5d9d-64b4151eef62.png)

以下のように管理者でログインしたらユーザが一覧表示されることを確認できました
![スクリーンショット 2024-04-17 16.35.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4474d70e-5c5d-1741-54bc-f1cd949f4e3d.png)

一般ユーザでログインします
![スクリーンショット 2024-04-17 16.36.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bf315e3f-1089-a3d5-8f8b-7cba926d93a7.png)

権限エラーを返すことが確認できました
![スクリーンショット 2024-04-17 16.36.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/315d1882-f864-a27b-aa33-476df13c37d3.png)

UseGuardsとUserAuthGuardを使って管理者ユーザのみ使用できるか確認します

```user.controller.ts
import {
  Get,
  Controller,
  HttpStatus,
  UseGuards,
} from '@nestjs/common';
import { ApiTags, ApiResponse } from '@nestjs/swagger';
import { UserService } from './user.service';
import { UserAuthGuard } from 'src/guards/user-auth.guard';

@ApiTags('users')
@Controller('admin/users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @UseGuards(UserAuthGuard)
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'ユーザを一覧表示',
    content: {
      'application/json': {
        example: [
          {
            id: 1,
            name: 'テストユーザゼロイチ',
            employee_number: '00000001',
            email: 'test_user_01@example.com',
            is_active: true,
            is_verified: true,
            createdAt: '2024-03-08T00:33:27.790Z',
            updatedAt: '2024-03-08T00:33:27.790Z',
          },
        ],
      },
    },
  })
  findAll() {
    return this.userService.findAll();
  }
}
```

一般ユーザでログインします
![スクリーンショット 2024-04-17 16.36.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bf315e3f-1089-a3d5-8f8b-7cba926d93a7.png)

以下のように一般ユーザでログインしたらユーザが一覧表示されることを確認できました
![スクリーンショット 2024-04-17 16.35.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4474d70e-5c5d-1741-54bc-f1cd949f4e3d.png)

## 参考
https://docs.nestjs.com/guards

https://stackoverflow.com/questions/75004427/how-to-throw-error-using-nest-js-guards-without-using-any-authentication-module
