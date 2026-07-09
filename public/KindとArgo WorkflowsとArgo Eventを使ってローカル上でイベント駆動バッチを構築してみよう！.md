---
title: KindとArgo WorkflowsとArgo Eventを使ってローカル上でイベント駆動バッチを構築してみよう！
tags:
  - 'Kind'
  - 'argoWorkflows'
  - 'ArgoCD'
  - 'Helm'
private: false
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: true
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Pub/SubやKafkaなどのメッセージングサービスからのeventをトリガーにバッチ処理を実行したいケースがあるかと思いますが、Argo WorkflowsとArgo Eventsを使ってイベント駆動バッチを構築できますので解説します

## 前提
下記記事にKindを使ってArgoCDおよびArgo Workflowsの環境構築の方法について記載してますので未実施の方は本記事から読んでおくとスムーズに理解できるかと思います

https://qiita.com/shun198/items/6108f77b0863a8da058d

## Argo Eventsの構成
Argo Eventsは

https://argoproj.github.io/argo-events/concepts/architecture/

### Event Source
https://argoproj.github.io/argo-events/concepts/event_source/

### Sensor
https://argoproj.github.io/argo-events/concepts/sensor/

### Event Bus
https://argoproj.github.io/argo-events/concepts/eventbus/

### Trigger
https://argoproj.github.io/argo-events/concepts/trigger/

## 構成
今回はArgo Workflows + Argo Eventsを使ってワークフローを実行します

```
tree
.
├── README.md
└── argocd
    ├── application.yaml
    ├── Chart.yaml
    ├── templates
    │   ├── events
    │   │   ├── eventbus.yaml
    │   │   ├── eventsource-webhook.yaml
    │   │   ├── rbac-sensor-workflow-trigger.yaml
    │   │   └── sensor-webhook-workflow.yaml
    │   └── workflows
    │       └── webhook-message-template.yaml
    └── values.yaml
```

## Argo Eventsの構築
まず、namespaceを作成します
```
kubectl create namespace argo-events
```

Argo Eventsをinstallします
```
kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml
customresourcedefinition.apiextensions.k8s.io/eventbus.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/eventsources.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/sensors.argoproj.io created
serviceaccount/argo-events-sa created
clusterrole.rbac.authorization.k8s.io/argo-events-aggregate-to-admin created
clusterrole.rbac.authorization.k8s.io/argo-events-aggregate-to-edit created
clusterrole.rbac.authorization.k8s.io/argo-events-aggregate-to-view created
clusterrole.rbac.authorization.k8s.io/argo-events-role created
clusterrolebinding.rbac.authorization.k8s.io/argo-events-binding created
configmap/argo-events-controller-config created
deployment.apps/controller-manager created
```




## 参考
