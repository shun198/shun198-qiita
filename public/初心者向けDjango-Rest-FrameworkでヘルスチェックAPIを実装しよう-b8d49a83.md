---
title: 【初心者向け】Django Rest FrameworkでヘルスチェックAPIを実装しよう！
tags:
  - Django
  - swagger
  - django-rest-framework
private: false
updated_at: '2024-07-10T08:04:34+09:00'
id: b8d49a830528addfae56
organization_url_name: null
slide: false
---
## ヘルスチェックとは？
システムが正常に稼働しているかどうかを確認することです
通常はALBからEC2またはECSへ向けてヘルスチェックを行います

## 実装してみよう！
今回は
- プロジェクトのurls.py
- アプリケーションのurls.py
- views.py

を編集し、`api/health`のエンドポイントを作成して実際にヘルスチェックを行う方法まで説明します

### プロジェクトのurls.py
プロジェクトにapi/のエンドポイントを作成します
```プロジェクト名/urls.py
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # api/のエンドポイントを作成
    path("api/", include("relationships.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # SwaggerUIの設定
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redocの設定
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
```

Swaggerの設定方法は下記の記事を参考にしてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

### アプリケーションのurls.py
`health/`のエンドポイントを作成します
```アプリケーション名/urls.py
from django.urls import path
from アプリケーション名.views.health_check import health_check

urlpatterns = [
    path("health/", health_check, name="health"),
]
```

### views.py
今回は`api/health`へGETすると200を返すだけの簡単なヘルスチェックを作成します

```views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return JsonResponse(data={"msg":"pass"},status=200)
```

## Swaggerで動作を確認しよう！
上記の設定を行ったら`api/docs`へアクセスします
![スクリーンショット 2022-11-02 19.17.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cc7c11d3-e469-0c5e-af32-027adfb8f591.png)

GETをすると設定したメッセージがresponseとして返ってくることが確認できました
![スクリーンショット 2022-11-02 19.18.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8ab1fa10-5fe1-0124-6114-eb58f9be39e7.png)

## まとめ
ヘルスチェックに関しては全てのプロジェクトで行うのでテンプレート化してもいいかもですね
