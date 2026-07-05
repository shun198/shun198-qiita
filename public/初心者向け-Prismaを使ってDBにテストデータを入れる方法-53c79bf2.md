---
title: '[初心者向け] Prismaを使ってDBにテストデータを入れる方法'
tags:
  - PostgreSQL
  - prisma
private: false
updated_at: '2024-03-19T21:15:24+09:00'
id: 53c79bf2c17f8787fd26
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Prismaを使ってDBにテストデータを入れる方法について解説します

## 前提
- Prismaをインストール済み
- 今回はPostgresを使用します

## ディレクトリ構成
```
└── package-lock.json
    ├── package.json
    ├── prisma
    │   ├── migrations
    │   │   ├── 20240305054538_
    │   │   └── migration_lock.toml
    │   ├── schema.prisma
    │   └── seed.ts
    └── src
```

## Modelの作成
今回は
- User
- Task

のModelを作成します

```typescript:schema.prisma
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
  id             Int      @id @default(autoincrement())
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt
  email          String   @unique
  hashedPassword String
  nickName       String?
  tasks          Task[]
}

model Task {
  id          Int      @id @default(autoincrement())
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  title       String
  description String?
  userId      Int
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

```

## テストデータの作成
seed.tsを作成して、データを入れる処理を追加します
main()内にUserとTaskを入れる処理を記載します
処理が終わったらPrisma Clientとの接続を切ります

```seed.ts
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
async function main() {
  await prisma.user.upsert({
    where: { email: 'alice@prisma.io' },
    update: {},
    create: {
      email: 'alice@prisma.io',
      nickName: 'Alice',
      hashedPassword: '$2b$12$tg885CjGIz1qs1nN2KFmlu6XdEPc.ucVzx4dwe9thxqL/rpaqWY9C',
      tasks: {
        create: {
          title: '懸垂',
          description: '広背筋と大円筋を鍛える種目',
        },
      },
    },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });

```

package.jsonに以下のコマンドを記載します

```package.json
  "prisma": {
    "seed": "ts-node prisma/seed.ts"
  },
```

## テストデータを入れる
以下のコマンドを実行してテストデータを入れます

```
npx prisma db seed
Running seed command `ts-node prisma/seed.ts` ...

🌱  The seed command has been executed.
```

データを入れ終わったらprisma studioを起動します
```
npx prisma studio
Prisma schema loaded from prisma/schema.prisma
Prisma Studio is up on http://localhost:5555
```

以下のようにテストデータが入っていたら成功です

![スクリーンショット 2024-03-07 14.53.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9ec034bc-a6e4-7d7b-1e86-fab48432f10b.png)

![スクリーンショット 2024-03-07 14.53.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/73af04d0-c1cb-ca1b-dc59-f06716ca9754.png)

## 参考
https://www.prisma.io/docs/orm/prisma-migrate/workflows/seeding

https://github.com/prisma/prisma-examples/blob/latest/typescript/rest-nestjs/prisma/seed.ts

