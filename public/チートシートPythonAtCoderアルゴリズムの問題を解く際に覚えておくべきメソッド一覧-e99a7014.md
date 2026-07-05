---
title: 【チートシート】【Python】AtCoder(アルゴリズム)の問題を解く際に覚えておくべきメソッド一覧
tags:
  - Python
  - AtCoder
private: false
updated_at: '2022-11-17T13:51:07+09:00'
id: e99a70147004814f15a6
organization_url_name: null
slide: false
---
## 記事を書いた背景
AtCoderの問題を解くのが他の人と比べてなぜ遅いのか自分で考えた結果
- AtCoder頻出のメソッドを知らなさすぎ
- Python独自の記法にまだ慣れていない
- Pythonの便利メソッドが全くわからない
- 文法なんてその都度調べたらいいや、という甘えがあった

のではないかと思い、執筆に至りました。文法の復習も兼ねています

## 前提
- コード例は全てPythonです
- AtCoderに興味ない方でも文法チェックシートとしても利用できます

## input
### 一つの文字列を標準入力
```python
N = input()
```

### 一つの数字を標準入力
```python
N = int(input())
```

### 二つ以上の文字列を標準入力
```python
# algo rithm
N, M = map(str, input().split())
print(N) # algo
print(M) # rithm
```

### 二つの数字を標準入力
```python
# 1 3
N, M = map(int, input().split())
print(N) # 1
print(M) # 3
```

### 標準入力(改行)
```python
M = input()
N = input()
```

### 無数の数字を入力
```python
# いくつ入力するかわからない場合はmap関数を使う
# set
N = set(map(int, input().strip().split()))
# tuple
N = tuple(map(int, input().strip().split()))
# list
N = list(map(int, input().strip().split()))
```

### 無数の文字を入力
```python
# いくつ入力するかわからない場合はmap関数を使う
# set
N = set(map(str, input().strip().split()))
# tuple
N = tuple(map(str, input().strip().split()))
# list
N = list(map(str, input().strip().split()))
```

### N個の要素を縦で入力
```python
N = int(input())
# N個分の要素を入れることができる空のlistを用意
A = [""] * N
# 数字なら A = [0] * N
# N個分代入していく
for i in range(N):
    A[i] = input()
```


## 計算
### 整数値を求める
```python
# 1 3 8
A, B, C = map(int, input().split())
# /だと4.0(double)になるが//だと4(int)になる
print((A+B+C)//3) # 3
```

### 複数の整数の最大値を求める
```python
# 31 41 59 26
A, B, C, D = map(int, input().split()) 
print(max(A, B, C, D)) # 59
```

### 複数の整数の最小値を求める
```python
# 31 41 59 26
A, B, C, D = map(int, input().split()) 
print(min(A, B, C, D)) # 26
```

### 割り算の商のみを抽出
```python
print(17 // 4) # 4
```

#### 過去問(abc239,B問題)
https://atcoder.jp/contests/abc239/tasks/abc239_b

#### 回答
<details>

```python
X = int(input())
print(X // 10)
```
</details>

### 絶対値
```python
print(abs(-10)) # 10
```

### 累乗
```python
print(pow(4,3)) # 64
```

### ルート
```python
from math import sqrt

print(sqrt(2)) # 1.4142135623730951
```

## 進数

### 10進数を2進数、8進数、16進数へ
```python
# 2進数
print(format(100, 'b')) # 1100100
# 8進数
print(format(100, 'o')) # 144
# 16進数
print(format(100,'x')) # 64
```

### 2進数、8進数、16進数を10進数へ
```python
print(int("1010", 2))  # 10
print(int("172", 8))  # 122
print(int("4D2", 16))  # 1234
```

### 10進数からN進数
2,8以外の進数に変換する用の自作関数
2 <= N <= 9  
```python
def ten_to_n(num_10, num):
    if num >= 10 or num <= 1:
        return "numの引数は1以上9以下にしてください"
    # 後ろから値を桁を追加することを容易にするためにanswerをstringとして定義
    answer = ""
    # num_10がnumで割り切れなくなるまでひたすらwhile文を回す
    while num_10 >= num:
        if num_10 % num == 0:
            answer += "0"
        else:
            answer += str(num_10 % num)
        num_10 = num_10 // num
    answer += str(num_10)
    # 文字列answerを反転させる
    return answer[::-1]

print(ten_to_n(3429,3)) # 11201000
```

## 文字列
### 長さ
```python
# S = "algo"
S = input
print(len(S)) # 4
```

### 文字列の中の特定の要素を出力
```python
# S = "algo"
S = input() # 入力を文字列型として受け取る 
print(S[2]) # g
```

### 文字列を昇順に並び替える
```python
algo = "algorithm"
print(''.join(sorted(algo))) #aghilmort
```

#### 過去問(abc242,B問題)
https://atcoder.jp/contests/abc242/tasks/abc242_b

#### 回答
<details>

```python
s = input()
print(''.join(sorted(s)))
```
</details>

### 文字列を降順に並び替える
```python
algo = "algorithm"
print("".join(sorted(algo, reverse=True))) # tromlihga
```

### 文字列を反転させる
```python
algo = "algorithm"
print(algo[::-1]) # mhtirogla
```

### 空白または文字列の先頭と末尾を削除する(strip)
```python
algo = "　　algorithm　　"
print(algo.strip()) # "algorithm"
anaconda = "anaconda"
print(anaconda.strip("a")) # "nacond"
ran_word = "aaalambaaa"
print(ran_word.strip("a")) # "lamb"
```

### 空白または文字列の先頭を削除する(lstrip)
```python
algo = "  algorithm  "
print(algo.lstrip()) # "algorithm  "
anaconda = "anaconda" 
print(anaconda.lstrip("a")) # "naconda"
ran_word = "aaalambaaa"
print(ran_word.lstrip("a")) # "lambaaa"
```

### 空白または文字列の末尾を削除する(rstrip)
```python
algo = "  algorithm  "
print(algo.rstrip())
anaconda = "anaconda" # "  algorithm"
print(anaconda.rstrip("a")) 
ran_word = "aaalambaaa" # anacond
print(ran_word.rstrip("a")) # "aaalamb"
```

### 一つの文字列を別の文字列へ置き換える
```python
date = "1982/07/06"
print(date.replace("/", "-")) # "1982-07-06"
```

### 文字列が含まれているか判定
```python
print("algo" in "algorithm") # True
print("yama" in "river") # False
```

## for
### list内の数を足し算する
```python
list = [10,20,30]
total = 0
# listの数だけitems変数に入れる
for items in list:
    total += items
print(total) # 60
```

### range
```python
N = 3
A = ["apple","banana","grape"]
text = ""
# 0からN-1までのループ
for i in range(N):
    text += A[i]
print(text) # applebananagrape
```

#### _(アンダーバー/アンダースコア)
変数を使わない際は_を使う
```python
for _ in range(5):
  print("Atcoder")
# Atcoder
# Atcoder
# Atcoder
# Atcoder
# Atcoder
```


## 配列
### 要素数
```python
A = ["apple", "banana", "grape"]
print(len(A)) # 3
```

### 文字列をlist化
```python
S = turtle
S_list = list(S)
print(S_list) # ['t','u','r','t','l','e']
```

### 特定の区切り文字で文字列をlist化
```python
S = 'one::two::three'
S_list = s.split('::')
print(S_list)
# ['one', 'two', 'three']
```


### listを文字列に
```python
S_list = ['t','u','r','t','l','e']
S = "".join(S_list)
print(S) # turtle
```

### listの要素を後ろから指定
```python
list = [1,2,3,4,5]
print(list[-1]) # 5
print(list[-4]) # 2
```

### インデックスを指定して取り出す(スライス)
`list[開始インデックス:終了インデックス]`
と記載することで特定のインデックスの範囲内で配列を取り出すことができる
```python
list = [1,2,3,4,5]
#　1以上、3未満のインデックスの配列を取り出す
print(list[1:3]) # [2, 3]
# 2以上のインデックスの配列を取り出す
print(list[2:]) # [3, 4, 5]
# 2未満のインデックスの配列を取り出す
print(list[:2]) # [1, 2]
```

### listの末尾に要素を追加
```python
list = [1,2,3,4]
list.append(5)
print(list) # [1, 2, 3, 4, 5]
algo = ["a", "l", "g", "o"]
algo.append("r")
print(algo) # ['a', 'l', 'g', 'o', 'r']
```

### listの末尾に別のlistを結合
```python
list = [1,2,3,4]
list.extend([5, 6, 7])
print(list) # [1, 2, 3, 4, 5, 6, 7]
algo = ["a", "l", "g", "o"]
algo.extend(["r", "i", "t", "h", "m"])
print(algo) # ['a', 'l', 'g', 'o', 'r', 'i', 't', 'h', 'm']
```

### listの指定位置に要素を追加
```python
list = [1, 2, 3, 4]
list.insert(2, 5)
print(list) # [1, 2, 5, 3, 4]
list.insert(-1, 6)
print(list) # [1, 2, 5, 3, 6, 4]
algo = ["a", "l", "g", "o"]
algo.insert(1, "r")
print(algo) # ['a', 'r', 'l', 'g', 'o']
algo.insert(-2, "i")
print(algo) # ['a', 'r', 'l', 'i', 'g', 'o']
```

### list内の最大値
```python
list = [1,2,3,4]
print(max(list)) # 4
alpha = ["Z", "A", "J", "W"]
print(max(alpha)) # Z
```

### list内の最小値
```python
list = [1,2,3,4]
print(min(list)) # 1
alpha = ["Z", "A", "J", "W"]
print(min(alpha)) # A
```

### list内の数字を絶対値の降順に並び替える
```python
list = [1,2,3,4]
list.reverse()
print(list) # [4,3,2,1]
```

### list内の要素を取り出す(アンパック)
```python
list = [1, 2, 3, 4, 5]
algo = ["a", "l", "g", "o"]
print(*list) # 1 2 3 4 5
print(*algo) # a l g o
```

### list内の要素を昇順に並び替える
```python
num = ["1", "3", "2", "5", "4"]
num.sort()
print(num) # ['1', '2', '3', '4', '5']
algo = ["a", "l", "g", "o", "r", "i", "t", "h", "m"]
algo.sort()
print(list) # ['a', 'g', 'h', 'i', 'l', 'm', 'o', 'r', 't']
```

### list内のインデックスを取得
```python
num = [1, 3, 2, 5, 4]
print(num.index(3)) # 1
algo = ["a", "l", "g", "o", "r", "i", "t", "h", "m"]
print(algo.index("r")) # 4
```

### listの中に要素があるかどうか判定
```python
num1 = [1, 3, 2, 5, 4]
num2 = {1, 3, 6}
for num in num2:
    if num in num1:
        print("Yes")
    else:
        print("No")
# Yes
# Yes
# No
algo1 = ["a", "l", "g", "o"]
algo2 = {"a", "r", "t"}
for algo in algo2:
    if algo in algo1:
        print("Yes")
    else:
        print("No")
# Yes
# No
# No
```

#### 過去問(abc236,B問題)
https://atcoder.jp/contests/abc236/tasks/abc236_c

#### 回答
<details>

```python
# コードを記載
N, M = map(int, input().split())
S = list(map(str, input().split()))
# Tをsetにして処理を高速化
T = set(map(str, input().split()))
for items in S:
    if items in T:
        print("Yes")
    else:
        print("No")
```

</details>


### list内の要素を降順に並び替える
```python
num = ["1", "3", "2", "5", "4"]
num.sort(reverse=True) 
print(num) # ['5', '4', '3', '2', '1']
algo = ["a", "l", "g", "o", "r", "i", "t", "h", "m"]
algo.sort(reverse=True)
print(list) # ['t', 'r', 'o', 'm', 'l', 'i', 'h', 'g', 'a']
```

### list内の要素を反転させる(reversed)
```python
num = [1, 3, 2, 5, 4]
num_rev = list(reversed(num))
print(num_rev) # [4, 5, 2, 3, 1]
algo = ["a", "l", "g", "o", "r", "i", "t", "h", "m"]
algo_rev = list(reversed(algo))
print(algo_rev)  # ['m', 'h', 't', 'i', 'r', 'o', 'g', 'l', 'a']
```

### list内の重複をなくす(setにキャスト)
```python
list = [1,4,1,2,2,1]
unique_list = set(list)
print(unique_list) # {1, 2, 4}
```

#### 過去問(abc240,B問題)
https://atcoder.jp/contests/abc240/tasks/abc240_b

#### 回答
<details>

```python
n = int(input())
print(len(set(map(int, input().split()))))
```

</details>


### 転置配列
```python
L = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(list(zip(*L))) # [(1, 4, 7), (2, 5, 8), (3, 6, 9)]
```

## dict(辞書型)
### keyとvalueをfor文使って出力
```python
fruit_dict = {1: "apple", 2: "banana", 3: "grape"}

# items()を使ってk,vにそれぞれkeyとvalueを代入
for k, v in fruit_dict.items():
    print(k)
    print(v)
# 1
# apple
# 2
# banana
# 3
# grape
```

### 要素を全て削除
```python
fruit_dict = {1: "apple", 2: "banana", 3: "grape"}

fruit_dict.clear()
print(fruit_dict) # {}
```

### 指定した要素を削除
```python
fruit_dict = {1: "apple", 2: "banana", 3: "grape"}

fruit_dict.pop("apple")
print(fruit_dict) # {2: "banana", 3: "grape"}
```

## lambda
無名関数のこと。簡単な関数ならlambdaにすることでコード量を大幅に削減できる
関数を引数とするメソッドにlamdbaを指定すると便利

### map
リストの各要素に対して関数を適用する
```python
# map(lambda式,リスト)
num = [1, 2, 3, 4, 5]
print(list(map(lambda x: x**2, num))) # [1, 4, 9, 16, 25]
```

### filter
条件を満たす要素を抽出する
```python
# filter(lambda式,リスト)
print(list(filter(lambda x: x % 2 == 0, num))) # [2, 4]
```

## まとめ
今後もアルゴリズムの勉強をするつもりなので問題を解いて新たにわかったメソッドなどがあれば逐一追記していく予定です

## 記事の紹介
VSCode内でAtCoderのワークフローを全て完結させることができますので余裕のある方はこちらも記事も参照していただけると幸いです

https://qiita.com/shun198/items/6dffbb119a3a133b8e3c


