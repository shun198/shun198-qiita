---
title: ArgoCDをGKEクラスタ上で構築してみよう！
tags:
  - vpc
  - GKE
  - ArgoCD
  - GoogleCloud
private: false
updated_at: '2025-10-13T20:30:57+09:00'
id: 40547ea840c5541a21aa
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Google CloudのGKE(Google Kubernetes Engine)というKubernetesをデプロイできるマネージドサービスを使ってArgoCDを構築する方法について解説します

## 前提
- GKEクラスタ作成時にautopilotとstandardの2種類ありますが、今回はVPCから作成するのでstandardを選択します

## ディレクトリ構成
```
tree
.
└── terraform
    ├── env
    │   └── dev
    │       ├── backend.tf
    │       ├── main.tf
    │       └── variables.tf
    └── modules
        ├── gke
        │   ├── main.tf
        │   └── variables.tf
        └── vpc
            ├── main.tf
            ├── output.tf
            └── variables.tf
```

## VPCの作成
GKEクラスタをVPC上に構築するのでVPCを作成します
ArgoCDのUIにアクセスしたいので今回はパブリックsubnetを作成します

```modules/vpc/main.tf
resource "google_compute_network" "test_vpc" {
  auto_create_subnetworks                   = false
  delete_default_routes_on_create           = false
  description                               = null
  enable_ula_internal_ipv6                  = false
  internal_ipv6_range                       = null
  mtu                                       = 1460
  name                                      = "test-vpc"
  network_firewall_policy_enforcement_order = "AFTER_CLASSIC_FIREWALL"
  project                                   = var.project
  routing_mode                              = "REGIONAL"
}

resource "google_compute_subnetwork" "test_subnet_1" {
  description                      = null
  external_ipv6_prefix             = null
  ip_cidr_range                    = "10.0.0.0/24"
  ipv6_access_type                 = null
  name                             = "test-subnet-1"
  network                          = "https://www.googleapis.com/compute/v1/projects/${var.project}/global/networks/${google_compute_network.test_vpc.name}"
  private_ip_google_access         = true
  private_ipv6_google_access       = "DISABLE_GOOGLE_ACCESS"
  project                          = var.project
  purpose                          = "PRIVATE"
  region                           = var.region
  reserved_internal_range          = null
  role                             = null
  send_secondary_ip_range_if_empty = null
  stack_type                       = "IPV4_ONLY"
}


resource "google_compute_subnetwork" "test_subnet_2" {
  description                      = null
  external_ipv6_prefix             = null
  ip_cidr_range                    = "10.0.1.0/24"
  ipv6_access_type                 = null
  name                             = "test-subnet-2"
  network                          = "https://www.googleapis.com/compute/v1/projects/${var.project}/global/networks/${google_compute_network.test_vpc.name}"
  private_ip_google_access         = true
  private_ipv6_google_access       = "DISABLE_GOOGLE_ACCESS"
  project                          = var.project
  purpose                          = "PRIVATE"
  region                           = var.region
  reserved_internal_range          = null
  role                             = null
  send_secondary_ip_range_if_empty = null
  stack_type                       = "IPV4_ONLY"
}
```

```variables.tf
variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}
```

作成したVPC上にGKEクラスタを立てたいのでGKEのmodule内でVPCとsubnetの名前を使用できるようにしたいのでoutput.tfを作成します

```output.tf
output "vpc_name" {
  value       = google_compute_network.test_vpc.name
  description = "The name of the VPC"
}

output "subnet_1_name" {
  value       = google_compute_subnetwork.test_subnet_1.name
  description = "The name of the subnet 1"
}

output "subnet_2_name" {
  value       = google_compute_subnetwork.test_subnet_2.name
  description = "The name of the subnet 2"
}
```

```
terraform apply
```

実行後、以下のようにVPCとsubnetが作成されたら成功です
![Screenshot 2025-10-13 at 19.15.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d28769d8-7ba6-4a9a-85b0-b8f25fcd90c1.png)

![Screenshot 2025-10-13 at 19.16.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e3e9044d-f5bd-4572-9328-6861061db0f0.png)

## GKE Clusterの作成
GKE Clusterを作成します
今回はmachine_typeなど含めて全てデフォルトの設定にします
Google Cloudの無料枠を使って検証しているので
```
disk_size_gb = 30
```
にします

```modules/gke/main.tf
resource "google_container_cluster" "cluster" {
  name                = "${var.project}-cluster"
  location            = var.region
  project             = var.project
  networking_mode     = "VPC_NATIVE"
  initial_node_count  = 1
  deletion_protection = false
  enable_autopilot    = false
  network             = "projects/${var.project}/global/networks/${var.vpc_name}"
  subnetwork          = "projects/${var.project}/regions/${var.region}/subnetworks/${var.subnet1_name}"
  node_locations      = ["us-central1-a", "us-central1-c", "us-central1-f"]
  node_version        = "1.33.4-gke.1350000"
  min_master_version  = "1.33.4-gke.1350000"
  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    tags         = ["gke-node"]
    disk_size_gb = 30
  }
}
```

```
terraform apply
```

実行後、以下のようにGKEクラスタが作成されたら成功です
![Screenshot 2025-10-13 at 19.26.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0bfce78b-489f-4bcc-a55c-84877ea79272.png)


## ArgoCDの作成
GKEクラスタ作成後、Cloud Shellを開きます
まず、以下のコマンドでclusterに接続します

```
gcloud container clusters get-credentials {cluster-name} --region us-central1 --project {project-name}
```

ArgoCD用のnamespaceを作成します
```
kubectl create namespace argocd
```

公式のArgoCDのmanifestファイルを適用し、ArgoCDを作成します
```
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
customresourcedefinition.apiextensions.k8s.io/applications.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/applicationsets.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/appprojects.argoproj.io created
serviceaccount/argocd-application-controller created
serviceaccount/argocd-applicationset-controller created
serviceaccount/argocd-dex-server created
serviceaccount/argocd-notifications-controller created
serviceaccount/argocd-redis created
serviceaccount/argocd-repo-server created
serviceaccount/argocd-server created
role.rbac.authorization.k8s.io/argocd-application-controller created
role.rbac.authorization.k8s.io/argocd-applicationset-controller created
role.rbac.authorization.k8s.io/argocd-dex-server created
role.rbac.authorization.k8s.io/argocd-notifications-controller created
role.rbac.authorization.k8s.io/argocd-redis created
role.rbac.authorization.k8s.io/argocd-server created
clusterrole.rbac.authorization.k8s.io/argocd-application-controller created
clusterrole.rbac.authorization.k8s.io/argocd-applicationset-controller created
clusterrole.rbac.authorization.k8s.io/argocd-server created
rolebinding.rbac.authorization.k8s.io/argocd-application-controller created
rolebinding.rbac.authorization.k8s.io/argocd-applicationset-controller created
rolebinding.rbac.authorization.k8s.io/argocd-dex-server created
rolebinding.rbac.authorization.k8s.io/argocd-notifications-controller created
rolebinding.rbac.authorization.k8s.io/argocd-redis created
rolebinding.rbac.authorization.k8s.io/argocd-server created
clusterrolebinding.rbac.authorization.k8s.io/argocd-application-controller created
clusterrolebinding.rbac.authorization.k8s.io/argocd-applicationset-controller created
clusterrolebinding.rbac.authorization.k8s.io/argocd-server created
configmap/argocd-cm created
configmap/argocd-cmd-params-cm created
configmap/argocd-gpg-keys-cm created
configmap/argocd-notifications-cm created
configmap/argocd-rbac-cm created
configmap/argocd-ssh-known-hosts-cm created
configmap/argocd-tls-certs-cm created
secret/argocd-notifications-secret created
secret/argocd-secret created
service/argocd-applicationset-controller created
service/argocd-dex-server created
service/argocd-metrics created
service/argocd-notifications-controller-metrics created
service/argocd-redis created
service/argocd-repo-server created
service/argocd-server created
service/argocd-server-metrics created
deployment.apps/argocd-applicationset-controller created
deployment.apps/argocd-dex-server created
deployment.apps/argocd-notifications-controller created
deployment.apps/argocd-redis created
deployment.apps/argocd-repo-server created
deployment.apps/argocd-server created
statefulset.apps/argocd-application-controller created
networkpolicy.networking.k8s.io/argocd-application-controller-network-policy created
networkpolicy.networking.k8s.io/argocd-applicationset-controller-network-policy created
networkpolicy.networking.k8s.io/argocd-dex-server-network-policy created
networkpolicy.networking.k8s.io/argocd-notifications-controller-network-policy created
networkpolicy.networking.k8s.io/argocd-redis-network-policy created
networkpolicy.networking.k8s.io/argocd-repo-server-network-policy created
networkpolicy.networking.k8s.io/argocd-server-network-policy created
```

argocdのnamespace内にpod, deployment, serviceが作成されていることが確認できます
```
kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS      AGE
argocd-application-controller-0                     1/1     Running   0             110s
argocd-applicationset-controller-578697b885-xqqqv   1/1     Running   0             113s
argocd-dex-server-95477cdd-crml4                    1/1     Running   2 (89s ago)   113s
argocd-notifications-controller-787447c77d-6bpft    1/1     Running   0             112s
argocd-redis-5746c4c5fb-m4bqx                       1/1     Running   0             112s
argocd-repo-server-588c6f4648-4vxgf                 1/1     Running   0             111s
argocd-server-656b9b6c6c-jsdst                      1/1     Running   0             110s
```

```
kubectl get deployments -n argocd
NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
argocd-applicationset-controller   1/1     1            1           2m56s
argocd-dex-server                  1/1     1            1           2m55s
argocd-notifications-controller    1/1     1            1           2m54s
argocd-redis                       1/1     1            1           2m54s
argocd-repo-server                 1/1     1            1           2m53s
argocd-server                      1/1     1            1           2m53s
```

```
kubectl get svc -n argocd
NAME                                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
argocd-applicationset-controller          ClusterIP   34.118.226.175   <none>        7000/TCP,8080/TCP            3m17s
argocd-dex-server                         ClusterIP   34.118.229.154   <none>        5556/TCP,5557/TCP,5558/TCP   3m16s
argocd-metrics                            ClusterIP   34.118.235.61    <none>        8082/TCP                     3m15s
argocd-notifications-controller-metrics   ClusterIP   34.118.227.206   <none>        9001/TCP                     3m15s
argocd-redis                              ClusterIP   34.118.231.50    <none>        6379/TCP                     3m14s
argocd-repo-server                        ClusterIP   34.118.229.15    <none>        8081/TCP,8084/TCP            3m14s
argocd-server                             ClusterIP   34.118.234.213   <none>        80/TCP,443/TCP               3m13s
argocd-server-metrics                     ClusterIP   34.118.234.132   <none>        8083/TCP                     3m12s
```

LoadBalancerを作成します
以下のコマンドでArgoCDのserviceを修正します
```
kubectl edit svc argocd-server -n argocd
```
上記のコマンド実行後、以下のようにserviceのmanifestファイルが表示されます

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: v1
kind: Service
metadata:
  annotations:
    cloud.google.com/neg: '{"ingress":true}'
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"labels":{"app.kubernetes.io/component":"server","app.kubernetes.io/name":"argocd-server","app.kubernetes.io/part-of":"argocd"},"name":"argocd-server","namespace":"argocd"},"spec":{"ports":[{"name":"http","port":80,"protocol":"TCP","targetPort":8080},{"name":"https","port":443,"protocol":"TCP","targetPort":8080}],"selector":{"app.kubernetes.io/name":"argocd-server"}}}
  creationTimestamp: "2025-10-13T07:57:03Z"
  labels:
    app.kubernetes.io/component: server
    app.kubernetes.io/name: argocd-server
    app.kubernetes.io/part-of: argocd
  name: argocd-server
  namespace: argocd
  resourceVersion: "1760342223637167018"
  uid: c9db5621-4407-4e8d-889c-a5ce92affd50
spec:
  clusterIP: 34.118.234.213
  clusterIPs:
  - 34.118.234.213
  internalTrafficPolicy: Cluster
  ipFamilies:
  - IPv4
  ipFamilyPolicy: SingleStack
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 8080
  - name: https
    port: 443
    protocol: TCP
    targetPort: 8080
  selector:
    app.kubernetes.io/name: argocd-server
  sessionAffinity: None
  type: ClusterIP
status:
  loadBalancer: {}
```

type: LoadBalancerに変更します

```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: v1
kind: Service
metadata:
  annotations:
    cloud.google.com/neg: '{"ingress":true}'
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"v1","kind":"Service","metadata":{"annotations":{},"labels":{"app.kubernetes.io/component":"server","app.kubernetes.io/name":"argocd-server","app.kubernetes.io/part-of":"argocd"},"name":"argocd-server","namespace":"argocd"},"spec":{"ports":[{"name":"http","port":80,"protocol":"TCP","targetPort":8080},{"name":"https","port":443,"protocol":"TCP","targetPort":8080}],"selector":{"app.kubernetes.io/name":"argocd-server"}}}
  creationTimestamp: "2025-10-13T07:57:03Z"
  labels:
    app.kubernetes.io/component: server
    app.kubernetes.io/name: argocd-server
    app.kubernetes.io/part-of: argocd
  name: argocd-server
  namespace: argocd
  resourceVersion: "1760342223637167018"
  uid: c9db5621-4407-4e8d-889c-a5ce92affd50
spec:
  clusterIP: 34.118.234.213
  clusterIPs:
  - 34.118.234.213
  internalTrafficPolicy: Cluster
  ipFamilies:
  - IPv4
  ipFamilyPolicy: SingleStack
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 8080
  - name: https
    port: 443
    protocol: TCP
    targetPort: 8080
  selector:
    app.kubernetes.io/name: argocd-server
  sessionAffinity: None
  type: LoadBalancer
status:
  loadBalancer: {}
```

以下のようにargocd-serverのtypeがLoad Balancerに変更され、Load Balancerが作成されたら成功です
```
kubectl get svc -n argocd
NAME                                      TYPE           CLUSTER-IP       EXTERNAL-IP      PORT(S)                      AGE
argocd-applicationset-controller          ClusterIP      34.118.226.175   <none>           7000/TCP,8080/TCP            12m
argocd-dex-server                         ClusterIP      34.118.229.154   <none>           5556/TCP,5557/TCP,5558/TCP   12m
argocd-metrics                            ClusterIP      34.118.235.61    <none>           8082/TCP                     12m
argocd-notifications-controller-metrics   ClusterIP      34.118.227.206   <none>           9001/TCP                     12m
argocd-redis                              ClusterIP      34.118.231.50    <none>           6379/TCP                     12m
argocd-repo-server                        ClusterIP      34.118.229.15    <none>           8081/TCP,8084/TCP            12m
argocd-server                             LoadBalancer   34.118.234.213   136.114.115.93   80:31906/TCP,443:31689/TCP   12m
argocd-server-metrics                     ClusterIP      34.118.234.132   <none>           8083/TCP                     12m
```

![Screenshot 2025-10-13 at 19.40.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c3042f4c-bcaf-490a-83a8-2e42d459c094.png)


## ArgoCDへアクセス
```
kubectl get svc -n argocd
```
で表示されたグローバルIPへアクセスします
以下のwarningが出ますが気にせずAdvancedを開きます

![Screenshot 2025-10-13 at 17.10.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f36d38fb-4a94-4e3f-b32a-99c992ba6f70.png)

その後、Proceed to IP(unsafe)をクリックします
![Screenshot 2025-10-13 at 17.11.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4c683621-1aba-4b87-b44e-7c59b9cd5496.png)

以下のようにArgoCDのログイン画面が表示されたら成功です
![Screenshot 2025-10-13 at 17.12.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/728152de-addd-4a7b-9439-90712a7bce1c.png)

ログイン時のAdminのパスワードを取得します
argocd-initial-admin-secretからパスワードを取得できます

```
kubectl get secrets -n argocd
NAME                          TYPE     DATA   AGE
argocd-initial-admin-secret   Opaque   1      15m
argocd-notifications-secret   Opaque   0      15m
argocd-redis                  Opaque   1      15m
argocd-secret                 Opaque   5      15m
```

```
kubectl get secret/argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d; echo
kzVyuVeVmWgqy1Ii
```

![Screenshot 2025-10-13 at 17.18.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/87a38aae-5d0b-4d4f-b192-ab449ad92acd.png)

## 試しにApplicatiionをデプロイしてみよう！
ApplicationsからNEW APPを押します
Application Nameをguestbook, Project Nameをdefaultにします

![Screenshot 2025-10-13 at 19.58.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c37dda86-8f79-4c3e-bc7b-0c41f5ecf77c.png)

Repository URLをhttps://github.com/argoproj/argocd-example-apps/tree/master/helm-guestbook, RevisionをHEAD, Pathをhelm-guestbookにします

![Screenshot 2025-10-13 at 19.59.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/972b29f7-03e9-4e49-90c9-326b92c2ff8c.png)

helm-guestbookのテンプレートの詳細は以下の通りです

https://github.com/argoproj/argocd-example-apps/tree/master/helm-guestbook

Cluster URLをhttps://kubernetes.default.svc, Namespaceをdefaultにします
![Screenshot 2025-10-13 at 20.03.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2a6c77e3-f0ad-49ab-9ebb-af0ade1b1e54.png)

values filesにvalue.yamlを指定します
![Screenshot 2025-10-13 at 20.03.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7bf62d73-b59f-443b-8b82-5a46a8fa3395.png)

以下のようにguestbookのApplicationが作成されたら成功です
![Screenshot 2025-10-13 at 20.03.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cf71b3a5-60c5-4209-8c1b-a62963299737.png)

![Screenshot 2025-10-13 at 20.12.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/18728f66-3c8d-470d-89d4-4ecb2317a63d.png)

## guestbookにアクセスできるようにするには
以下のようにguestbook-helm-guestbookのserviceがあることが確認できます
EXTERNAL-IPがないのでLoadBalancerを作成してGlobalLPを割り振ってみましょう

```
kubectl get service -n default                                                                                
NAME                       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
guestbook-helm-guestbook   ClusterIP   34.118.238.123   <none>        80/TCP    2m58s
kubernetes                 ClusterIP   34.118.224.1     <none>        443/TCP   44m
```

```
kubectl edit svc guestbook-helm-guestbook -n default
```
でmanifestファイルを編集します
下記のようにtype: LoadBalancerに変更します

```yaml
apiVersion: v1
kind: Service
metadata:
  annotations:
    argocd.argoproj.io/tracking-id: guestbook:/Service:default/guestbook-helm-guestbook
    cloud.google.com/neg: '{"ingress":true}'
    kubectl.kubernetes.io/last-applied-configuration: |
  creationTimestamp: "2025-10-13T11:04:10Z"
  finalizers:
  - gke.networking.io/l4-netlb-v1
  - service.kubernetes.io/load-balancer-cleanup
  labels:
    app: helm-guestbook
    chart: helm-guestbook-0.1.0
    heritage: Helm
    release: guestbook
  name: guestbook-helm-guestbook
  namespace: default
  resourceVersion: "1760353863448527001"
  uid: ed7fab8b-f053-4e31-baab-a929999f5dc2
spec:
  allocateLoadBalancerNodePorts: true
  clusterIP: 34.118.238.123
  clusterIPs:
  - 34.118.238.123
  externalTrafficPolicy: Cluster
  internalTrafficPolicy: Cluster
  ipFamilies:
  - IPv4
  ipFamilyPolicy: SingleStack
  ports:
  - name: http
    nodePort: 32290
    port: 80
    protocol: TCP
    targetPort: http
  selector:
    app: helm-guestbook
    release: guestbook
  sessionAffinity: None
  type: LoadBalancer
status:
  loadBalancer:
    ingress:
    - ip: 35.202.55.120
      ipMode: VIP
```

```以下のようにEXTERNAL-IPが割り振られていたら成功です
kubectl get service -n default
NAME                       TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)        AGE
guestbook-helm-guestbook   LoadBalancer   34.118.238.123   35.202.55.120   80:32290/TCP   8m49s
kubernetes                 ClusterIP      34.118.224.1     <none>          443/TCP        50m
```

`http://{EXTERNAL-IP}:80`にアクセスし、以下のようにguestbookのUIが表示されたら成功です

![Screenshot 2025-10-13 at 20.17.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bdfe22f2-d2ca-481b-92af-49faee41def5.png)

## 参考
https://argo-cd.readthedocs.io/en/stable/getting_started/

https://zenn.dev/cloud_ace/articles/argocd_on_gke

https://medium.com/@vijaygiduthuri67/-48ed2211262b

https://cloud.google.com/kubernetes-engine/docs/learn

https://cloud.google.com/kubernetes-engine/docs/terraform
