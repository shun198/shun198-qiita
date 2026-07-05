---
title: '[Django Rest Framework] Djangoのget_object_or_404について注意すべきこと'
tags:
  - Django
  - django-rest-framework
private: false
updated_at: '2025-01-18T10:52:28+09:00'
id: f980cdf98d05ef7df05d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Djangoの便利メソッドであるget_object_or_404について使用する際の注意点について解説していきたいと思います

## 前提
- DRFを使用する方向けに記事を執筆しています

## get_object_or_404とは？
Djangoの便利メソッドの一つで下記のように引数にModelとpkを指定することで存在すればuserのオブジェクトを返し、存在しなければ404を返します
```python
user = get_object_or_404(User,pk=1)
```

やっていることは下記と同じで一行で実現できるのでとても便利です
詳細は公式ドキュメントを参照してください
```python
try:
    user = User.objects.get(pk=1)
except User.DoesNotExist:
    raise Http404("No User matches the given query.")
```

https://docs.djangoproject.com/ja/5.0/topics/http/shortcuts/

## 試しにget_object_or_404を使ってみよう
以下のようにユーザを有効・無効化するAPIを作成してみました
今回はget_object_or_404の挙動を理解するためのサンプルコードを作成しているのでコードの詳細については理解できなくても問題ないです

```application/views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from application.models import User


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = None

        
    @action(detail=True, methods=["post"])
    def toggle_user_active(self, request, pk):
        """ユーザを有効化/無効化するAPI
        Args:
            request : リクエスト
            pk : ユーザID
        Returns:
            JsonResponse
        """
        user = get_object_or_404(User,pk=pk)
        if request.user == user:
            return JsonResponse(
                data={"msg": "自身を無効化することはできません"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse(data={"is_active": user.is_active})
```

まず、存在するIDを使って実行します
今回はUUIDを使用しています
下記のように200を返していたら成功です

![スクリーンショット 2024-01-07 10.44.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5f19de2b-6330-f7c8-20f2-3ba3624fd86f.png)

続いて存在しないUUIDを使って実行します
下記のように404を返していたら成功です

![スクリーンショット 2024-01-07 10.47.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d51d9ce8-a468-f3c3-e817-6aa2ecf802b2.png)

## Djangoのget_object_or_404の問題点について
ここまでのケースだと一見Djangoのget_object_or_404を使うとすごくいいように思えます
しかし、今回はUserのIDをUUIDにしてますがたとえばURLにIDを直打ちする際に間違えてUUID以外の形式で入力してしまうケースの場合だと下記のように500エラーを返してしまいます

![スクリーンショット 2024-01-07 10.42.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0b67637d-5cc9-6ff0-3fab-ddcc9d676273.png)

どうして500を返してしまうのは解説します
get_object_or_404のソースコードを見てみましょう

```django.shortcuts.py
def get_object_or_404(klass, *args, **kwargs):
    """
    Use get() to return an object, or raise an Http404 exception if the object
    does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Like with QuerySet.get(), MultipleObjectsReturned is raised if more than
    one object is found.
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, "get"):
        klass__name = (
            klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        )
        raise ValueError(
            "First argument to get_object_or_404() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        raise Http404(
            "No %s matches the given query." % queryset.model._meta.object_name
        )
```

下記の処理でtry exceptを使ってModelのオブジェクトが存在しなかったら404をraiseする処理を記載しているので一見大丈夫のように思えます
しかし、ここで注意したいのはUUID以外のIDを入れてしまうとValidationErrorを返してしまうことです
そのため、ValidationErrorが発生したら404をraiseする処理を入れていないため、500を返してしまいます

```python
try:
    return queryset.get(*args, **kwargs)
except queryset.model.DoesNotExist:
    raise Http404(
        "No %s matches the given query." % queryset.model._meta.object_name
    )
```


## Djangoのget_object_or_404ではなく、rest_frameworkのGenericAPIViewのget_objectを使おう！
rest_frameworkにはDjangoのget_object_or_404のような便利メソッドがあるので紹介します
ModelViewSetのようにGenericAPIViewクラスをoverrideしているViewを使用している場合は
get_objectメソッドを使用できます

```rest_framework.generics.py
"""
Generic views that provide commonly needed behaviour.
"""
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404

from rest_framework import mixins, views
from rest_framework.settings import api_settings


def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError, ValidationError):
        raise Http404


class GenericAPIView(views.APIView):
    """
    Base class for all other generic views.
    """
    # You'll need to either set these attributes,
    # or override `get_queryset()`/`get_serializer_class()`.
    # If you are overriding a view method, it is important that you call
    # `get_queryset()` instead of accessing the `queryset` property directly,
    # as `queryset` will get evaluated only once, and those results are cached
    # for all subsequent requests.
    queryset = None
    serializer_class = None

    # If you want to use object lookups other than pk, set 'lookup_field'.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = 'pk'
    lookup_url_kwarg = None

    # The filter backend classes to use for queryset filtering
    filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
```

get_objectメソッド内でrest_framework.genericsのget_object_or_404を使用しています

```python
    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
```

rest_frameworkのget_object_or_404内で
- TypeError
- ValueError
- ValidationError

をraiseしてからDjangoのget_object_or_404を実行する処理を記載しています
そのため、先ほどの例のようにUUID以外の形式のIDを入れてAPIを実行しても404をraiseしてくれるようになります
今までDjango Rest FrameworkでDjangoのget_object_or_404を使ってAPIを実装していた場合は今後rest_frameworkのget_objectまたはget_object_or_404を使いましょう

```python
def get_object_or_404(queryset, *filter_args, **filter_kwargs):
    """
    Same as Django's standard shortcut, but make sure to also raise 404
    if the filter_kwargs don't match the required types.
    """
    try:
        return _get_object_or_404(queryset, *filter_args, **filter_kwargs)
    except (TypeError, ValueError, ValidationError):
        raise Http404
```

## rest_frameworkのget_objectを使ってもう一度検証してみよう！
userのオブジェクトを取得する処理を変えたうえでもう一度実行します

```application/views.py
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from application.models import User


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = None

        
    @action(detail=True, methods=["post"])
    def toggle_user_active(self, request, pk):
        """ユーザを有効化/無効化するAPI
        Args:
            request : リクエスト
            pk : ユーザID
        Returns:
            JsonResponse
        """
        user = self.get_object()
        if request.user == user:
            return JsonResponse(
                data={"msg": "自身を無効化することはできません"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse(data={"is_active": user.is_active})
```

下記のように404を返したら成功です
![スクリーンショット 2024-01-07 11.00.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b4a7ad38-003f-6e7e-64b0-0d992e694e05.png)

## まとめ
今までよく分からずにget_object_or_404を使っていた方は今回の記事を読んで理解が深まれば幸いです

## 参考
https://github.com/django/django/blob/main/django/shortcuts.py

https://github.com/encode/django-rest-framework/blob/master/rest_framework/generics.py
