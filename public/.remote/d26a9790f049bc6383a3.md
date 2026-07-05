---
title: '[React(Next.js)+Django Rest Framework] 一覧表示用APIを自作してページ内にテーブルを表示させよう！'
tags:
  - TypeScript
  - React
  - django-rest-framework
  - Next.js
private: false
updated_at: '2023-12-19T09:10:59+09:00'
id: d26a9790f049bc6383a3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
React/Next.jsを使って画面を作成し、Django Rest Frameworkを使ってAPIと疎通した上でデータを一覧表示させる方法について解説します
今回作成するお客様一覧画面は以下の通りです

![スクリーンショット 2023-12-11 10.21.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3db03e22-c069-8d56-67fc-03dc347c143f.png)


## 前提
- Django、React(Next.js)のプロジェクトを作成済み
- Material UIとTailwind CSSを使用しますが今回は説明しません
- docker-compose.ymlとnginx.confを使用します。ソースコードは添付しますが詳細な説明は別記事のリンクを貼るのでそちらを参照してください

## ディレクトリ構成
```
tree
・
├── .gitignore
├── README.md
├── backend
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── fixture.json
│   │   ├── migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py
│   ├── poetry.lock
│   ├── project
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── pyproject.toml
├── containers
│   ├── django
│   │   ├── Dockerfile
│   │   ├── Dockerfile.prd
│   │   ├── entrypoint.prd.sh
│   │   └── entrypoint.sh
│   ├── front
│   │   └── Dockerfile
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── postgres
│       ├── Dockerfile
│       └── init.sql
├── docker-compose.yml
├── frontend
│   ├── README.md
│   ├── package-lock.json
│   ├── package.json
│   └── pages
│       └── customers
│           └── index.tsx
└── static
```

## docker-composeとNginxの設定
今回はフロントエンド側でAPIを使用するときは
```
http://localhost/back/
```
へリクエストを送るようdocker-composeとNginxの設定を行います
詳細は以下の記事の通りです

https://qiita.com/shun198/items/ee93c50eac2f7c77e443

https://qiita.com/shun198/items/c92977c6cd31eb2187fc

```docker-compose.yml
version: '3.9'

services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_NAME
      - POSTGRES_USER
      - POSTGRES_PASSWORD
    ports:
      - '5432:5432' # デバッグ用

  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./backend:/code
      - ./static:/static
    ports:
      - '8000:8000'
      # デバッグ用ポート
      - '8080:8080'
    command: sh -c "/usr/local/bin/entrypoint.sh"
    stdin_open: true
    tty: true
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  nginx:
    container_name: web
    build:
      context: .
      dockerfile: containers/nginx/Dockerfile
    volumes:
      - ./static:/static
    ports:
      - 80:80
    depends_on:
      - app

volumes:
  db_data:
  static:

networks:
  default:
    name: testnet

```

```nginx.conf
upstream front {
    server host.docker.internal:3000;
}

upstream back {
    server host.docker.internal:8000;
}
 
server {
    listen       80;
    server_name  localhost;

    client_max_body_size 5M;
    
    location / {
        proxy_pass http://front/;
    }
 
    location /back/ {
        proxy_set_header X-Forwarded-Host $host:$server_port;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass http://back/;
    }

    location /_next/webpack-hmr {
        proxy_pass http://front/_next/webpack-hmr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

}
```

## お客様一覧表示API
- model
- fixture
- serilaizer
- view
- url

の順番に作成します

### Model
- User
- Customer
- Address

の3種類のModelを作成します
UserのModelについてはDjangoのAbstractUserを継承して作成します
詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e


```models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """システムユーザ"""

    username_validator = UnicodeUsernameValidator()

    class Role(models.IntegerChoices):
        """システムユーザのロール

        Args:
            MANAGEMENT(0): 管理者
            GENERAL(1):    一般
            PART_TIME(2):  アルバイト
        """

        MANAGEMENT = 0, "管理者"
        GENERAL = 1, "一般"
        PART_TIME = 2, "アルバイト"

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    groups = None
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="システムユーザID",
    )
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r"^[0-9]{8}$")],
        max_length=8,
        db_comment="社員番号",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        db_comment="ユーザ名",
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        db_comment="メールアドレス",
    )
    role = models.PositiveIntegerField(
        choices=Role.choices,
        default=Role.PART_TIME,
        db_comment="システムユーザのロール",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日",
    )
    is_verified = models.BooleanField(
        default=False,
        db_comment="有効化有無",
    )

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"
        db_table_comment = "システムユーザ"

    def __str__(self):
        return self.username


class Customer(models.Model):
    """お客様"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    kana = models.CharField(
        max_length=255,
        db_comment="カナ氏名",
    )
    name = models.CharField(
        max_length=255,
        db_comment="氏名",
    )
    birthday = models.DateField(
        db_comment="誕生日",
    )
    email = models.EmailField(
        db_comment="メールアドレス",
    )
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
        db_comment="電話番号",
    )
    address = models.OneToOneField(
        "Address",
        on_delete=models.CASCADE,
        related_name="address",
        db_comment="住所のFK",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日時",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_created_by",
        db_comment="作成者ID",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_updated_by",
        db_comment="更新者ID",
    )

    class Meta:
        db_table = "Customer"


class Address(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    prefecture = models.CharField(
        max_length=255,
        db_comment="都道府県",
    )
    municipalities = models.CharField(
        max_length=255,
        db_comment="市区町村",
    )
    house_no = models.CharField(
        max_length=255,
        db_comment="丁・番地",
    )
    other = models.CharField(
        max_length=255,
        blank=True,
        db_comment="その他(マンション名など)",
    )
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
        db_comment="郵便番号",
    )

    class Meta:
        db_table = "Address"

```

### Fixture
今回使用するテストデータを作成します
Userのパスワードは全てtestです

```fixture.json
[
    {
        "model": "application.User",
        "pk": 1,
        "fields": {
            "employee_number": "00000001",
            "username": "管理者ユーザユーザ01",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test01@example.com",
            "role": 0,
            "is_superuser": 0,
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 2,
        "fields": {
            "employee_number": "00000002",
            "username": "一般ユーザ01",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test02@example.com",
            "role": 1,
            "is_superuser": 0,
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 3,
        "fields": {
            "employee_number": "00000003",
            "username": "アルバイトユーザ01",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test03@example.com",
            "role": 2,
            "is_superuser": 0,
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 4,
        "fields": {
            "employee_number": "00000004",
            "username": "スーパーユーザ01",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test04@example.com",
            "role": 0,
            "is_superuser": 1,
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 1,
        "fields": {
            "kana": "オオサカタロウ",
            "name": "大阪太郎",
            "birthday": "1992-01-06",
            "email":"osaka@example.com",
            "phone_no": "08011112222",
            "address": 1,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 1,
            "updated_by": 1
        }
    },
    {
        "model": "application.Customer",
        "pk": 2,
        "fields": {
            "kana": "キョウトジロウ",
            "name": "京都二郎",
            "birthday": "1994-01-06",
            "email":"kyoto@example.com",
            "phone_no": "08022223333",
            "address": 2,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 2,
            "updated_by": 2
        }
    },
    {
        "model": "application.Customer",
        "pk": 3,
        "fields": {
            "kana": "ヒョウゴサブロウ",
            "name": "兵庫三郎",
            "birthday": "1995-03-06",
            "email":"hyogo@example.com",
            "phone_no": "08033334444",
            "address": 3,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 1,
            "updated_by": 1
        }
    },
    {
        "model": "application.Address",
        "pk": 1,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "清水",
            "other": "1-294",
            "post_no": "6050862"
        }
    },
    {
        "model": "application.Address",
        "pk": 2,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "北区金閣寺町1",
            "other": "",
            "post_no": "6038361"
        }
    },
    {
        "model": "application.Address",
        "pk": 3,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "左京区銀閣寺町2",
            "other": "",
            "post_no": "6068402"
        }
    }
]
```

### Serilaizer

一覧表示する際のバリデーションやデータの整形をするためにSerilaizerを実装します
created_atを受付日として使用するのでdjangoのtimezoneとstrftimeを使って整形します
また、updated_byを担当者として使用するので担当者の名前を表示できるようにCustomerのインスタンス内のupdated_by(User)のインスタンスのusername(システムユーザ名)を表示するようSerilaizerのto_representationを使用します

```serializers.py
from django.utils import timezone
from rest_framework import serializers

from application.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """ユーザ一覧表示用シリアライザ"""

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "kana",
            "email",
            "phone_no",
            "created_at",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_by",
        ]

    def to_representation(self, instance):
        rep = super(CustomerSerializer, self).to_representation(instance)
        rep["created_at"] = timezone.localtime(instance.created_at).strftime(
            "%Y/%m/%d"
        )
        rep["updated_by"] = instance.updated_by.username
        return rep
```

### View
今回はログイン認証ができたユーザのみAPIにアクセスできるようにします
また、CustomerとAddressの関係はmodels.pyに記載の通り1to1の関係です
Customer.objects.all()を使うとN+1回クエリが実行されるので今回はselect_relatedを使用します

```views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from application.models import Customer
from application.serializers import CustomerSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("address")
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
```

### url
CustomerのViewset内で作成したAPIを使用できるよう設定します
```urls.py
from rest_framework_nested import routers

from application.views.customer import CustomerViewSet
from application.views.health_check import health_check
from application.views.login import LoginViewSet

router = routers.DefaultRouter()
router.register(r"", LoginViewSet, basename="login")
router.register(r"customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"health/", health_check, name="health_check"),
]
```

## お客様一覧画面

```pages/customers/index.tsx
import { useState, useEffect } from "react";
import Cookies from "js-cookie";
import router from "next/router";
import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import { BasicMenu } from "@/components/buttons/MenuButton";
import { Button } from "@mui/material";

type CustomerData = {
  id: number;
  created_at: string;
  name: string;
  kana: string;
  updated_by: string;
};

type CustomerArray = CustomerData[];

function CustomerList() {
  const [data, setData] = useState<CustomerArray>([]);
  const [loggedIn, setLoggedIn] = useState<Boolean>(true); // ログイン状態を管理

  const fetchData = async () => {
    try {
      const apiUrl = "http://localhost/back/api/customers/";
      const csrftoken = Cookies.get("csrftoken") || "";
      const credentials = "include";

      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        credentials: credentials,
      });

      if (response.ok) {
        const responseData: CustomerArray = await response.json();
        setData(responseData);
        setLoggedIn(true);
      } else if (response.status === 403) {
        setLoggedIn(false);
      } else {
        alert("エラーが発生しました");
      }
    } catch (error) {
      console.error("データの取得に失敗しました:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!loggedIn) {
      router.push("/");
    }
  }, [loggedIn]);

  if (!data || !data.results) return null;

  return (
    <div className="customer-list">
      <BasicMenu />
      <br />
      <div className="flex flex-col items-center my-[10px]">
        <h1 className="text-3xl text-gray-900">お客様情報一覧</h1>
      </div>
      <div>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell align="center" className="font-bold">
                受付日
              </TableCell>
              <TableCell align="center" className="font-bold">
                お客様氏名
              </TableCell>
              <TableCell align="center" className="font-bold">
                お客様カナ氏名
              </TableCell>
              <TableCell align="center" className="font-bold">
                担当者
              </TableCell>
              <TableCell align="center" className="font-bold"></TableCell>
            </TableRow>
          </TableHead>
          {data.results.map((item, index) => {
            return (
              <TableBody key={index}>
                <TableCell align="center">{item.created_at}</TableCell>
                <TableCell align="center">{item.name}</TableCell>
                <TableCell align="center">{item.kana}</TableCell>
                <TableCell align="center">{item.updated_by}</TableCell>
                <TableCell align="center">
                  <Button
                    size="small"
                    variant="contained"
                    className="w-[100px] my-[10px]"
                    onClick={() => router.push(`/customers/${item.id}`)}
                  >
                    詳細
                  </Button>
                </TableCell>
              </TableBody>
            );
          })}
        </Table>
      </div>
    </div>
  );
}

export default CustomerList;

```

一つずつ解説していきます

### 一覧表示のAPIからデータを取得
fetchDataという関数を使って関数内にAPIを実行し、response.okの場合はsetDataメソッドを実行し、dataのArrayに入れる処理を記載します
ログインしているか知りたいのでuseStateを使ってresponse.okだったらloggedInをTrueに、ステータスコードが403の場合はloggedInをFalseにします
useEffectを使って初回レンダリング時のみデータを取得する処理を実行するようにします

```tsx
type CustomerData = {
  id: number;
  created_at: string;
  name: string;
  kana: string;
  updated_by: string;
};

type CustomerArray = CustomerData[];

  const [data, setData] = useState<CustomerArray>([]);
  const [loggedIn, setLoggedIn] = useState<Boolean>(true); // ログイン状態を管理
  
  const fetchData = async () => {
    try {
      const apiUrl = "http://localhost/back/api/customers/";
      const csrftoken = Cookies.get("csrftoken") || "";
      const credentials = "include";

      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        credentials: credentials,
      });

      if (response.ok) {
        const responseData: CustomerArray = await response.json();
        setData(responseData);
        setLoggedIn(true);
      } else if (response.status === 403) {
        setLoggedIn(false);
      } else {
        alert("エラーが発生しました");
      }
    } catch (error) {
      console.error("データの取得に失敗しました:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);
```

### ログイン有無の確認
useEffectを使ってloggedInの変数が変わったタイミングで処理を実施します
loggedInがFalseの場合はルートページへリダイレクトさせます
ログイン機能について詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/9f8f92d91caef0d47727

```tsx
  useEffect(() => {
    if (!loggedIn) {
      router.push("/");
    }
  }, [loggedIn]);

```

### 一覧の描画
ページをレンダリングし、APIが実行されると以下のようにリクエストが送られるので
今回はdata.resultsの中身をmap関数を使って展開していきます
![スクリーンショット 2023-12-11 10.35.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/30b88cae-0be5-eb01-b3d6-019d1b2c62e5.png)

```tsx
return (
    <div className="customer-list">
      <BasicMenu />
      <br />
      <div className="flex flex-col items-center my-[10px]">
        <h1 className="text-3xl text-gray-900">お客様情報一覧</h1>
      </div>
      <div>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell align="center" className="font-bold">
                受付日
              </TableCell>
              <TableCell align="center" className="font-bold">
                お客様氏名
              </TableCell>
              <TableCell align="center" className="font-bold">
                お客様カナ氏名
              </TableCell>
              <TableCell align="center" className="font-bold">
                担当者
              </TableCell>
              <TableCell align="center" className="font-bold"></TableCell>
            </TableRow>
          </TableHead>
          {data.results.map((item, index) => {
            return (
              <TableBody key={index}>
                <TableCell align="center">{item.created_at}</TableCell>
                <TableCell align="center">{item.name}</TableCell>
                <TableCell align="center">{item.kana}</TableCell>
                <TableCell align="center">{item.updated_by}</TableCell>
                <TableCell align="center">
                  <Button
                    size="small"
                    variant="contained"
                    className="w-[100px] my-[10px]"
                    onClick={() => router.push(`/customers/${item.id}`)}
                  >
                    詳細
                  </Button>
                </TableCell>
              </TableBody>
            );
          })}
        </Table>
      </div>
    </div>
  );
```

## 実際に表示させてみよう！
以下のように表示させることができたら成功です

![スクリーンショット 2023-12-11 10.21.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3db03e22-c069-8d56-67fc-03dc347c143f.png)

