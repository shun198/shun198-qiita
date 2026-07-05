---
title: 【チートシート】【Javascript】AtCoder(アルゴリズム)の問題を解く際に覚えておくべきメソッド一覧
tags:
  - JavaScript
  - AtCoder
private: false
updated_at: '2023-09-02T21:01:10+09:00'
id: dd4b68c7401f45137530
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- コード例は全てJavascriptです
- AtCoderに興味ない方でも文法チェックシートとしても利用できます

## 標準出力
### 一つの文字列を標準入力
```javascript
function main(input) {
  const a = input.split(" ");

  // コードを入れる

}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
```

### 一つの数字を標準入力
```javascript
function main(input) {
  const a = Number(input.split(" "));

  // コードを入れる

}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
```

### 2つ以上の文字列を連続で標準入力
```javascript
function main(input) {
  const args = input.split('\n');
  const words = args[0].split(' ');
  const a = words[0];
  const b = words[1];

  // コードを入れる

}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));
```

### 2つ以上の数字を連続で標準入力
```javascript
function main(input) {
  const args = input.split('\n');
  const nums = args[0].split(' ');
  const a = Number(nums[0]);
  const b = Number(nums[1]);

  // コードを入れる

}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));
```

## 文字列
### 文字列の長さ
```javascript
const str = '大阪府大阪市西区千代崎3丁目中2-1';
console.log(str.length) // 18
```

### 先頭と後ろの空白を削除する
```javascript
const str = '　東京都千代田区霞が関1-2-3　　霞が関ビル　　';
console.log(str.trim()); // 東京都千代田区霞が関1-2-3　　霞が関ビル
```

### 文字列内の空白も削除する
```javascript
const str = '　東京都千代田区霞が関1-2-3　　霞が関ビル　　';
console.log(str.replace(/\s+/g, '')); // 東京都千代田区霞が関1-2-3霞が関ビル
```

### 一つの文字列を別の文字列へ置き換える
```javascript
const str = '大阪府大阪市西区千代崎3丁目中2-1';
console.log(str.replace('大阪', '京都'));　// '京都府大阪市西区千代崎3丁目中2-1'
```

### 文字列が含まれるか判定
```javascript
const str = '大阪府大阪市西区千代崎3丁目中2-1';
if (str.includes('大阪府')) {
  //strに'大阪府'を含む場合の処理
  console.log('大阪の住所'); // '大阪の住所'
} else {
  //strに'大阪府'を含まれない場合の処理
  console.log('違うよ');
}
```

|正規表現|説明|
|--|--|
|\s|一つ以上の空白文字|
|+|回以上繰り返されること|
|g|マッチしたすべてのパターンを一括で置換|

## for
```javascript
let str = '';

for (let i = 0; i < 9; i++) {
  str = str + i;
}
console.log(str); // "012345678"
```

## 配列
### 配列の中身を展開
```javascript
const array = [1,2,3]
// ...(Spread構文を使うと配列の要素を全て展開できる)
console.log(...array) // 1,2,3
```

### 要素を先頭から追加
```javascript
const array = [2,4,6]
array.push(8)
console.log(array) // 2,4,6,8
```

### 要素を後ろから追加
```javascript
const array = [2,4,6]
array.unshift(8);
console.log(...array); // 8,2,4,6
```

### 文字列を配列に
```javascript
const str = 'hello';
const arr = [...str];
console.log(arr); // ['h', 'e', 'l', 'l', 'o']
```

###　配列を文字列に
```javascript
const arr = ['h', 'e', 'l', 'l', 'o']
const str = arr.join(",")
console.log(str) // 'hello'
```

### インデックスを指定して取り出す(スライス)
```javascript
const arr = ['h', 'e', 'l', 'l', 'o']
console.log(arr.slice(1,3)) // ['e', 'l']
console.log(arr.slice(0,3)) // ['h', 'e', 'l']
console.log(arr.slice(-1)) // ['o']
```

## map
### 配列の各要素を2倍にする
```javascript
var items = [1, 2, 3, 4, 5];

var result = items.map(function (value) {
  //配列の各要素を2倍にする
  return value * 2;
});

console.log(result);　// [2, 4, 6, 8, 10]
```

## まとめ
今後もアルゴリズムの勉強をするつもりなので問題を解いて新たにわかったメソッドなどがあれば逐一追記していく予定です

## 参考
https://qiita.com/cotton11aq/items/a8b93d61fca8f83ffaae
