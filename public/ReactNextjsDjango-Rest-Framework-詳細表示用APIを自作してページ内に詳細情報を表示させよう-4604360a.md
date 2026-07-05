---
title: '[React(Next.js)+Django Rest Framework] 詳細表示用APIを自作してページ内に詳細情報を表示させよう！'
tags:
  - TypeScript
  - React
  - django-rest-framework
  - Next.js
private: false
updated_at: '2023-12-13T22:35:31+09:00'
id: 4604360a3af39e6f086d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
React/Next.jsを使って画面を作成し、Django Rest Frameworkを使ってAPIと疎通した上でデータを詳細表示させる方法について解説します
今回作成するお客様詳細画面は以下の通りです

![スクリーンショット 2023-12-13 21.55.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eb256ceb-5f67-6f7e-a192-41a1868d82ec.png)

## 前提
- Django、React(Next.js)のプロジェクトを作成済み
- Material UIとTailwind CSSを使用しますが今回は説明しません
- 一覧表示画面の記事の続きになりますので一覧表示画面とAPIの作成方法などについてピンと来ない方は以下の記事を参考にしてください

https://qiita.com/shun198/items/d26a9790f049bc6383a3

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
│       ├── 404
│       |   └── index.tsx
│       ├── customers
│       |   ├── [id]
│       |   │    └── index.tsx
│       |   └── index.tsx
│       └── index.tsx
└── static

```

## お客様詳細表示API
以下の記事の続きになるので
- serializer
- view

の順に作成します

https://qiita.com/shun198/items/d26a9790f049bc6383a3

### serializer
- 一覧表示
- 詳細表示

用のSerializerに分けます
```serilaizers.py
from django.utils import timezone
from rest_framework import serializers

from application.models import Customer


class ListCustomerSerializer(serializers.ModelSerializer):
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
        rep = super(ListCustomerSerializer, self).to_representation(instance)
        rep["created_at"] = timezone.localtime(instance.created_at).strftime(
            "%Y/%m/%d"
        )
        rep["updated_by"] = instance.updated_by.username
        return rep


class DetailCustomerSerializer(serializers.ModelSerializer):
    """ユーザ詳細表示用シリアライザ"""

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["id"]

    def to_representation(self, instance):
        rep = super(DetailCustomerSerializer, self).to_representation(instance)
        rep["address"] = (
            instance.address.prefecture
            + instance.address.municipalities
            + instance.address.house_no
            + instance.address.other
        )
        rep["post_no"] = instance.address.post_no
        rep["created_by"] = instance.created_by.username
        rep["updated_by"] = instance.updated_by.username
        return rep

```

### View
メソッドごとに使用するSerializerを分けます
```views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from application.models import Customer
from application.serializers.customer import (
    DetailCustomerSerializer,
    ListCustomerSerializer,
)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("address")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        match self.action:
            case "list":
                return ListCustomerSerializer
            case "retrieve":
                return DetailCustomerSerializer
            case _:
                return None

```

## お客様一覧画面
お客様一覧画面内に詳細ボタンを作成します
idはitemの中から取得します

```customers/index.tsx
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

## 404画面
存在しないIDを入力した時に表示させる画面を作成します
```tsx
import React from "react";

const NotFoundPage = () => {
  return (
    <div>
      <h1>Page Not Found</h1>
    </div>
  );
};

export default NotFoundPage;

```

## お客様詳細表示画面
今回作成するお客様詳細画面です

```customers/[id]/index.tsx
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import Cookies from "js-cookie";
import List from '@mui/material/List';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import SmartphoneIcon from '@mui/icons-material/Smartphone';
import EmailIcon from '@mui/icons-material/Email';
import CakeIcon from '@mui/icons-material/Cake';
import PersonIcon from '@mui/icons-material/Person';
import HomeIcon from '@mui/icons-material/Home';
import BadgeIcon from '@mui/icons-material/Badge';
import ListItem from '@mui/material/ListItem';
import SignpostIcon from '@mui/icons-material/Signpost';

type CustomerDetailData = {
  id: number;
  name: string;
  kana: string;
  birthday: Date;
  email: string;
  phone_no: string;
  address: string;
  post_no: string;
  updated_by: string;
};

function CustomerDetail() {
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState<Boolean>(true);
  const [data, setData] = useState<any>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = `http://localhost/back/api/customers/${router.query.id}/`;
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
          const responseData: CustomerDetailData = await response.json();
          setData(responseData);
          setLoggedIn(true);
        } else if (response.status === 403) {
          setLoggedIn(false);
          router.push("/"); // ログインしていない場合にルートページにリダイレクト
        } else if (response.status === 404) {
          router.replace("/404"); // IDが存在しない場合は404ページへリダイレクト
        } else {
          alert("エラーが発生しました");
        }
      } catch (error) {
        console.error("データの取得に失敗しました:", error);
      }
    };

    if (router.isReady) {
      fetchData();
    }
  }, [router.isReady]);

  useEffect(() => {
    if (!loggedIn) {
      router.push("/");
    }
  }, [loggedIn]);

  if (!data) return null;

  return (
    <div className="customer-details">
      <h1 className="justify-center">お客様詳細</h1>
      <List>        
        <ListItem disablePadding>
          <ListItemIcon>
              <PersonIcon />
          </ListItemIcon>
          <ListItemText>{data.name}({data.kana})</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <CakeIcon />
          </ListItemIcon>
          <ListItemText>{data.birthday}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <EmailIcon />
          </ListItemIcon>
          <ListItemText>{data.email}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <SmartphoneIcon />
          </ListItemIcon>
          <ListItemText>{data.phone_no}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <HomeIcon />
          </ListItemIcon>
          <ListItemText>{data.address}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <SignpostIcon />
          </ListItemIcon>
          <ListItemText>{data.post_no}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <BadgeIcon />
          </ListItemIcon>
          <ListItemText>{data.updated_by}</ListItemText>
        </ListItem>
      </List>
    </div>
  );
}

export default CustomerDetail;

```

### 詳細表示のAPIからデータを取得
fetchDataという関数を使って関数内にAPIを実行し、response.okの場合はsetDataメソッドを実行し、dataのArrayに入れる処理を記載します
ログインしているか知りたいのでuseStateを使ってresponseの内容に応じて以下の処理を実行します
- response.okの時
    - loggedInをTrueに変更
- ステータスコードが403の時
    - loggedInをFalseに変更し、ログイン画面へリダイレクト
- ステータスコードが404の時
    - 404ページへリダイレクト

今回404エラー時にrouter.replace()を使用しているのは、指定したURL(/404)をアクセスしたURLの履歴として残さずににページ遷移できるからです

> router.replace will prevent adding a new URL entry into the history stack.

https://nextjs.org/docs/pages/api-reference/functions/use-router#routerreplace

#### idを動的に変えるには
router.query.idから一覧画面内の詳細ボタンを押した時に入るIDを取得できます
ただし、初回ロード時にidがundefinedになってしまいます
そこで、useEffectを使ってrouter.isReadyがTrueになったタイミングでfetchDataを使ってデータを取得する処理を実行するようにします
isReadyがTrueだとRouterが使えるようになるので初回ロード時にundefinedになってしまうのを防ぐことができます

> isReady: boolean - Whether the router fields are updated client-side and ready for use. Should only be used inside of useEffect methods and not for conditionally rendering on the server. See related docs for use case with automatically statically optimized pages

```tsx
  const router = useRouter();
  const [loggedIn, setLoggedIn] = useState<Boolean>(true);
  const [data, setData] = useState<any>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = `http://localhost/back/api/customers/${router.query.id}/`;
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
          const responseData: CustomerDetailData = await response.json();
          setData(responseData);
          setLoggedIn(true);
        } else if (response.status === 403) {
          setLoggedIn(false);
          router.push("/"); // ログインしていない場合にルートページにリダイレクト
        } else if (response.status === 404) {
          router.replace("/404"); // IDが存在しない場合は404ページへリダイレクト
        } else {
          alert("エラーが発生しました");
        }
      } catch (error) {
        console.error("データの取得に失敗しました:", error);
      }
    };

    if (router.isReady) {
      fetchData();
    }
  }, [router.isReady]);
```

### ログイン有無の確認
useEffectを使ってloggedInの変数が変わったタイミングで処理を実施します
loggedInがFalseの場合はルートページへリダイレクトさせます
ログイン機能について詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/9f8f92d91caef0d47727

```
  useEffect(() => {
    if (!loggedIn) {
      router.push("/");
    }
  }, [loggedIn]);
```

### 詳細の描画
ページをレンダリングし、APIが実行されると以下のようにリクエストが送られるので
今回はdataの中身をmap関数を使って展開していきます

![スクリーンショット 2023-12-13 22.32.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f5a8523d-2c3a-29fe-0f40-33534566bb39.png)

```tsx
  if (!data) return null;

  return (
    <div className="customer-details">
      <h1 className="justify-center">お客様詳細</h1>
      <List>        
        <ListItem disablePadding>
          <ListItemIcon>
              <PersonIcon />
          </ListItemIcon>
          <ListItemText>{data.name}({data.kana})</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <CakeIcon />
          </ListItemIcon>
          <ListItemText>{data.birthday}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <EmailIcon />
          </ListItemIcon>
          <ListItemText>{data.email}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <SmartphoneIcon />
          </ListItemIcon>
          <ListItemText>{data.phone_no}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <HomeIcon />
          </ListItemIcon>
          <ListItemText>{data.address}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <SignpostIcon />
          </ListItemIcon>
          <ListItemText>{data.post_no}</ListItemText>
        </ListItem>
        <ListItem disablePadding>
          <ListItemIcon>
              <BadgeIcon />
          </ListItemIcon>
          <ListItemText>{data.updated_by}</ListItemText>
        </ListItem>
      </List>
    </div>
  );
```

## 実際に表示させてみよう！
大阪太郎の担当者の横の詳細ボタンを押します
![スクリーンショット 2023-12-13 22.33.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4e898af6-b4d9-5a6c-7d9d-9c466d570962.png)

以下のように表示させることができたら成功です

![スクリーンショット 2023-12-13 21.55.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eb256ceb-5f67-6f7e-a192-41a1868d82ec.png)

また、
http://localhost/customers/10000000-0000-0000-0000-000000000001

のように存在しないIDを入力すると以下の404画面が表示されたら成功です

![スクリーンショット 2023-12-13 22.35.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e03fc2ee-ac61-5cea-c816-d193c286d952.png)

## 参考
https://mui.com/material-ui/react-list/

https://zenn.dev/tanoshima/articles/b940659de3709d

https://qiita.com/hinako_n/items/d24488935d9bff19188f

https://thunder-fury-devlog.netlify.app/blog/next-js-router-query-id-undefined/

https://nextjs.org/docs/pages/api-reference/functions/use-router#routerpush

https://qiita.com/ke_na/items/ee6a6edd24847c616b62
