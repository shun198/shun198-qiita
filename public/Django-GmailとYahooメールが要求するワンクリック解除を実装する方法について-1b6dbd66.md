---
title: '[Django] GmailとYahooメールが要求するワンクリック解除を実装する方法について'
tags:
  - Django
  - AWS
  - ses
  - Gmail
  - Yahoo
private: false
updated_at: '2024-07-20T21:10:54+09:00'
id: 1b6dbd667a092a1c0947
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
2024年の2月からGmailとYahooでは1日5000通以上のメールを送信する場合はワンクリックによるメール購読解除機能を実装することが求められるようになりました
実装する際は以下の情報をメールのヘッダに追加する必要があるのでその方法について解説していきます

```
List-Unsubscribe-Post: List-Unsubscribe=One-Click
List-Unsubscribe: <https://some-system.jp/unsubscribe/example>
````

## 前提
- Djangoのプロジェクトを作成およびデプロイ済み
- Djangoのプロジェクト内でメール送信設定が完了済み
- AWS SESの設定が完了済み

## 実装
今回はDjangoのEmailMultiAlternativesクラスを使ってメールを送信します
EmailMultiAlternativesクラス内にヘッダを指定できるので以下のように記載します

```emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_email(email):
    """メールを送信する

    Args:
        email (str): 送信先Eメール
        name (str): ユーザ名
    """
    plaintext = render_to_string(
        "send_email.txt",
    )

    msg = EmailMultiAlternatives(
        subject="テスト",
        body=plaintext,
        from_email="noreply@example.com",
        to=[email],
        headers={
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            "List-Unsubscribe": "<https://example.com>",
        },
    )

    # 送信
    msg.send()
```


```django/core/mail/message.py
class EmailMultiAlternatives(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/alternative
    messages. For example, including text and HTML versions of the text is
    made easier.
    """

    alternative_subtype = "alternative"

    def __init__(
        self,
        subject="",
        body="",
        from_email=None,
        to=None,
        bcc=None,
        connection=None,
        attachments=None,
        headers=None,
        alternatives=None,
        cc=None,
        reply_to=None,
    ):
```

## 実際に送信してみよう！
以下のように送信したメールにヘッダが表示されたら成功です

![スクリーンショット 2024-07-20 21.07.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/beb75eb3-ad34-c1a4-8ccb-b66e5a72a3a0.png)


## 登録解除リンクが表示されない場合は
登録解除リンクについてはGoogle側でドメインが信頼できるかどうかと一定数以上の購読者がいるかどうかを確認してから表示させる仕様だそうです

https://support.google.com/mail/thread/49653586?hl=en&msgid=49801705

## 参考
https://mailmarketinglab.jp/gmail-one-click-unsubscribe/

https://note.shiftinc.jp/n/n37e894acbcf3

https://support.google.com/a/answer/81126?sjid=8610702489842767047-AP

https://datatracker.ietf.org/doc/html/rfc8058

https://support.google.com/mail/thread/49653586?hl=en&msgid=49801705

