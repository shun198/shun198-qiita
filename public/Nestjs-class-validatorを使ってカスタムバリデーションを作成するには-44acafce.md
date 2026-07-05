---
title: '[Nest.js] class-validatorを使ってカスタムバリデーションを作成するには'
tags:
  - NestJS
  - class-validator
private: false
updated_at: '2024-03-31T08:51:22+09:00'
id: 44acafce057b4baf8486
organization_url_name: null
slide: false
---
## 概要
Nest.jsでバリデーションを行う際はdtoを作成し、class-validatorのデコレータを使って行うのが一般的です
しかし、class-validatorが提供しているデコレータだけでバリデーションできないケースがあるのでカスタムバリデーションを作成する方法について解説します

## 前提
- Nest.jsのアプリケーションを作成済み

## ディレクトリ構成
```
└── src
    ├── app.controller.ts
    ├── app.module.ts
    ├── app.service.ts
    ├── common
    │   └── validators.ts
    ├── main.ts
    └── user
        ├── dto
        │   └── verifyUser.dto.ts
        ├── user.controller.ts
        ├── user.module.ts
        └── user.service.ts
```

## dtoの作成
dtoを作成する際は以下のように例えばIsStringやMaxLengthなどのデコレータを使用するのが一般的です
今回は8桁の数字のみを許容するバリデーションを作成したいのですがclass-validatorが提供しているデコレータだけでは実現できません
そこで後述するカスタムバリデーションを作成して、デコレータとして適用します
その際は以下のようにValidateデコレータ内にIsEmployeeNumberクラスを引数として入れた状態で記載します

```dto/verifyUser.dto.ts
import { IsString, MaxLength, Validate } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { IsEmployeeNumber } from '../../common/validators';

export class VerifyUserDto {
  @ApiProperty()
  @IsString()
  @Validate(IsEmployeeNumber)
  employee_number: string;

  @ApiProperty()
  @IsString()
  @MaxLength(255)
  password: string;
}

```

## カスタムバリデーションの作成
カスタムバリデーションを作成する際はValidatorConstraintInterface内にvalidateとdefaultMessageの処理を実装する形で作成します
validateメソッドに適用したいバリデーションを作成し、defaultMessage内にバリデーションエラー時のエラーメッセージを記載します

```common/validators.ts
import {
  ValidatorConstraint,
  ValidatorConstraintInterface,
} from 'class-validator';

@ValidatorConstraint({ name: 'isEmployeeNumber' })
export class IsEmployeeNumber implements ValidatorConstraintInterface {
  validate(text: string) {
    // 8桁の数字のみを許容する正規表現パターン
    const pattern = /^\d{8}$/;
    return typeof text === 'string' && pattern.test(text);
  }

  defaultMessage() {
    return '社員番号は8桁の数字でなければなりません';
  }
}

```

## 実際に実行してみよう！
今回は以下のように社員番号とパスワードを使ってユーザが一致するかどうかの簡単なAPIを作成しています
先ほど作成したバリデーションを適用するためにVerifyUserDtoを使用します

```user.controller.ts
import { Controller, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { Post, Body } from '@nestjs/common';
import { UserService } from './user.service';
import { VerifyUserDto } from './dto/verifyUser.dto';

@ApiTags('users')
@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}
  
  @Post('verify_user')
  @HttpCode(HttpStatus.OK)
  verify_user(@Body() verifyUserDto: VerifyUserDto) {
    return this.userService.verify_user(verifyUserDto);
  }
}
```

以下のように8桁の数字以外を入力した状態でAPIを実行した際に作成したカスタムバリデーションが適用されたら成功です

![スクリーンショット 2024-03-30 21.53.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6e4bfa8c-2275-e25f-dc52-bd7098f0aba4.png)

![スクリーンショット 2024-03-30 21.54.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3c2efb75-fe75-2c7c-1861-37dc787e1823.png)

## 参考
https://github.com/typestack/class-validator?tab=readme-ov-file#custom-validation-classes

https://www.npmjs.com/package/class-validator#custom-validation-classes
