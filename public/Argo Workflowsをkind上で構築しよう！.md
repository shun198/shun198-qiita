---
title: Argo Workflowsをkind上で構築しよう！
tags:
  - Kind
  - ArgoCD
  - argoWorkflows
private: false
updated_at: '2026-07-09T09:53:26+09:00'
id: 6108f77b0863a8da058d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Argo WorkflowsはKubernetes上でワークフローを自動で実行・管理するためのツールです
主にバッチ処理やデータパイプライン処理を作成するのに最適です
今回はkindというローカル上でKubernetesを実行できるツールを使ってArgo Workflowsの設定を行います

## 前提
- kubectl, kindをインストール済み
- ArgoCD v2.12.1を使用
- Argo Workflows v3.7.10を使用

## Argo Workflowsの設定
Argo Workflowsが実行できるクラスタをkindを使って作成します

```kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
```

下記のコマンドを実行し、クラスタが作成されたら成功です
```
kind create cluster --name "argo-local" --config "kind-config.yaml"
Creating cluster "argo-local" ...
 ✓ Ensuring node image (kindest/node:v1.36.1) 🖼
 ✓ Preparing nodes 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
Set kubectl context to "kind-argo-local"
You can now use your cluster with:

kubectl cluster-info --context kind-argo-local

Have a nice day! 👋
```

argoというnamespaceを作成します

```
kubectl create namespace "argo"
namespace/argo created
```

その後、Argo Workflowsをinstallします

```
kubectl apply --server-side -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.7.10/install.yaml
customresourcedefinition.apiextensions.k8s.io/applications.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/applicationsets.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/appprojects.argoproj.io serverside-applied
serviceaccount/argocd-application-controller serverside-applied
serviceaccount/argocd-applicationset-controller serverside-applied
serviceaccount/argocd-dex-server serverside-applied
serviceaccount/argocd-notifications-controller serverside-applied
serviceaccount/argocd-redis serverside-applied
serviceaccount/argocd-repo-server serverside-applied
serviceaccount/argocd-server serverside-applied
role.rbac.authorization.k8s.io/argocd-application-controller serverside-applied
role.rbac.authorization.k8s.io/argocd-applicationset-controller serverside-applied
role.rbac.authorization.k8s.io/argocd-dex-server serverside-applied
role.rbac.authorization.k8s.io/argocd-notifications-controller serverside-applied
role.rbac.authorization.k8s.io/argocd-redis serverside-applied
role.rbac.authorization.k8s.io/argocd-server serverside-applied
clusterrole.rbac.authorization.k8s.io/argocd-application-controller serverside-applied
clusterrole.rbac.authorization.k8s.io/argocd-applicationset-controller serverside-applied
clusterrole.rbac.authorization.k8s.io/argocd-server serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-application-controller serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-applicationset-controller serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-dex-server serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-notifications-controller serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-redis serverside-applied
rolebinding.rbac.authorization.k8s.io/argocd-server serverside-applied
clusterrolebinding.rbac.authorization.k8s.io/argocd-application-controller serverside-applied
clusterrolebinding.rbac.authorization.k8s.io/argocd-applicationset-controller serverside-applied
clusterrolebinding.rbac.authorization.k8s.io/argocd-server serverside-applied
configmap/argocd-cm serverside-applied
configmap/argocd-cmd-params-cm serverside-applied
configmap/argocd-gpg-keys-cm serverside-applied
configmap/argocd-notifications-cm serverside-applied
configmap/argocd-rbac-cm serverside-applied
configmap/argocd-ssh-known-hosts-cm serverside-applied
configmap/argocd-tls-certs-cm serverside-applied
secret/argocd-notifications-secret serverside-applied
secret/argocd-secret serverside-applied
service/argocd-applicationset-controller serverside-applied
service/argocd-dex-server serverside-applied
service/argocd-metrics serverside-applied
service/argocd-notifications-controller-metrics serverside-applied
service/argocd-redis serverside-applied
service/argocd-repo-server serverside-applied
service/argocd-server serverside-applied
service/argocd-server-metrics serverside-applied
deployment.apps/argocd-applicationset-controller serverside-applied
deployment.apps/argocd-dex-server serverside-applied
deployment.apps/argocd-notifications-controller serverside-applied
deployment.apps/argocd-redis serverside-applied
deployment.apps/argocd-repo-server serverside-applied
deployment.apps/argocd-server serverside-applied
statefulset.apps/argocd-application-controller serverside-applied
networkpolicy.networking.k8s.io/argocd-application-controller-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-applicationset-controller-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-dex-server-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-notifications-controller-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-redis-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-repo-server-network-policy serverside-applied
networkpolicy.networking.k8s.io/argocd-server-network-policy serverside-applied
```

これでArgo Workflowsのインストールが完了しました
続いてはコンソール上で実行させるサンプルワークフローを作成します

下記が通常のワークフローです
generateNameにワークフロー名を指定します

```yaml:hello-world.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hello-world-
spec:
  entrypoint: main
  templates:
    - name: main
      container:
        image: alpine:3.20
        command: [sh, -c]
        args: ["echo 'hello from argo workflows' && date"]
```

https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/#workflow-spec

下記のようにワークフローを作成できれば成功です

```
kubectl create -n "argo" -f hello-world.yaml
workflow.argoproj.io/hello-world-xslvh created
```

下記がCronWorkflowです
通常のWorkflowと違ってschedulesにcronを設定することができます
concurrencyPolicyで複数のワークフロー実行時の挙動を以下のように設定ができます
- Allow: 全て許可する
- Replace: 新しいワークフローを実行する前に古いワークフローを全て削除する
- Forbid: 古いワークフローの実行中は新しいワークフローの実行を許可しない

successfulJobsHistoryLimitが永続化するワークフローの成功件数、failedJobsHistoryLimitが永続化するワークフローの失敗件数です

```yaml:cron-hello-world.yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: cron-hello-world
spec:
  schedules:
    - "*/5 * * * *"
  timezone: "Asia/Tokyo"
  concurrencyPolicy: "Forbid"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  workflowSpec:
    entrypoint: main
    templates:
      - name: main
        container:
          image: alpine:3.20
          command: [sh, -c]
          args: ["echo 'hello from cron workflow' && date"]

```

https://argo-workflows.readthedocs.io/en/latest/cron-workflows/#cron-workflows

下記のようにワークフローを作成できれば成功です

```
kubectl create -n "argo" -f cron-hello-world.yaml
cronworkflow.argoproj.io/cron-hello-world created
```

UIへログインできるトークンを作成します
```
kubectl -n ${ARGOCD_NAMESPACE} get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 --decode; echo
```

https://argo-workflows.readthedocs.io/en/latest/access-token/#token-creation

自分のローカル上でArgo WorkflowsのUIを閲覧できるようport fowardingします
```
kubectl -n "argo" port-forward service/argo-server 2746:2746
Forwarding from 127.0.0.1:2746 -> 2746
Forwarding from [::1]:2746 -> 2746
```

localhost:2746へアクセスすると以下の画面が出ますが、このままlocalhostへアクセスしても問題ないです

![Screenshot 2026-06-21 at 22.20.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e0f6bd91-5eaa-486b-9fac-48bf260c90aa.png)

UIへアクセスし、
```
If your organisation has configured client authentication,
get your token following this instructions from here and
paste in this box:
```
の箇所に先ほど作成したトークンを入力します

以下のようにUIを表示できれば成功です
これでArgo Workflowsの設定は一通り完了です


![Screenshot 2026-07-09 at 9.49.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6d5a4f29-4ac2-470b-9374-ca923e817e8b.png)

![Screenshot 2026-07-09 at 9.47.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/27fbb427-93dd-4c17-8e3b-b4b385f1c9e2.png)

![Screenshot 2026-07-09 at 9.48.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d060e9f9-3149-474e-ac40-b7e10f8577be.png)

![Screenshot 2026-07-09 at 9.48.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3f96b0f8-777a-4b8c-b171-be2146f75ebc.png)

## Cron Workflowsを構築するには
こちらも同様に以下のworkflowsをkubectlコマンドで展開します

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: cron-hello-world
spec:
  schedules:
    - "*/5 * * * *"
  timezone: "Asia/Tokyo"
  concurrencyPolicy: "Forbid"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  workflowSpec:
    entrypoint: main
    templates:
      - name: main
        container:
          image: alpine:3.20
          command: [sh, -c]
          args: ["echo 'hello from cron workflow' && date"]
```

```
kubectl create -n argo -f workflows/cron-hello-world.yaml
cronworkflow.argoproj.io/cron-hello-world created
```

以下のようにWorkflowsがcronのschedule通りに実行できれば成功です

![Screenshot 2026-07-09 at 13.41.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/660b9324-f2ad-4db0-a8f8-a22dbb4de8eb.png)

## 参考
https://argo-workflows.readthedocs.io/en/latest/quick-start/

https://argo-workflows.readthedocs.io/en/latest/argo-server/

https://argo-workflows.readthedocs.io/en/latest/cron-workflows/

https://github.com/argoproj/argo-workflows

https://kind.sigs.k8s.io/
