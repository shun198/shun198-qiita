---
title: Argo Workflowsをkind上で構築しよう！
tags:
  - ArgoCD
  - argoWorkflows
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
Argo WorkflowsはKubernetes上でワークフローを自動で実行・管理するためのツールです
主にバッチ処理やデータパイプライン処理を作成するのに最適です
今回はkindというローカル上でKubernetesを実行できるツールを使ってArgo Workflowsの設定を行います

## 前提
- kubectl, kindをインストール済み


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
今回はversion4.0.6を指定します
kubectl apply時にデフォルトでclient sideからgit上の設定を実行します
ただし、今回のversionのようにリソースが272144byte以上ある場合はserver-sideのオプションを付与してkubectl applyを実行することが公式ドキュメントで推奨されています

> By default, Argo CD executes the kubectl apply operation to apply the configuration stored in Git. This is a client side operation that relies on the kubectl.kubernetes.io/last-applied-configuration annotation to store the previous resource state.
However, there are some cases where you want to use kubectl apply --server-side over kubectl apply:
Resource is too big to fit in 262144 bytes allowed annotation size. In this case server-side apply can be used to avoid this issue as the annotation is not used in this case.

https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/#server-side-apply

```
kubectl apply --server-side -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v4.0.6/install.yaml
customresourcedefinition.apiextensions.k8s.io/clusterworkflowtemplates.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/cronworkflows.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workflowartifactgctasks.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workfloweventbindings.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workflows.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workflowtaskresults.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workflowtasksets.argoproj.io serverside-applied
customresourcedefinition.apiextensions.k8s.io/workflowtemplates.argoproj.io serverside-applied
serviceaccount/argo serverside-applied
serviceaccount/argo-server serverside-applied
role.rbac.authorization.k8s.io/argo-role serverside-applied
clusterrole.rbac.authorization.k8s.io/argo-aggregate-to-admin serverside-applied
clusterrole.rbac.authorization.k8s.io/argo-aggregate-to-edit serverside-applied
clusterrole.rbac.authorization.k8s.io/argo-aggregate-to-view serverside-applied
clusterrole.rbac.authorization.k8s.io/argo-cluster-role serverside-applied
clusterrole.rbac.authorization.k8s.io/argo-server-cluster-role serverside-applied
rolebinding.rbac.authorization.k8s.io/argo-binding serverside-applied
clusterrolebinding.rbac.authorization.k8s.io/argo-binding serverside-applied
clusterrolebinding.rbac.authorization.k8s.io/argo-server-binding serverside-applied
configmap/workflow-controller-configmap serverside-applied
service/argo-server serverside-applied
priorityclass.scheduling.k8s.io/workflow-controller serverside-applied
deployment.apps/argo-server serverside-applied
deployment.apps/workflow-controller serverside-applied
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

```
kubectl create role jenkins --verb=list,update --resource=workflows.argoproj.io
role.rbac.authorization.k8s.io/jenkins created
```

```
kubectl create sa jenkins
serviceaccount/jenkins created
```

```
kubectl create rolebinding jenkins --role=jenkins --serviceaccount=argo:jenkins
rolebinding.rbac.authorization.k8s.io/jenkins created
```

```
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: jenkins.service-account-token
  annotations:
    kubernetes.io/service-account.name: jenkins
type: kubernetes.io/service-account-token
EOF
secret/jenkins.service-account-token created
```

```
ARGO_TOKEN="Bearer $(kubectl get secret jenkins.service-account-token -o=jsonpath='{.data.token}' | base64 --decode)"
❯ echo $ARGO_TOKEN
Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkRHQUxiT1hxUng4WURMSzIyc1R3TXhnQWljaFQzUnZGUEpWZDhJcVhLODAifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImplbmtpbnMuc2VydmljZS1hY2NvdW50LXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImplbmtpbnMiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI0M2Q1Y2MxYy0zYjhlLTQ5Y2YtYmJkMy03MDdlMzUyOTBjMjMiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6ZGVmYXVsdDpqZW5raW5zIn0.kuLy57knivf-sz5l5iegRJy0w8Xk_BWFzR4-f19XPvcW-EMyQv08KFs3WcvEVMwKMN_o-1Lktz3RvE0FEI6oeVN2X5cPY5t0SugVfA8Qy6znyY9t6Y1jkuTZhC4yuvi787y7gxRwq1mUa3X7PtU7rYxzPBx_s0EE6yTVmwy-T2oonFz2LEkVCJG0ztVzMtDCgzguIvFArMK03GwzDPLpc6EJhCYEwEfzFNtjOuLjPSvEDGOSLk4yAzO_zniaqbFV63543Sd2I4uO3ZxezVhJoxSeoo8i1C5xA1TpIdB2ybT9O9Q54mWr5AiNzSo9shyMI3xyh5d_LhwPU074SO0PQQ
```


自分のローカル上でArgo WorkflowsのUIを閲覧できるようport fowardingします
```
kubectl -n "argo" port-forward service/argo-server 2746:2746
Forwarding from 127.0.0.1:2746 -> 2746
Forwarding from [::1]:2746 -> 2746
```

localhost:2746へアクセスすると以下の画面が出ますが、このままlocalhostへアクセスしても問題ないです

![Screenshot 2026-06-21 at 22.20.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e0f6bd91-5eaa-486b-9fac-48bf260c90aa.png)


以下のようにUIを表示できれば成功です



```

```

これでArgo Workflowsの設定は一通り完了です


## 参考
https://argo-workflows.readthedocs.io/en/latest/quick-start/

https://argo-workflows.readthedocs.io/en/latest/argo-server/

https://github.com/argoproj/argo-workflows

https://kind.sigs.k8s.io/
