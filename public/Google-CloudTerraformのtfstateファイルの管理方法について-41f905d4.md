---
title: '[Google Cloud]Terraformのtfstateファイルの管理方法について'
tags:
  - GCS
  - Terraform
  - tfstate
  - GoogleCloud
private: false
updated_at: '2025-09-15T11:27:28+09:00'
id: 41f905d40aab2ec8ea1e
organization_url_name: null
slide: false
---
## 概要
複数人でTerraformを使ってGoogle Cloudを操作する際はtfstateファイルをGoogle Cloud Storage上で管理して競合を防ぐ必要があります
今回はtfstateファイルの管理方法について解説します

## 前提
- Google Cloud cliをインストール済み
    - [gcloud CLI をインストールする](https://cloud.google.com/sdk/docs/install?hl=ja)
- Terraformをインストール済み
    - [Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- Google Cloudのアカウントを作成済み

## Google Cloud cliの設定
まず、gcloud authコマンドで自身のアカウントと認証します

```
gcloud auth application-default login
```

使用するプロジェクトを指定します
```
gcloud config set project <プロジェクト名>
```

以下のようにprojectの箇所に設定できていれば成功です
```
gcloud config list
[core]
account = <アカウント名>
disable_usage_reporting = False
project = <プロジェクト名>

Your active configuration is: [default]
```

## Terraformの設定
以下のファイルが必要です
backend.tfはStorageを作成してから設定するので後ほど解説します

```
tree
.
├── backend.tf
├── main.tf
└── variables.tf
```

### variables.tf
変数の設定を行います
今回は
- プロジェクト名
- 環境(dev,stg,prdなど)
- リージョン

を設定します

```variables.tf
variable "project" {
  type = string
}

variable "env" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

```

### main.tf
main.tfで
- Terraformのバージョン
- 使用するクラウドプロバイダ(今回はGoogle Cloud)
- 使用するプロジェクト名とリージョン

の設定を行います

```main.tf
terraform {
  required_version = ">= 1.11.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

```

### storage.tf
tfstateファイルを格納するGoogle Cloud Storageを作成します
以下の設定を行います
- パブリックアクセスの無効化
- Cloud Storageリソースへのアクセスを均一に管理するか
    - Trueにするのが推奨されている
    - Cloud Storage リソースへのアクセス権の付与方法が統一され、簡素化される
    - ACLによる意図しないデータ漏洩を防ぐことができる

![Screenshot 2025-09-15 at 11.25.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2b6fc215-e544-4652-8d2b-9266689a1c97.png)

![Screenshot 2025-09-15 at 11.26.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/85323593-464e-4037-9f88-c456b978b74b.png)

## Terraformの初期化
以下のコマンドでterraformの初期化を行います
以下のように表示されたら成功です

```
terraform init
Initializing the backend...

Successfully configured the backend "gcs"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing provider plugins...
- Finding hashicorp/google versions matching "6.8.0"...
- Installing hashicorp/google v6.8.0...
- Installed hashicorp/google v6.8.0 (signed by HashiCorp)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```


## tfstateを格納するバケットの作成
バケットを作成します
変数を使用してるのでplanと後ほど記載するapplyで変数を入力していきます
以下のようにバケットの設定等が記載されていたら成功です

```
terraform plan
var.env
  Enter a value: 

var.project
  Enter a value: 


Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following
symbols:
  + create

Terraform will perform the following actions:

  # google_storage_bucket.tfstate will be created
  + resource "google_storage_bucket" "tfstate" {
      + effective_labels            = {
          + "goog-terraform-provisioned" = "true"
        }
      + force_destroy               = false
      + id                          = (known after apply)
      + location                    = "US-CENTRAL1"
      + name                        = 
      + project                     = (known after apply)
      + project_number              = (known after apply)
      + public_access_prevention    = "enforced"
      + rpo                         = (known after apply)
      + self_link                   = (known after apply)
      + storage_class               = "STANDARD"
      + terraform_labels            = {
          + "goog-terraform-provisioned" = "true"
        }
      + uniform_bucket_level_access = true
      + url                         = (known after apply)

      + soft_delete_policy (known after apply)

      + versioning {
          + enabled = true
        }

      + website (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform
apply" now.
```

terraform applyで実際にGoogle Cloud上でデプロイしていきます
Apply complete!と表示されたら成功です

```
terraform apply
var.env
  Enter a value: 

var.project
  Enter a value: 


Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following
symbols:
  + create

Terraform will perform the following actions:

  # google_storage_bucket.tfstate will be created
  + resource "google_storage_bucket" "tfstate" {
      + effective_labels            = {
          + "goog-terraform-provisioned" = "true"
        }
      + force_destroy               = false
      + id                          = (known after apply)
      + location                    = "US-CENTRAL1"
      + name                        = 
      + project                     = (known after apply)
      + project_number              = (known after apply)
      + public_access_prevention    = "enforced"
      + rpo                         = (known after apply)
      + self_link                   = (known after apply)
      + storage_class               = "STANDARD"
      + terraform_labels            = {
          + "goog-terraform-provisioned" = "true"
        }
      + uniform_bucket_level_access = true
      + url                         = (known after apply)

      + soft_delete_policy (known after apply)

      + versioning {
          + enabled = true
        }

      + website (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

google_storage_bucket.tfstate: Creating...
google_storage_bucket.tfstate: Creation complete after 3s

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

```

## tfstateファイルを作成したバケットへ格納する設定
backendを指定する際にバケットがすでに存在している必要があるので先ほど作成したバケットを指定します
バケット名は変数を使わずにハードコーディングする必要があるので注意です
tfstateファイルはterraform/state配下に格納されます

```backend.tf
terraform {
  backend "gcs" {
    bucket = "<バケット名>"
    prefix = "terraform/state"
  }
}

```

バケット名は秘匿情報なので.gitignoreします
```.gitignore
backend.tf
```

backendの内容を反映させたいのでもう一度初期化します
バケット作成時にすでにtfstateファイルが作成されているので今回は既存のtfstateファイルを使用します
以下の選択肢でyesを入力し、以下のように初期化が完了したら成功です

```
Enter "yes" to copy and "no" to start with an empty state.
```

```
terraform init
Initializing the backend...
Acquiring state lock. This may take a few moments...
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "gcs" backend. No existing state was found in the newly
  configured "gcs" backend. Do you want to copy this state to the new "gcs"
  backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes

Releasing state lock. This may take a few moments...

Successfully configured the backend "gcs"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing provider plugins...
- Reusing previous version of hashicorp/google from the dependency lock file
- Using previously-installed hashicorp/google v6.8.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.
```

## tfstateが格納されているか確認しよう！
以下のようにtfstateファイルがバケット内に格納されていれば成功でs

![スクリーンショット 2025-03-02 10.32.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1965efcb-ba9e-45ef-b80c-9b6055a94eda.png)

## バケット名をgit管理したくない時
バケット名を特定されたくないユースケースがあるかと思います
その際は以下のように記載します

```backend.tf
terraform {
  backend "gcs" {}
}
```

その後、以下のようにterraform initします
```
terraform init -backend-config="bucket=<bucket_name>" -backend-config="prefix=terraform/state"
```

以下のように初期化できれば成功です
```
Initializing the backend...

Successfully configured the backend "gcs"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing provider plugins...
- Finding hashicorp/google versions matching "6.8.0"...
- Installing hashicorp/google v6.8.0...
- Installed hashicorp/google v6.8.0 (signed by HashiCorp)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

## 参考
https://cloud.google.com/docs/terraform/resource-management/store-state?hl=ja

https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build

https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-variables

https://github.com/terraform-google-modules/cloud-foundation-training/issues/18

https://cloud.google.com/storage/docs/uniform-bucket-level-access?hl=ja#should-you-use
