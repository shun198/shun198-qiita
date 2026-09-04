---
title: Nest.jsとBullMQを使って指定した時間にメール配信を実現しよう！
tags:
  - Redis
  - TypeScript
  - mailcatcher
  - NestJS
  - bullmq
private: false
updated_at: '2026-04-19T11:36:31+09:00'
id: 6d8133a28b6f30e62cea
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Nest.jsで指定した時間にジョブを実行したい場合はBullMQと一緒に実装するのが一般的です
今回はNest.jsとBullMQを使って指定した時間にメール配信する機能を実装する方法について解説します

## 前提
- bullmqをインストール済み
- ローカル上でのメール配信はmailcatcherを使用します

メール送信機能の実装方法は下記を参照してください

https://qiita.com/shun198/items/d95001f94aecfc01be92

## ディレクトリ構成
```
tree
.
├── compose.yaml
├── app.module.ts
├── main.ts
├── dto
│   └── schedule-email.dto.ts
├── email
│   ├── email.module.ts
│   ├── email.service.ts
│   └── templates
│       └── welcome.hbs
└── schedule
    ├── schedule.controller.ts
    ├── schedule.module.ts
    ├── schedule.processor.ts
    └── schedule.service.ts
```

## コンテナ環境の用意
MailCatcherとRedis用のコンテナを用意します

```yaml:compose.yaml
services:
  mail:
    container_name: mail
    image: schickling/mailcatcher
    ports:
      - "1080:1080"
      - "1025:1025"
  redis:
    container_name: redis
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"
```

## 実装
### app.moduleの設定
app.module.tsにBullMQおよびqueueをUI上で閲覧可能なBullBoardの設定を行います

```app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ScheduleModule } from './schedule/schedule.module';
import { EmailModule } from './email/email.module';
import { EmailService } from './email/email.service';
import { LoggerMiddleware } from './middleware/logger.middleware';
import { RedisModule } from './redis/redis.module';
import { BullModule } from '@nestjs/bullmq';
import { BullBoardModule } from '@bull-board/nestjs';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, envFilePath: ['.env', '../.env'] }),
    // redisとの接続設定を記載します
    BullModule.forRoot({
      connection: {
        host: 'localhost',
        port: 6379,
      },
    }),
    BullBoardModule.forRoot({
      route: '/admin/queues',
      adapter: ExpressAdapter,
    }),
    BullBoardModule.forFeature({
      name: 'schedule',
      adapter: BullMQAdapter,
    }),
    EmailModule,
    RedisModule,
    ScheduleModule,
  ],
  controllers: [],
  providers: [EmailService],
})

```

### メール送信機能
メール送信に必要な機能を追加していきます

```email.module.ts
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

```email.service.ts
import { MailerService } from '@nestjs-modules/mailer';
import { Injectable } from '@nestjs/common';

@Injectable()
export class EmailService {
  constructor(private readonly mailerService: MailerService) {}

  async sendWelcomeEmail(email: string) {
    const subject = `ようこそ`;

    await this.mailerService.sendMail({
      to: email,
      subject,
      template: './welcome',
    });
  }
}

```

### schedule機能の実装
shedule.module.tsを作成します
今回はscheduleというqueueを作成し、後述する
- controller
- service
- processor

を作成します

```schedule.module.ts
import { BullModule } from '@nestjs/bullmq';
import { Module } from '@nestjs/common';
import { EmailModule } from '../email/email.module';
import { ScheduleController } from './schedule.controller';
import { ScheduleProcessor } from './schedule.processor';
import { ScheduleService } from './schedule.service';

@Module({
  imports: [
    BullModule.registerQueue({
      name: 'schedule',
    }),
    EmailModule,
  ],
  controllers: [ScheduleController],
  providers: [ScheduleService, ScheduleProcessor],
})
export class ScheduleModule {}

```

BullMQのscheduleキューへメッセージを送信するエンドポイントを作成します
/api/scheduleへ
- email
- sendAt

をPOSTします

```schedule.controller.ts
import { Body, Controller, HttpCode, HttpStatus, Post } from '@nestjs/common';
import { ApiBody, ApiResponse, ApiTags } from '@nestjs/swagger';
import { ScheduleEmailDto } from '../dto/schedule-email.dto';
import { ScheduleService } from './schedule.service';

@ApiTags('schedule')
@Controller('api/schedule')
export class ScheduleController {
  constructor(private readonly scheduleService: ScheduleService) {}

  @HttpCode(HttpStatus.CREATED)
  @Post('email')
  @ApiBody({
    type: ScheduleEmailDto,
    examples: {
      example: { value: { email: 'john@example.com', sendAt: '2026-04-20T09:00:00.000Z' } },
    },
  })
  @ApiResponse({ status: HttpStatus.CREATED, description: 'ウェルカムメールのジョブを登録しました' })
  async scheduleWelcomeEmail(@Body() dto: ScheduleEmailDto): Promise<string> {
    return this.scheduleService.scheduleWelcomeEmail(dto);
  }
}
```

メール配信用のDTOを作成します
class-validatorのデコレータでバリデーションを実施します

```schedule-email.dto.ts
import { IsEmail, IsISO8601 } from 'class-validator';

export class ScheduleEmailDto {
  @IsEmail()
  email: string;

  @IsISO8601()
  sendAt: string; // ISO 8601形式 例: "2026-04-20T09:00:00.000Z"
}

```

serviceにBullMQのscheduleキューへメッセージを送信するまでのロジックを実装します
send-welcome-emailという名前のjobが送信されます

```schedule.service.ts
import { InjectQueue } from '@nestjs/bullmq';
import { Injectable, NotFoundException } from '@nestjs/common';
import { Queue } from 'bullmq';
import { ScheduleEmailDto } from '../dto/schedule-email.dto';

@Injectable()
export class ScheduleService {
  constructor(
    @InjectQueue('schedule') private scheduleQueue: Queue,
  ) {}

  async scheduleWelcomeEmail(dto: ScheduleEmailDto): Promise<string> {
    return this.enqueue('send-welcome-email', dto);
  }

  private async enqueue(jobName: string, dto: ScheduleEmailDto): Promise<string> {
    const delay = new Date(dto.sendAt).getTime() - Date.now();
    if (delay < 0) {
      throw new Error('sendAt must be a future date');
    }

    const job = await this.scheduleQueue.add(jobName, { email: dto.email }, { delay });
    return `Job scheduled: ${job.id} (delay: ${Math.round(delay / 1000)}s)`;
  }
}
```

processor側で指定した時間になったらメールを配信するロジックを実装します
Processorデコレータを使用してjob用のクラスだと明示し、processメソッドにjobのロジックを記載します
OnWorkerEventのcompletedとfailedを使用してジョブが完了した時、失敗した時はログを出力するよう設定してます

https://docs.bullmq.io/guide/workers

```schedule.processor.ts
import { OnWorkerEvent, Processor, WorkerHost } from '@nestjs/bullmq';
import { Injectable, Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { EmailService } from '../email/email.service';

@Injectable()
@Processor('schedule')
export class ScheduleProcessor extends WorkerHost {
  private readonly logger = new Logger(ScheduleProcessor.name);

  constructor(private readonly emailService: EmailService) {
    super();
  }

  async process(job: Job): Promise<void> {
    await this.emailService.sendWelcomeEmail(job.data.email);
  }

  @OnWorkerEvent('completed')
  onCompleted(job: Job) {
    this.logger.log(`Email sent to ${job.data.email} (job: ${job.name})`);
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    this.logger.error(`Failed to send email to ${job.data.email} (job: ${job.name}): ${error.message}`);
  }
}

```

## 検証してみよう！
/api/schedule/emailに
- email
- sentAt

を入れた上でPOSTします

![Screenshot 2026-04-19 at 11.30.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a5f3ba39-389a-43a4-a0cd-8e33cadcc42b.png)

![Screenshot 2026-04-19 at 11.31.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b2366fed-7dd0-44d7-b52d-d58b3bd2a937.png)


127.0.0.1:8000へアクセスするとBullBoardが表示され、Jobが作成されたことを確認しました
![Screenshot 2026-04-19 at 11.32.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2140b946-1820-4d7b-9f3d-67c9abca4347.png)

ログを閲覧し、メール送信に成功したことを確認できました
```
[Nest] 84542  - 04/19/2026, 11:32:01 AM     LOG [ScheduleProcessor] Email sent to john@example.com (job: send-welcome-email)
```

127.0.0.1:1080へアクセスし、メールを受信できました
![Screenshot 2026-04-19 at 11.33.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/09d9d293-58ea-4d36-900d-75a9ba2df8f4.png)

Redisブラウザからも確認できます
![Screenshot 2026-04-19 at 11.35.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6ccf245a-0b95-428b-b409-0aebde6a0f1d.png)

## まとめ
BullMQを使ってJobを簡単に作成できました
指定時間でのメール、AppPush配信や繰り返し実行したいジョブを登録するなどいろんなユースケースがあるので幅広く活用したいですね

## 参考文献
https://docs.nestjs.com/techniques/queues

https://github.com/nestjs/nest/tree/master/sample/26-queues

https://note.com/opst_mkrydik/n/n50c53c64bf59

https://docs.bullmq.io/

https://docs.bullmq.io/guide/workers
