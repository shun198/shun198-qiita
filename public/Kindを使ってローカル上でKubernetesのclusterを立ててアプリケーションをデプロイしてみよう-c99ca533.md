---
title: Kindを使ってローカル上でKubernetesのclusterを立ててアプリケーションをデプロイしてみよう！
tags:
  - dockerfile
  - kubernetes
  - Kind
private: false
updated_at: '2025-09-13T16:03:53+09:00'
id: c99ca533fb2d4a408cb3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Kubernetesをローカル上で検証する際にKindもしくはminikubeを使うのが一般的です
今回はKindを使ってローカル上にclusterを立てて、FastAPIのアプリケーションがpod内で起動するところまで検証していきたいと思います

## ディレクトリ構成
```
❯ tree
.
├── application
│   ├── main.py
│   ├── pyproject.toml
│   └── uv.lock
├── containers
│   └── fastapi
│       └── Dockerfile
├── kubernetes
│   └── templates
│       └── api
│           ├── deployment.yaml
│           └── service.yaml
└── README.md
```

## 実装
### Dockerfileの作成

```Dockerfile:Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY application/pyproject.toml /code/
RUN uv sync
COPY application /code/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

### deployment.yamlの作成
deployment.yamlにPodの作成・管理・更新に関する設定を記載します
Pod名は fastapi-deployment、ラベルは app: fastapi に設定しています
コンテナポートはDockerfileに合わせて 8000 を指定しています

```yaml:deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-deployment
  labels:
    app: fastapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
        - name: fastapi
          image: kubernetes-fastapi-app:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          env:
            - name: SECRET_KEY
              value: 'test'
            - name: ALGORITHM
              value: 'HS256'
            - name: SQLALCHEMY_DATABASE_URL
              value: 'postgresql://postgres:postgres@db:5432/postgres'
            - name: SENDGRID_API_KEY
              value: 'test'
            - name: COOKIE_SAME_SITE
              value: 'Lax'
```

### service.yamlの作成
service.yamlにpodへアクセスする設定について記載します
ローカル上で検証するのでNodePortを使用します
NodePortは 30000 に設定し、Deploymentのポート 8000 に対応させます

```yaml:service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  ports:
    - name: http
      port: 8000
      protocol: TCP
      targetPort: 8000
      nodePort: 30000
  # どのpodにトラフィックを送るかを決定するためのラベルセレクター
  selector:
    app: fastapi
  type: NodePort
```

## アプリケーションのデプロイ
### クラスタの作成
以下のようにローカル上にクラスタを作成します

```
kind create cluster --name kind
Creating cluster "kind" ...
 ✓ Ensuring node image (kindest/node:v1.33.1) 🖼 
 ✓ Preparing nodes 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
Set kubectl context to "kind-kind"
You can now use your cluster with:

kubectl cluster-info --context kind-kind

Not sure what to do next? 😅  Check out https://kind.sigs.k8s.io/docs/user/quick-start/
❯ kubectl cluster-info --context kind-kind
Kubernetes control plane is running at https://127.0.0.1:64024
CoreDNS is running at https://127.0.0.1:64024/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

### imageのbuild
imageをbuildし、タグ付けします
```
docker build -f ./containers/fastapi/Dockerfile -t kubernetes-fastapi-app:latest .
```

### kindへロード
Kind上でアプリケーションをデプロイできるよう、imageをあらかじめアップロードします
```
kind load docker-image kubernetes-fastapi-app:latest --name kind
```

### deploymentの適用
deploymentを適用し、以下のようにpodが起動していれば成功です
```
kubectl apply -f ./kubernetes/templates/api/deployment.yaml
deployment.apps/fastapi-deployment created
```

```
kubectl get pods
NAME                                  READY   STATUS    RESTARTS   AGE
fastapi-deployment-6b58989887-74kzn   1/1     Running   0          40s
fastapi-deployment-6b58989887-hctdh   1/1     Running   0          40s
fastapi-deployment-6b58989887-whqpn   1/1     Running   0          40s
```

ログからuvicornが起動し、8000番ポートにlistenしていることも確認できました
```
kubectl logs fastapi-deployment-6b58989887-74kzn
Downloading greenlet (1.1MiB)
Downloading pygments (1.2MiB)
Downloading botocore (12.9MiB)
Downloading cryptography (4.1MiB)
Downloading ruff (11.0MiB)
Downloading sqlalchemy (3.1MiB)
 Downloading greenlet
 Downloading pygments
 Downloading sqlalchemy
 Downloading cryptography
 Downloading ruff
 Downloading botocore
Uninstalled 84 packages in 5.15s
Installed 42 packages in 221ms
INFO:     Will watch for changes in these directories: ['/code']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [83] using StatReload
```

### serviceの適用
以下のようにserviceを適用し、NodePortの設定が有効化されていたら成功です
```
kubectl apply -f ./kubernetes/templates/api/service.yaml
```

```
kubectl get svc
NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
fastapi-service   NodePort    10.96.156.213   <none>        8000:30000/TCP   7m59s
kubernetes        ClusterIP   10.96.0.1       <none>        443/TCP          12m
```

## 実際にアクセスしてみよう！
以下のようにローカルの8000番ポートをserviceの8000番ポートにポートフォワーディングし、ブラウザ上で127.0.0.1:8000/docsにアクセスできれば成功です
```
kubectl port-forward svc/fastapi-service 8000:8000
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
Handling connection for 8000
```

![Screenshot 2025-09-13 at 14.48.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1916455d-eeb6-41f5-9c4e-dbcc36084b82.png)

## 参考
https://kind.sigs.k8s.io/

https://santiagoalvarez87.medium.com/deploying-a-fastapi-application-on-a-local-cluster-of-kubernetes-368232690292

https://zenn.dev/akasan/articles/1633f745945c56
