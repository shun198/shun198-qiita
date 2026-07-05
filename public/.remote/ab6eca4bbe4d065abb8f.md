---
title: '【Docker】コンテナ起動時にPorts are not available: address already in useが出た時の対処法について'
tags:
  - Docker
  - Linuxコマンド
  - docker-compose
private: false
updated_at: '2024-04-12T14:18:35+09:00'
id: ab6eca4bbe4d065abb8f
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- Linuxの基本的な操作は知っている
- Dockerの基礎的な知識を持っている
- 今回はMySQLとRailsのDockerコンテナを使用したときに起こった状況を解説しています

## エラーが出る原因
``docker compose up``と打つと
```terminal:terminal
❯ docker compose up
[+] Running 2/2
 ⠿ Container rails-db-1   Created                                                                                                                                                              0.0s
 ⠿ Container rails-web-1  Recreated                                                                                                                                                            0.2s
Attaching to rails-db-1, rails-web-1
Error response from daemon: 
- Ports are not available: 
- exposing port TCP 0.0.0.0:3306 -> 0.0.0.0:0: listen tcp 0.0.0.0:3306: 
- bind: address already in use
```
というエラー文が表示されます
要するにMySQLのポート3306を指定したら空いてないから使えないよって言われてます
そのため、今回はすでに開いているポート3306を閉じます

## 対処法
ターミナル上で
```terminal:terminal
sudo lsof -i:3306
```
と打ちます
``lsof(listen open files)``のオプション``-i``でポート番号を指定することができるので
今回は``-i:3306``でMySQLのポート番号を指定します
すると
```terminal:terminal
sudo lsof -i:3306
COMMAND PID   USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
mysqld  150 _mysql   24u  IPv6 0x99545106b728bf5f      0t0  TCP *:mysql (LISTEN)
```
と表示されます
ポートを落としたいので
```terminal:terminal
sudo kill <PID>
```
と打ちます。私の画面ではPIDが150なので　
```terminal:terminal
sudo kill 150
```
と打ちますがPIDは人によって違うと思います
```terminal:terminal
sudo lsof -i:3306
```
と打っても何も表示されないことを確認してもう一度コンテナを起動します

```terminal:terminal
docker compose up
[+] Running 1/0
 ⠿ Container rails-db-1  Created                                                                                                                                                               0.0s
Attaching to rails-db-1, rails-web-1
rails-db-1   | 2022-06-04 04:27:17+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.22-1debian10 started.
rails-db-1   | 2022-06-04 04:27:18+00:00 [Note] [Entrypoint]: Switching to dedicated user 'mysql'
rails-db-1   | 2022-06-04 04:27:18+00:00 [Note] [Entrypoint]: Entrypoint script for MySQL Server 8.0.22-1debian10 started.
rails-web-1  | ruby 2.7.3p183 (2021-04-05 revision 6847ee089d) [x86_64-linux]
rails-db-1   | 2022-06-04T04:27:18.803556Z 0 [System] [MY-010116] [Server] /usr/sbin/mysqld (mysqld 8.0.22) starting as process 1
rails-db-1   | 2022-06-04T04:27:18.824864Z 1 [System] [MY-013576] [InnoDB] InnoDB initialization has started.
rails-db-1   | 2022-06-04T04:27:19.119291Z 1 [System] [MY-013577] [InnoDB] InnoDB initialization has ended.
rails-db-1   | 2022-06-04T04:27:19.356866Z 0 [System] [MY-011323] [Server] X Plugin ready for connections. Bind-address: '::' port: 33060, socket: /var/run/mysqld/mysqlx.sock
・・・
略
・・・
/usr/sbin/mysqld: ready for connections. Version: '8.0.22'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.
rails-web-1  | => Booting Puma
rails-web-1  | => Rails 6.1.3.2 application starting in development 
rails-web-1  | => Run `bin/rails server --help` for more startup options
rails-web-1  | Puma starting in single mode...
・・・
略
・・・
rails-web-1  | Use Ctrl-C to stop
```
無事コンテナの起動に成功しました!!

## まとめ
初めてこのエラーに遭遇した時はなんじゃこれ？って焦っていた記憶がありますが上記の記事通りにやれば解決できるかと思います。ポート番号を変更しても解決できますが極力変えない方がいいと思います

## 記事の紹介
以下の記事も書いたので良かったら読んでいただけると幸いです

https://qiita.com/shun198/items/ebcb1236b061acd14405

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/ee93c50eac2f7c77e443

## 参考文献
https://atmarkit.itmedia.co.jp/ait/articles/1904/18/news033.html

https://offlo.in/blog/port-kill.html
