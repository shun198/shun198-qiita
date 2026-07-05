---
title: DjangoでSwaggerUIを使おう！設定方法を徹底解説
tags:
  - Django
  - swagger
  - django-rest-framework
  - DRF
  - OpenAPI
private: false
updated_at: '2024-03-14T07:36:36+09:00'
id: 23c6baa450ba37a5fd66
organization_url_name: null
slide: false
---
## はじめに
今回はDjangoでもSwaggerUIを使えるようにする方法について説明したいと思います

## 前提
- Djangoのプロジェクトを作成済み
- Djangoのアクセスするポート番号は8000を使用

## DjangoでもSwaggerUIを使おう！
- ローカル上で使用するとき
```terminal
pip install drf-spectacular
```

- requirements.txtを使用するとき
```requirements.txt
drf-spectacular==0.23.1
```

- poetryを使用するとき
```terminal:terminal
poetry add drf-spectacular 
```

## 各種設定
プロジェクト配下にある
- settings.py
- urls.py

に以下を記述します

### settings.py
```settings.py
INSTALLED_APPS = [
    "rest_framework",
    # 先ほどインストールしたdrf_spectacularを記述
    "drf_spectacular",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'プロジェクト名',
    'DESCRIPTION': '詳細',
    'VERSION': '1.0.0',
    # api/schemaを表示しない
    'SERVE_INCLUDE_SCHEMA': False,
}
```

### urls.py
```urls.py
from django.urls import path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # 127.0.0.1/8000/api/schema にアクセスするとテキストファイルをダウンロードできます
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # SwaggerUIの設定
    # 今回は127.0.0.1/8000/api/docs にアクセスするとSwaggerUIが表示されるよう設定します
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redocの設定
    # 今回は127.0.0.1/8000/api/redoc にアクセスするとRedocが表示されるよう設定します
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
```

http://127.0.0.1/api/docs へアクセスした際にSwaggerUIが出たら成功です
![スクリーンショット 2022-10-09 8.29.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0a632890-909f-dd8a-a270-ce71b589b240.png)

http://127.0.0.1/api/redoc にアクセスするとRedocも表示されます
![スクリーンショット 2022-10-09 8.33.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a81ff85f-86ae-ea44-cc11-a770bb765390.png)



ModelやViewに何も記述していない場合は以下のように
`No operations defined in spec!`
と表示されます
<img width="500"src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/772e277f-857e-4bf3-6fdc-9de263490ef1.png">

http://127.0.0.1/api/redoc も同様にModelやViewに何も記述していない場合は以下のように表示されます
<img width="500" src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d156af83-7805-5e91-25f0-aa69833ff5b7.png">

一度Swaggerの設定をすると

- ローカル上
- Docker

ともにホットリロードされるので変更のたびにローカル上でrunserverし直したり、コンテナを手動でrestartする必要がないのでとても便利です

## extend_schema
また、以下のようにextend_schemaを使うことでSwaggerを使用する際にrequest内のパラメータを予め指定したり200、400の時のレスポンス例を作成することもできます

```views.py
from application.models import User
from application.serializers.user import LoginSerializer, UserSerializer
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from project.settings import DEBUG
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet, ViewSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        """ユーザのログイン"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee_number = serializer.validated_data.get("employee_number")
        password = serializer.validated_data.get("password")
        user = authenticate(employee_number=employee_number, password=password)
        if not user:
            return JsonResponse(
                data={"msg": "社員番号またはパスワードが間違っています"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
            return JsonResponse(data={"role": user.Role(user.role).name})

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        """ユーザのログアウト"""
        logout(request)
        return HttpResponse()

    
    extend_schema(
        request=LoginSerializer,
        examples=[
            OpenApiExample(
                "ログイン",
                summary="ログインAPIのリクエスト",
                value={
                    "employee_number": "00000001",
                    "password": "test",
                },
                request_only=True,
                response_only=False,
                description="システムユーザーのログイン",
            )
        ],
        responses=OpenApiResponse(
            status.HTTP_200_OK,
            description="ログインが成功した場合",
            examples=[
                OpenApiExample(
                    "login",
                    summary={
                        "ログイン成功時のレスポンス",
                    },
                    value={
                        "role": User.Role.MANAGEMENT
                    },
                    request_only=False,
                    response_only=True,
                )
            ],
        ),
        summary="システムユーザーのログイン",
    )(LoginViewSet.login)
    
    extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="ログアウトに成功しました",
            ),
        },
        summary="システムユーザのログアウト",
    )(LoginViewSet.logout)
```

![スクリーンショット 2024-01-09 14.09.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b72b32d3-559d-b093-ba3f-1b7b4695a03f.png)

![スクリーンショット 2024-01-09 14.09.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8dc9792e-2fa6-d7a3-9147-e2f30903e0d3.png)

## drf-spectacularで自動生成したAPIドキュメントをymlに出力するには
下記のコマンドを実行するとymlファイルに出力できます
```
python manage.py spectacular --file schema.yml
```

ymlファイルに出力することができると、例えば下記のようにGitHub Pagesにアップロードできます

https://qiita.com/shun198/items/520806a86a14a4bd64a8

## 最後に
Swagger最高!

## 参考文献
https://qiita.com/mykysyk@github/items/fef6fb298393a029a5d4#swagger-%E3%81%AE%E6%9C%89%E5%8A%B9%E5%8C%96

https://akiyoko.hatenablog.jp/entry/2020/12/08/120230
