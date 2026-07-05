---
title: '[Django Rest Framework] ページネーションについてカスタムページネーションの作成方法も含めて徹底解説'
tags:
  - Django
  - django-rest-framework
private: false
updated_at: '2023-11-12T14:37:46+09:00'
id: 6f64541565ae4057f942
organization_url_name: null
slide: false
---
## 概要
Django Rest Frameworkを使って
- PageNumberPagination
- LimitOffsetPagination
- 自作のカスタムページネーション

を使ってページネーションを適用する方法について解説します

## 前提
- Djangoのプロジェクトを作成済み

## はじめに
Django Rest Frameworkのページネーションクラスは
- PageNumberPagination
- LimitOffsetPagination

の2種類のうちのいずれかを使うのが一般的です

## PageNumberPagination
DEFAULT_PAGINATION_CLASSにPageNumberPaginationを指定します
今回はPAGE_SIZEを5とします

```settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
}
```

GETのAPIを実行するとデフォルトで指定したページ数に応じて表示される項目数が変わります
今回はPAGE_SIZEを5に指定したので一覧で5つ表示されます

![スクリーンショット 2023-11-12 13.42.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3011821c-6bad-b45e-b3b4-bb63cd7b7ac8.png)

以下のように
```
?page=2
```
と指定することでPagenationの何ページ目を一覧で取得できるか指定することができます

![スクリーンショット 2023-11-12 13.43.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6c861562-3d81-9e94-92b9-28bf8fb67658.png)


## LimitOffsetPagination
DEFAULT_PAGINATION_CLASSにLimitOffsetPaginationを指定します

```settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 5,
}
```

LimitOffsetPaginationを使用する際は
```
?limit=2&offset=2
```

とlimitに表示させるページ数、offsetに何番目のページかを指定することでPagenationの指定した項目数の指定したページを一覧で取得できます

![スクリーンショット 2023-11-12 13.56.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bc175885-56ed-50be-4642-1774dccc0125.png)

## カスタムページネーション
カスタムページネーションを作成する方法について解説します
今回はカスタムページネーションクラスをrest_frameworkのPageNumberPaginationクラスをOverrideして作成します
各ページネーションに表示させる内容は以下の通りです

|項目|説明|
|--|--|
|current|現在のページ数|
|final|最後のページ|
|count|項目数の合計|
|next|次のページネーションのリンク|
|previous|前のページネーションのリンク|
|results|表示される一覧データ|

また、1ページネーション内に表示する項目数を設定する際のパラメータをsizeにします

```application.utils.pagination.py
from rest_framework.pagination import PageNumberPagination

from rest_framework.response import Response
from collections import OrderedDict


class CustomPageNumberPagination(PageNumberPagination):
    # 1ページネーション内に表示する項目数にsizeパラメータを設定
    page_size_query_param = "size"
    max_page_size = 5

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("current", self.page.number),
                    ("final", self.page.paginator.num_pages),
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
```

現在のページ数と最後のページ数についてはrest_frameworkのpagitation.pyのget_html_context関数を見て実装しました

```rest_framework/pagination.py
    def get_html_context(self):
        base_url = self.request.build_absolute_uri()

        def page_number_to_url(page_number):
            if page_number == 1:
                return remove_query_param(base_url, self.page_query_param)
            else:
                return replace_query_param(base_url, self.page_query_param, page_number)

        # 現在のページ数を表示
        current = self.page.number
        # 最後のページ数を表示
        final = self.page.paginator.num_pages
        page_numbers = _get_displayed_page_numbers(current, final)
        page_links = _get_page_links(page_numbers, current, page_number_to_url)

        return {
            'previous_url': self.get_previous_link(),
            'next_url': self.get_next_link(),
            'page_links': page_links
        }
```


settings.pyに作成したページネーションクラスのパスを指定します

```settings.py
REST_FRAMEWORK = {
    # 作成したページネーションクラスのパスを指定
    'DEFAULT_PAGINATION_CLASS': 'application.utils.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 5,
}
```

今回はPageNumberPaginationクラスをOverrideしているので表示されるページ番号はpageパラメータを使って指定します
また、表示させる項目数は前述したsizeパラメータを使って指定します
```
?page=2&size=3
```

以下のようにパラメータを指定すると項目が3つ、2ページ目が表示されたら成功です

![スクリーンショット 2023-11-12 14.35.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4a8339b4-6990-e17f-132d-c0bffb965180.png)

## 参考
https://www.django-rest-framework.org/api-guide/pagination/
