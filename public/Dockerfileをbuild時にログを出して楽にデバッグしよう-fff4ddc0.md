---
title: Dockerfileをbuild時にログを出して楽にデバッグしよう！
tags:
  - Docker
  - Linuxコマンド
  - docker-compose
private: false
updated_at: '2022-11-30T17:14:22+09:00'
id: fff4ddc0d7ae53665c2c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 背景
- docker buildする際にログが高速で流れてしまうため、どこでエラーが起きているか詳しく知りたい

## Docker imageをbuildするとき
Pythonのimageを例に出します
```Dockerfile
FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY . /code/
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
```

imageのbuild時のログを見る際は
```terminal
docker compose build --progress=plain 
```
を実行すると下記のようにログが流れずに表示されます

```
docker compose build --progress=plain
#1 [<image名>-nginx internal] load build definition from Dockerfile.dev
#1 transferring dockerfile: 35B 0.0s done
#1 DONE 0.0s

#2 [<image名>-app internal] load build definition from Dockerfile
#2 transferring dockerfile: 270B done
#2 DONE 0.0s

#3 [<image名>-db internal] load build definition from Dockerfile
#3 transferring dockerfile: 304B done
#3 DONE 0.0s

#4 [<image名>-nginx internal] load .dockerignore
#4 transferring context: 2B 0.0s done
```

### ビルドコンテキストがわからなくなる時
例えば指定したディレクトリが間違っていたせいでrequirements.txtやpoetry.tomlがないよ！というエラーが出た際に上記の
```
docker compose build --progress=plain 
```
とLinuxの`ls`コマンドと組み合わせて使うとデバッグが容易になります

```Dockerfile
FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY . /code/
# lsコマンドを実行。また、-laを入れるとファイルの権限まで見ることができる
RUN ls -la
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
```

### 実際にbuildしてみよう！
```
docker compose build --progress=plain 
```
を実行すると下記のようにWORKDIR内のファイル構成を確認できます
```terminal
#23 [<image名> 4/7] RUN ls -la
#23 0.541 total 168
#23 0.541 drwxr-xr-x  1 root root  4096 Nov 30 07:53 .
#23 0.541 drwxr-xr-x  1 root root  4096 Nov 30 07:53 ..
#23 0.541 drwxr-xr-x  2 root root  4096 Nov 30 07:53 .devcontainer
#23 0.541 -rw-r--r--  1 root root   307 Nov 30 05:24 .env
#23 0.541 -rw-r--r--  1 root root   315 Nov 14 04:30 .env.local
#23 0.541 drwxr-xr-x  8 root root  4096 Nov 30 07:53 .git
#23 0.541 drwxr-xr-x  4 root root  4096 Nov 30 07:53 .github
#23 0.541 -rw-r--r--  1 root root  3138 Nov 17 07:49 .gitignore
#23 0.541 drwxr-xr-x  3 root root  4096 Nov 30 07:53 .pytest_cache
#23 0.541 drwxr-xr-x  2 root root  4096 Nov 30 07:53 .vscode
#23 0.541 -rw-r--r--  1 root root  6458 Nov 29 02:02 README.md
#23 0.541 drwxr-xr-x  3 root root  4096 Nov 30 07:53 <プロジェクト名>
#23 0.541 drwxr-xr-x  5 root root  4096 Nov 30 07:53 containers
#23 0.541 drwxr-xr-x 10 root root  4096 Nov 30 07:53 <アプリケーション名>
#23 0.541 -rw-r--r--  1 root root  1085 Nov  8 02:53 docker-compose.prod.yml
#23 0.541 -rw-r--r--  1 root root  1339 Nov 16 00:59 docker-compose.yml
#23 0.541 -rw-r--r--  1 root root   282 Nov 17 08:07 entrypoint.bash
#23 0.541 -rwxr-xr-x  1 root root   683 Nov 13 23:06 manage.py
#23 0.541 -rw-r--r--  1 root root 76266 Nov 29 02:02 poetry.lock
#23 0.541 -rw-r--r--  1 root root   919 Nov 29 02:02 pyproject.toml
#23 0.541 -rw-r--r--  1 root root   173 Nov 29 02:02 pytest.ini
#23 0.541 -rw-r--r--  1 root root   387 Nov  8 03:00 set-up-env.test.sh
#23 0.541 drwxr-xr-x  5 root root  4096 Nov 30 07:53 static
#23 DONE 0.6s
```

## まとめ
Dockerfileをbuildする際にログが早く流れすぎてデバッグしずらかったのですがこのコマンドを知ってからかなりやりやすくなりました

## 記事の紹介
以下の記事も書きましたのでよかったら見てみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/35c97c95079ecbe80e9d

https://qiita.com/shun198/items/a66d6214cdab5629029d

https://qiita.com/shun198/items/9e4fcb4479385217c323

