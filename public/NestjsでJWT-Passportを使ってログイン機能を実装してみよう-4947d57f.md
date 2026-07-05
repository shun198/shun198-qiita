---
title: Nest.jsでJWT + Passportを使ってログイン機能を実装してみよう！
tags:
  - TypeScript
  - JWT
  - Passport
  - NestJS
private: false
updated_at: '2025-10-13T13:47:38+09:00'
id: 4947d57f8594f9694a6b
organization_url_name: null
slide: false
---
## 概要
Nest.jsとJWTとPassportを使ってログイン機能を作成する方法について解説します

## Passportとは
Node.jsの認証用ライブラリの一つで@nestjs/passportを使用することでNest.jsのアプリケーション内で簡単に実装できます

## ディレクトリ構成
```
tree
.
└── application
    └── src
        ├── app.module.ts
        ├── auth
        │   ├── auth.controller.spec.ts
        │   ├── auth.controller.ts
        │   ├── auth.module.ts
        │   ├── auth.service.spec.ts
        │   ├── auth.service.ts
        │   └── constants.ts
        ├── entity
        │   └── user.entity.ts
        ├── guards
        │   ├── jwt-auth.guard.ts
        │   ├── jwt.strategy.ts
        │   ├── local-auth.guard.ts
        │   └── local.strategy.ts
        └── main.ts
```

## 実装
### entity
以下のようにUserのEntityを作成します
今回は
- username
- password

を使ってログインするのでusernameはuniqueにしています

```user.entity.ts
import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

export enum Role {
  Admin = 'admin',
  General = 'general',
}

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  username: string;

  @Column()
  password: string;

  @Column({ default: true })
  isActive: boolean;

  @Column({
    type: 'enum',
    enum: Role,
    default: Role.General,
  })
  role: Role;
}
```

### Passport使用時に必要な設定ファイルの作成
LocalStrategyクラスを作成してログインAPI実行時のユーザの認証を行います
後ほど作成するvalidateUserメソッドで該当するユーザがDB内にあるか確認し、ない場合は401を返します

```local.strategy.ts
import { Strategy } from 'passport-local';
import { PassportStrategy } from '@nestjs/passport';
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { AuthService } from '../auth/auth.service';

@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy) {
  constructor(private authService: AuthService) {
    super();
  }

  async validate(username: string, password: string): Promise<any> {
    const user = await this.authService.validateUser(username, password);
    if (!user) {
      throw new UnauthorizedException();
    }
    return user;
  }
}
```

guardの作成を行います
ログインAPI内に下記のguardを設定することでAPI実行時にLocalStrategy内のvalidateメソッドが実行されます

```local-auth.guards.ts
import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class LocalAuthGuard extends AuthGuard('local') {}
```

下記がJWT用のsecret keyの設定です
```constants.ts
export const jwtConstants = {
  secret: process.env.SECRET_KEY
};
```

ログイン時に実行したいAPIがある場合、Header内のJWTトークンを照合するクラスです
ExtractJwt.fromAuthHeaderAsBearerToken()メソッドでHeader内のJWTトークンを認証します
認証後、該当するユーザのものだと判明した場合はvalidateメソッドを実行します
今回はJWT内にusername, userId, roleの情報が入っているのでこれらを返します
他のAPIで上記の情報を使用したい場合は下記のように`@Request() req`を引数として入れることで使用できます

```typescript
  @Get('profile')
  getProfile(@Request() req) {
    return req.user;
  }
```

```jwt.strategy.ts
import { ExtractJwt, Strategy } from 'passport-jwt';
import { PassportStrategy } from '@nestjs/passport';
import { Injectable } from '@nestjs/common';
import { jwtConstants } from '../auth/constants';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor() {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: jwtConstants.secret,
    });
  }

  async validate(payload: any) {
    return { username: payload.username, userId: payload.userId, role: payload.role};
  }
}
```

guardの作成を行います
ログインユーザのみ実行できるようにしたいAPIに下記のguardを設定することでAPI実行時にJwtStrategy内のvalidateメソッドが実行されます

```jwt-auth..guard.ts
import { Injectable } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {}
```

### 認証関連のAPIの作成
auth.module.ts内に先ほど作成した
- LocalStrategy
- JwtStrategy

をproviderに追加します
また、importsにJwtModuleを追加し、JWT用のsecret keyと有効期限を設定できます
今回は有効期限を1時間に設定しています

```auth.module.ts
import { Module } from '@nestjs/common';
import { AuthService } from './auth.service';
import { LocalStrategy } from '../guards/local.strategy';
import { JwtStrategy } from '../guards/jwt.strategy';
import { UsersModule } from '../users/users.module';
import { PassportModule } from '@nestjs/passport';
import { JwtModule } from '@nestjs/jwt';
import { jwtConstants } from './constants';
import { AuthController } from './auth.controller';

@Module({
  imports: [
    UsersModule,
    PassportModule,
    JwtModule.register({
      secret: jwtConstants.secret,
      signOptions: { expiresIn: '3600s' },
    }),
  ],
  providers: [AuthService, LocalStrategy, JwtStrategy],
  controllers: [AuthController],
  exports: [AuthService],
})
export class AuthModule {}
```

- ログインAPI(/api/auth/login)
- プロファイル情報取得API(/api/auth/profile)

を作成します
ログインAPIでは
- username
- password

をリクエストボディに入れ、POSTしたらJWTトークンがreturnされるよう作成します
`@UseGuards`デコレータとLocalAuthGuardsクラスを使用することでログインAPI実行時にLocalAuthGuardsクラス内のvalidateメソッドが実行されてからcontroller内の`this.authService.login(req.user)`が実行されます

JWTトークンの作成はauth.service.tsのloginメソッド内で行われます
また、プロファイル情報取得APIではユーザがログインしている場合は
以下のように
- username
- userId
- role

が返され、ログインしていない場合は401(UnAuthorized)のレスポンスを返します
`@UseGuards`デコレータとJwtStrategyクラスを使用することでAuthorization Header内のJWTトークンを照合し、以下のユーザ情報を返します

```json
{
    "username": "john",
    "userId": 1,
    "role": "admin"
}
```

```auth.controller.ts
import {
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Post,
  Request,
  UseGuards,
} from '@nestjs/common';
import { AuthService } from './auth.service';
import { ApiTags, ApiBody, ApiResponse } from '@nestjs/swagger';
import { JwtAuthGuard } from '../guards/jwt-auth.guard';
import { LocalAuthGuard } from '../guards/local-auth.guard';

@ApiTags('auth')
@Controller('api/auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @UseGuards(LocalAuthGuard)
  @HttpCode(HttpStatus.OK)
  @Post('login')
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        username: { type: 'string', example: 'john' },
        password: { type: 'string', example: 'test' },
      },
      required: ['username', 'password'],
    },
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Successful login',
    content: {
      'application/json': {
        example: [
          {
            access_token: "token_string",
          },
        ],
      },
    },
  })
  async login(@Request() req) {
    return this.authService.login(req.user);
  }

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
  @Get('profile')
  getProfile(@Request() req) {
    return req.user;
  }
}
```

serviceでは
- 認証
- ログイン

メソッドを作成します
validateUserメソッドではまずusernameから該当するユーザをDBから取得します
次にbcryptを使ってDB内のハッシュ化されたユーザのパスワードとリクエスト内のパスワードを照合します
```typescript
const user = await this.usersService.findOneByUsername(username)
```

でユーザが存在しない場合は`this.dummyHashを使って`パスワードが有効かダミー用のハッシュ値で照合します
上記を行うことでusernameが間違っていたとしてもハッシュの検証を行い、usernameがあっていることを処理時間で推測されないようにすることができます(タイミング攻撃対策)

```auth.service.ts
import { Injectable } from '@nestjs/common';
import { UsersService } from '../users/users.service';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';

@Injectable()
export class AuthService {
  constructor(
    private usersService: UsersService,
    private jwtService: JwtService
  ) {}

  private readonly dummyHash = bcrypt.hashSync('dummy', 10);

  async validateUser(username: string, pass: string): Promise<any> {
    const user = await this.usersService.findOneByUsername(username);
    const isPasswordValid = await bcrypt.compare(
      pass,
      user?.password ?? this.dummyHash
    );
    if (!user || !isPasswordValid) {
      return null;
    }
    const { password, ...result } = user;
    return result;
  }

  async login(user: any) {
    const payload = { username: user.username, userId: user.id, role: user.role };
    return {
      access_token: this.jwtService.sign(payload),
    };
  }
}
```

## 実際にログインしてみよう！
以下のようにログインできれば成功です

![Screenshot 2025-10-13 at 13.02.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/57ca1885-a7d9-4c43-a89a-7a89e36b6ae6.png)

以下のようにログインユーザの情報が返ってきたら成功です
![Screenshot 2025-10-13 at 13.02.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6272c0a8-92de-414c-9641-e4dc0c3e539b.png)



## 参考文献
https://docs.nestjs.com/recipes/passport

https://zenn.dev/uttk/articles/9095a28be1bf5d
