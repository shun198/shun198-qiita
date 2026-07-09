---
title: Argo WorkflowsとArgo EventとKindを使ってローカル上でイベント駆動バッチを構築してみよう！
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
Argo Eventsは主に
- Event Source
- Sensor
- Event Bus
- Trigger

の4つで構成されています

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

## ArgoCDの構築
```yaml:argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: argo-workflows-practice
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/shun198/argo-workflows-practice.git
    targetRevision: HEAD
    path: kubernetes
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: argo
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Argo Eventsの構築
### Event Busの構築

```yaml:kubernetes/templates/events/eventbus.yaml
apiVersion: argoproj.io/v1alpha1
kind: EventBus
metadata:
  name: default
  namespace: argo-events
spec:
  nats:
    native:
      replicas: 1

```

### Event Sourceの構築
```yaml:kubernetes/templates/events/eventsource-webhook.yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: webhook
  namespace: argo-events
spec:
  service:
    ports:
      - port: 12000
        targetPort: 12000
  webhook:
    example:
      endpoint: /hook
      method: POST
      port: "12000"
```

### RBACの設定
```yaml:kubernetes/templates/events/rbac-sensor-workflow-trigger.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sensor-workflow-trigger-sa
  namespace: argo-events
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: sensor-workflow-trigger-role
  namespace: argo
rules:
  - apiGroups: ["argoproj.io"]
    resources: ["workflows"]
    verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: sensor-workflow-trigger-rb
  namespace: argo
subjects:
  - kind: ServiceAccount
    name: sensor-workflow-trigger-sa
    namespace: argo-events
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: sensor-workflow-trigger-role
```

### Sensorの構築
```yaml:kubernetes/templates/events/sensor-webhook-workflow.yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: webhook-workflow-sensor
  namespace: argo-events
spec:
  eventBusName: default
  template:
    serviceAccountName: sensor-workflow-trigger-sa
  dependencies:
    - name: webhook-dep
      eventSourceName: webhook
      eventName: example
  triggers:
    - template:
        name: webhook-workflow-trigger
        k8s:
          operation: create
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: webhook-event-
                namespace: argo
              spec:
                workflowTemplateRef:
                  name: webhook-message-template
                arguments:
                  parameters:
                    - name: message
                      value: "fallback message"
          parameters:
            - src:
                dependencyName: webhook-dep
                dataKey: body.message
              dest: spec.arguments.parameters.0.value
```

### Eventをトリガーに実行するArgo Workflowsの構築
```yaml:kubernetes/templates/workflows/webhook-message-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: webhook-message-template
  namespace: argo
spec:
  entrypoint: main
  arguments:
    parameters:
      - name: message
        value: "hello from argo events"
  templates:
    - name: main
      inputs:
        parameters:
          - name: message
      container:
        image: alpine:3.20
        command: [sh, -c]
        args:
          - |
            echo "received message: '{{ "{{inputs.parameters.message}}" }}'"
            date
```

## 実際に検証してみよう

## 参考
https://argoproj.github.io/argo-events/concepts/architecture/

https://argoproj.github.io/argo-events/concepts/event_source/

https://argoproj.github.io/argo-events/concepts/sensor/

https://argoproj.github.io/argo-events/concepts/eventbus/

https://argoproj.github.io/argo-events/concepts/trigger/
