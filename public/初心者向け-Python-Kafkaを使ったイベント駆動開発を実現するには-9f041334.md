---
title: '[初心者向け] Python + Kafkaを使ったイベント駆動開発を実現するには？'
tags:
  - Python
  - ZooKeeper
  - Kafka
  - docker-compose
private: false
updated_at: '2025-06-01T15:58:19+09:00'
id: 9f04133420466c93ea25
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Apache Kafkaを使ったイベント駆動開発（Event-Driven Development）の方法についてPython、Kafka、compose.yamlを交えて解説します
構成としては以下のとおりです
- Producer
    - Brokerへイベントを送信するPythonのバッチ
- Broker
    - Kafkaのコンテナ
- Consumer
    - Brokerからのイベントを受け取るPythonのバッチ

## 前提
- confluent-kafkaを使用

## Kafkaとは
スケーラビリティに優れた分散型のストリーミングプラットフォームです
イベント駆動開発においては、アプリケーション間の非同期通信のハブの役割をはたします
覚えておきたい単語は以下のとおりです
- Producer
    - データを送る送信元
- Broker
    - アプリケーション間のデータの受け渡しを行うサーバー（Kafka本体）
- Consumer
    - データを受け取る受信元

KafkaはTopic単位でメッセージのやり取りを行っており、送信元(Producer)がBroker内のTopicにメッセージを書き込み、受信元(Consumer)はBroker内のTopicから受け取ったメッセージを購読します

## 実装
### Docker環境の構築
以下のコンテナをあらかじめ用意しておきます
- zookeeper
    - Kafkaクラスタのメタデータを保存・管理するための分散データベース
    - 主に以下を保存・管理する
        - Topicの一覧
        - Topicの設定値
        - Partitionの状態
        - Brokerの一覧
- broker
    - 後ほど作成するProducerからのメッセージを受け取り、Consumerへ送るために必要
- kafka-ui
    - ローカル上でメッセージ、TopicなどをGUI上で見るために使用(必須ではない)

```compose.yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.9.0
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  broker:
    image: confluentinc/cp-kafka:7.9.0
    container_name: broker
    ports:
      - "9092:9092"
    depends_on:
      - zookeeper
    environment:
      # zookeeperの接続設定。zookeeperのホスト名とポートを指定
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      # 今回はローカルで検証するため、KafkaとProducer、Consumer間で暗号化せずに通信する
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
      # Zookeeperを使用する際に必須。Zookeeperに接続可能なBrokerのホスト名を共有
      # broker:29092を指定することでKafkaがコンテナ外へアクセスできるようにする
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://broker:29092
      # Dockerのネットワーク内での通信に必要
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT_INTERNAL
      KAFKA_BROKER_ID: 1
      # single-nodeのクラスタで運用する場合は1を指定
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  kafka-ui:
    container_name: kafka-ui
    image: ghcr.io/kafbat/kafka-ui:v1.2.0
    ports:
      - "8090:8080"
    depends_on:
      - broker
    environment:
      KAFKA_CLUSTERS_0_NAME: local-cluster
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: broker:29092
```

https://docs.confluent.io/platform/current/installation/docker/config-reference.html#required-ak-configurations-for-zk-mode

### 環境変数
以下の環境変数を使用します
BROKER_URLはBrokerのコンテナのホスト名を指定します

```.env
TOPIC_NAME=my-topic
BROKER_URL=localhost:9092
GROUP_ID=fastapi-consumer-group
```

### Producer
producer.flush()メソッドで全てのメッセージがProducerのqueueに送られるまで
内部でイベントをポーリング(監視)し、対応するコールバック関数(今回だとsend_messages)を呼び出し、作成したBrokerへ向けてメッセージを送ります

```python
from confluent_kafka import Producer
import json
import os

conf = {"bootstrap.servers": os.environ.get("BROKER_URL")}
producer = Producer(conf)


def send_messages(err, msg):
    if err is not None:
        print(f"配信失敗: {err}")
    else:
        print(f"メッセージ配信成功: {msg.value().decode('utf-8')}")


message = {"event": "task_done", "id": 123}
producer.produce(topic="my-topic", value=json.dumps(message), callback=send_messages)
producer.flush()
```

### Consumer
Brokerから受け取ったメッセージを処理します
今回はConsumerがメッセージをポーリング(監視)し、msgを取得できればprintする簡単な処理を記載しています

```python
from confluent_kafka import Consumer
import json
import logging
import os


logging.basicConfig(level=logging.INFO)


conf = {
    "bootstrap.servers": os.environ.get("BROKER_URL"),
    "group.id": os.environ.get("GROUP_ID"),
    "auto.offset.reset": "earliest",
}


def consume_messages():
    consumer = Consumer(conf)
    consumer.subscribe([os.environ.get("TOPIC_NAME")])
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                logging.info("No message")
                continue
            if msg.error():
                print(f"Error while consuming messages: {msg.error()}")
                logging.error(msg.error())
            data = json.loads(msg.value().decode("utf-8"))
            print(f"message: {data}")
            logging.info(data)
    finally:
        consumer.close()
        logging.info("Consumer closed")


def startup():
    logging.info("Starting consumer...")
    consume_messages()


if __name__ == "__main__":
    try:
        startup()
    except Exception as e:
        print(f"Exception occurred: {e}")
```

## 実際に実行してみよう！
### Kafka UIの起動
localhost:8090にアクセスし、以下のようにKafka UIが起動すれば成功です

![スクリーンショット 2025-06-01 14.12.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/251e413b-0054-46da-bed6-cc1e1e004e9e.png)

### Consumerの起動
Brokerへメッセージを送るバッチを実行します
以下のようにメッセージを受信できれば成功です

![スクリーンショット 2025-06-01 15.54.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/74660a6d-dc49-4bfa-bf86-47b4a8818ea5.png)

![スクリーンショット 2025-06-01 15.55.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dd9c57b3-70c0-491e-a10f-092b22277338.png)


### Producerの起動
Brokerからのメッセージを受信するバッチを起動します
以下のようにメッセージを取得できれば成功です

```
INFO:root:Starting consumer...
INFO:root:No message
INFO:root:No message
INFO:root:No message
INFO:root:No message
INFO:root:No message
message: {'event': 'task_done', 'id': 123}
INFO:root:{'event': 'task_done', 'id': 123}
```

## まとめ
簡易的ですがPythonとKafkaを使ったイベント駆動開発を実現できました
実務レベルになるとメッセージのバリデーションをどうするか、DLQの扱いをどうするか、など考慮しないといけない点は多いですが別記事で取り上げたいな、と思いまs

## 参考
https://github.com/confluentinc/confluent-kafka-python

https://docs.confluent.io/kafka-clients/python/current/overview.html#ak-consumer

https://stackoverflow.com/questions/75839415/kafka-fastapi-docker-template

https://docs.confluent.io/kafka-clients/python/current/overview.html#ak-producer

https://zenn.dev/ryoneko/articles/3dee3c716d1cd5

https://qiita.com/Shigai/items/d6752fd6ce034096f112

https://docs.confluent.io/platform/current/installation/docker/config-reference.html#docker-image-configuration-reference-for-cp

https://www.confluent.io/ja-jp/blog/kafka-listeners-explained/
