---
title: Pydanticでメールアドレスのカスタムバリデーションを作成するには
tags:
  - FastAPI
  - pydantic
  - email-validator
private: false
updated_at: '2025-05-05T10:04:34+09:00'
id: 92c064ddc68b2b0a39a4
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Pydanticでたとえば特定のドメインのみ許可したい、などの要望があるときはPydanticのEmailStrを使うだけでなく、カスタムバリデーションを作成する必要があります
今回はEmailStr、email-validator、field_validatorのデコレータを使ってカスタムバリデーションを作成する方法について解説します

## 前提
- email-validatorをインストール済み(EmailStrを使用するにはemail-validatorがインストールされていないと使用できないため)
- フレームワークはFastAPIを使用

## 実装
```python
from pydantic import BaseModel, EmailStr, field_validator
from email_validator import validate_email, EmailNotValidError


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    is_admin: bool
    phone_number: str

    @field_validator("email")
    @classmethod
    def validate_custom_email(cls, value):
        try:
            allowed_domains = {"gmail.com", "test.com"}
            emailinfo = validate_email(value, check_deliverability=True)
            email = emailinfo.normalized
            if emailinfo.ascii_domain not in allowed_domains:
                raise ValueError(f"Only emails from {', '.join(allowed_domains)} are allowed")
            if not email.isascii():
                raise ValueError("Invalid email format")
            return email
        except EmailNotValidError:
            raise ValueError("Invalid email format")
```

順番に解説します

### validate_emailを使ったメールアドレスのバリデーション
Pydanticでカスタムバリデーションを作成するにはfield_validatorとclassmethodのデコレータを使用する必要があります
validate_email_methodでメールアドレスのバリデーションを行います
valueにはemailフィールドの値が入ります
check_deliverability=Trueにすることで初回のユーザ作成時などでDNSを使ったメールアドレスの存在確認ができます
今回はユーザ作成用のバリデーションをするためのBaseModelを定義しているのでTrueにしてますが、ログイン時などは無駄なDNSチェックを行わないようにFalseにすることが推奨されています

```python
    @field_validator("email")
    @classmethod
    def validate_custom_email(cls, value):
        try:
            allowed_domains = {"gmail.com", "test.com"}
            emailinfo = validate_email(value, check_deliverability=True)
```

### メールアドレスの正規化
email-validatorのREADMEに記載されていますが、IDNA ASCIIのドメイン名をUnicodeに変換し、ローカル部分とドメイン部分（元々Unicodeの場合）に対してUnicodeによる正規化を行うことが推奨されているので記載してます

```python
            email = emailinfo.normalized
```

### バリデーション
- メールアドレスが該当するドメインを持つか
- メールアドレス内にascii以外が含まれているか


のバリデーションを行います
メールアドレスにascii以外が含まれているかのバリデーションを入れているのはEmailStrでは全角文字を検知できないからです

```python
            if emailinfo.ascii_domain not in allowed_domains:
                raise ValueError(f"Only emails from {', '.join(allowed_domains)} are allowed")
            if not email.isascii():
                raise ValueError("Invalid email format")
            return email
        except EmailNotValidError:
            raise ValueError("Invalid email format")
```

## 実際に検証してみよう！
- メールアドレスが該当するドメインを持つか
- メールアドレス内にascii以外が含まれているか

の検証を行います
以下のようにAPIを実行し、エラーメッセージが表示されたら成功です

![スクリーンショット 2025-03-01 11.02.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b99552cb-b43e-4a02-ae20-7e2752742f92.png)

![スクリーンショット 2025-03-01 11.03.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5962ceef-514f-44aa-bb0e-cb80c55df916.png)

## 参考
https://github.com/JoshData/python-email-validator

https://stackoverflow.com/questions/76972389/fastapi-pydantic-how-to-validate-email

https://docs.pydantic.dev/latest/concepts/validators/#using-the-decorator-pattern
