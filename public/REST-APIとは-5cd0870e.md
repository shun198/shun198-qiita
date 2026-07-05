---
title: REST APIとは？
tags:
  - API
  - HTTP
  - REST-API
private: false
updated_at: '2023-10-22T20:28:59+09:00'
id: 5cd0870ef95e0fc248bc
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## そもそもAPIって何？
Application Programming Interfaceの略
他社が提供するサービス内の情報、機能を扱えるようにする仕組みのことです

## APIの種類
APIには
- HTTP/HTTPSベースで実現するWebAPI
- WindowsAPI

など色々ありますが、一般的にはAPIと言われたらWebAPIのことだと思っていただけたら大丈夫です

![API.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/48cc28b3-d577-f510-7f3e-f36ecc73d664.jpeg)


## 代表的なAPI(WebAPI)
- GitHub REST API

https://docs.github.com/ja/rest

- Twitter API

https://developer.x.com/en/docs

など

## APIのメリットは？
### ユーザ(APIを使用する個人、企業)側
- 開発コストの削減、効率化
    - 機能を１から作成せずにAPIを使うことで開発コストを削減できる
- セキュリティ面の向上
    - 機能やデータはAPIを開発者側が保持するため使用する側は意識しなくても良い
    - 特にユーザの口座情報などリスクの高い個人情報を扱う時に便利
- クォリティの向上
    - 特定の分野に特化した企業(Google、Amazonなど)が提供しているAPIはユーザ側が1から開発するより安価でハイクォリティ

あえてデメリットを挙げるとしたら
- APIの提供サービスに依存してしまう
    - 料金体系の変更やAPIの仕様変更に対応する必要がある
    - 開発者側のサーバに障害が起きると利用できなくなる

### 開発者(APIを提供、開発する個人、企業)側
- サービス連携が容易になり、ビジネスチャンスを拡大させることができる
    - APIを公開していると普段関わる可能性が低い企業とも繋がることができる
- 技術を隠蔽(ブラックボックス化)できる
    - APIのソースコードは非公開のため、技術流出リスクがない

## Web APIの主な設計思想について
主に
- RPC（Representational StateTransfer）
- SOAP（Simple Object Access Protocol）
- REST（Remote Procedure Call）

が挙げられますが、現在主流となっているのがREST APIです
RPC、SOAPに関して気になる方は調べてみてください

## REST APIとは？
RESTという設計思想に沿って作成されたAPI
REpresentational State Transferの略で
- 統一インターフェース（Uniform Interface）
- アドレス可能性（Addressability）
- 接続性（Connectability）
- ステートレス性(Stateless)

の4つの原則から成り立っています
REST APIという共通の設計思想があることでユーザ側・開発者側双方にとって利用、開発が容易になります

### 統一インターフェース（Uniform Interface）
操作のやり取りをする方法を統一することです
WebAPIの操作はHTTPメソッドで統一されています
主なHTTPメソッドと役割は以下のとおりです。

|HTTPメソッド|役割|
|------|------|
|GET|データを取得|
|POST|データを新規作成|
|PUT|データを更新|
|DELETE|データを削除|

また、やり取りする際のデータ形式は主にXMLかJSONになります

![API-Uniform Interface (1).jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/540e2b7d-8496-9667-49bd-809e3e0ae402.jpeg)



### アドレス可能性（Addressability）
1つのURIで全ての機能を実現できるようにすることです
全ての情報が一意のURIで表現されます

![API-address.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a1951034-e7b7-284e-021f-a5a1476f2b46.jpeg)


### 接続性（Connectability）
情報のなかに、別の情報へのリンクが含まれることです
リンクを含めることで別の情報へ接続することができるようになります
![API-connectability.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7846311f-5210-7f37-1a1a-705059d309eb.png)


### ステートレス性(Stateless、状態を持たないの意味)
全てのリクエストが完全に分離していることです
つまり、それぞれのリクエスト同士が影響し合うことがないことです
通常、ステートレスな状態だとユーザの状態(ログイン情報)を持たないことになります
そこで、ユーザのログイン情報を持った状態でRestAPIを使用する、つまりステートフル(状態をもつ)にするにはCookie(ユーザの情報を保存する仕組み)とSessionID(ユーザを認証するための一意のID)を使うのが一般的です

![API-stateless.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8d6fca39-1b1d-3dbc-d00b-6f17e556b04f.png)

## 最後に
RESTAPIという単語はなんとなく知ってたものの、調べることで理解が深まりました

## 参考
https://www.jbat.co.jp/dx_blog_5/

https://blog.hubspot.jp/api-rest#:~:text=%E9%96%8B%E7%99%BA%E8%80%85%E3%81%8CREST%20API,%E3%81%99%E3%82%8B%E7%82%B9%E3%82%82%E3%83%A1%E3%83%AA%E3%83%83%E3%83%88%E3%81%A7%E3%81%99%E3%80%82

https://appmaster.io/ja/blog/rest-apitohahe-desuka-ta-notaiputodonoyouniyi-narimasuka

https://www.redhat.com/ja/topics/api/what-is-a-rest-api#:~:text=REST%20API%20(RESTful%20API%20%E3%81%A8%E3%82%82,API%20%E3%81%BE%E3%81%9F%E3%81%AF%20Web%20API)%20%E3%81%A7%E3%81%99%E3%80%82

https://www.contents.digitallab.jp/api.html
