---
title: S3へアップロードされたことをトリガーにzipファイルをLambdaを使って解凍しよう！
tags:
  - Python
  - AWS
  - S3
  - lambda
private: false
updated_at: '2024-05-10T14:23:20+09:00'
id: bfe56542a9e5bf1302cb
organization_url_name: null
slide: false
---
## 概要
S3へzipファイルがアップロードされたことをトリガーにzipファイルを解凍するLambdaを作成する方法について解説していきたいと思います

## 前提
- Pythonで解凍処理を作成します

## Lambdaの作成
zipファイルを解凍するLambdaを新規作成します
![スクリーンショット 2024-04-22 15.45.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79bf32d3-5dd4-6a2e-9427-396037764f1e.png)

今回は基本的なLambdaアクセス権限で新しいロールを作成します
![スクリーンショット 2024-05-10 13.46.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0a239a10-2092-415c-06d0-a55d9687c233.png)

## zipファイルを解凍する処理の作成
まず、S3へzipがアップロードされたことをトリガーに解凍処理をするので最初にeventから
- バケット
- オブジェクトキー

を取得します
次に解凍処理を実行するための一時フォルダを作成します
S3からZIPファイルをダウンロードし、一時フォルダに格納します
一時フォルダ内でZIPファイルからファイルを全て展開した後に一時ファイル内のZIPファイル以外のファイルをS3バケットへアップロードします
Lambdaの実行が完了したら一時ファイルは自動的に削除されます

```python
import boto3
import zipfile
import os
import tempfile

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    with tempfile.TemporaryDirectory() as tmpdir:
        download_path = os.path.join(tmpdir, os.path.basename(key))
        
        s3_client.download_file(bucket_name, key, download_path)
        
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

        for file in os.listdir(tmpdir):
            if file != os.path.basename(key):
                s3_client.upload_file(os.path.join(tmpdir, file), bucket_name, file)
             
```

## ロールの修正
Lambdaを使ってzipファイルを解凍するのでS3バケットへの
- オブジェクトのS3から取得
- オブジェクトをS3へ置く

権限を追加で付与します

![スクリーンショット 2024-05-10 13.46.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1334f67e-12ad-6ac3-e1ee-e60aa0f4b093.png)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup"
            ],
            "Resource": "arn:aws:logs:ap-northeast-1:xxxxxxxxxxxx:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:ap-northeast-1:xxxxxxxxxxxx:log-group:/aws/lambda/shun198-unzip-files-in-s3:*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::shun198-unzip-zip-file/*"
        }
    ]
}
```

## S3の作成
zipファイルをアップロードするS3バケットを作成します
![スクリーンショット 2024-04-22 15.50.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0a61ee90-5e66-6e29-e73a-d9f864309d1c.png)

![スクリーンショット 2024-04-22 15.50.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/434ded95-fd10-e9b6-d38b-79194cc3e97e.png)

## イベントの設定
ファイルのアップロードをトリガーにLambdaを実行できるよう、S3へイベントを設定します
![スクリーンショット 2024-04-22 15.51.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/53fd3ed6-c935-4cbf-28be-4c271e2d0260.png)

プロパティを選択します
![スクリーンショット 2024-04-22 15.56.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0ff0e942-c21c-876b-4a3f-dd48949e7481.png)

イベント通知を作成します
![スクリーンショット 2024-04-22 15.56.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3e96b1cd-2437-a28b-b05f-d3a8dba9ef48.png)

イベント名とサフィックスを設定します
今回はzipファイルがアップロードされたことをトリガーにしたいので.zipを指定します
![スクリーンショット 2024-04-22 15.57.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/db024600-1327-d966-d3c6-947a6404b206.png)

イベントタイプにPOSTを指定します
![スクリーンショット 2024-05-10 14.10.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9e754d15-afa1-057d-24e6-406927ed4ea1.png)

送信先に今回作成したLambdaを指定します
![スクリーンショット 2024-04-22 15.59.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/223c1819-0b42-fef6-3d20-0fbb3476204e.png)

以下のようにイベントが設定されていたら成功です
![スクリーンショット 2024-05-10 14.12.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/971ed835-212b-aab8-b75b-3671348fa61e.png)

## 実際にアップロードしてみよう！
作成したS3へzipファイルをアップロードします
![スクリーンショット 2024-04-23 8.55.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ecb3b6c5-f223-af4e-c921-311435bb8c97.png)

今回はimport_customer.zipというファイルをアップロードします
![スクリーンショット 2024-05-10 14.05.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d9976919-41c7-a4c8-d470-7aea1b9d55c6.png)

以下のようにzipファイルの中身が展開されていたら成功です
![スクリーンショット 2024-05-10 13.49.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/38a240ec-2d38-1e05-f640-90c8d62b5d79.png)

## 参考
https://github.com/maheshpeiris0/aws-lambda-auto-unzip-files-in-s3

https://docs.python.org/ja/3/library/tempfile.html#examples

https://docs.python.org/ja/3/library/zipfile.html#zipfile.ZipFile.extractall
