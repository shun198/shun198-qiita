---
title: '[React]useStateを使ったフォームの作成方法'
tags:
  - React
  - useState
private: false
updated_at: '2023-09-03T10:23:46+09:00'
id: ee16224ff444021d8572
organization_url_name: null
slide: false
---
## 概要
フォームを作成するにあたって最もスタンダートであるuseStateを使った方法について解説していきたいと思います

## ディレクトリ構成
ディレクトリ構成は以下のとおりです
```
tree
・
├── src
|   └── components
|       └── Form.js
├── App.js
├── index.js
└── styles.css
```

## フォームの作成
Formというコンポーネントを作成します
順番に一つずつ解説していきます

```react:src/components/Form.js
import { useState } from "react";

function Form() {
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    // ブラウザで設定されているデフォルトの動作をキャンセルさせる
    e.preventDefault();
    console.log({
      employeeNumber,
      password
    });
  };

  const handleChangeEmployeeNumber = (e) => {
    setEmployeeNumber(e.target.value);
  };
  const handleChangePassword = (e) => {
    setPassword(e.target.value);
  };

  return (
    <div>
      <h1>ログイン画面</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <input
            id="employee_number"
            name="employee_number"
            placeholder="社員番号"
            type="text"
            onChange={handleChangeEmployeeNumber}
          />
        </div>
        <div>
          <input
            id="password"
            name="password"
            placeholder="パスワード"
            type="password"
            onChange={handleChangePassword}
          />
        </div>
        <div>
          <button type="submit">ログイン</button>
        </div>
      </form>
    </div>
  );
}

export default Form;
```

```react:App.js
import Form from "./components/Form";
import "./styles.css";

export default function App() {
  return (
    <div className="App">
      <Form />
    </div>
  );
}
```

## form
フォームを作成する際は以下のように<form>タグを使用します
```react
<div>
    <form onSubmit={handleSubmit}>
    </form>
</div>
```

ReactのonSubmit関数を使ってフォーム内に入力した値を後述するhandleSubmit関数内で処理します

## input
フォーム内に<input>タグを入れて入力欄を作成します
```react
<div>
    <input
        id="employee_number"
        name="employee_number"
        placeholder="社員番号"
        type="text"
        onChange={handleChangeEmployeeNumber}
    />
</div>
```

inputタグ内の要素は以下のとおりです
|要素|説明|
|--|--|
|id|inputタグのid|
|name|入力欄の名前|
|placeholder|入力欄が空の時に表示されるテキスト|
|type|入力欄の型<br>通常のテキストを入力する場合はtext,パスワードはpasswordにするなど入力したい項目に応じて設定|
|onChange|ReactのEventハンドラ関数の一つ<br>入力値が変わったときなどに即座に実行されます<br>inputイベントと同様に動作|

input typeの型の一覧は以下を参照してください

https://developer.mozilla.org/ja/docs/Web/HTML/Element/input#input_%E3%81%AE%E5%9E%8B

## button
```react
フォーム内に<button>タグを入れてボタンを作成します
<div>
  <button type="submit">ログイン</button>
</div>
```

buttonのtypeを"submit"に設定し、formタグ内で定義したonSubmit関数を実行させます

## useState
useStateを使って
- 社員番号
- パスワード

の状態を管理します
今回は以下の変数、関数名にし、デフォルト値を未入力("")とします

```react
import { useState } from "react";

const [employeeNumber, setEmployeeNumber] = useState("");
const [password, setPassword] = useState("");
```

## onChangeハンドラー
前述したinputタグ内に記載したハンドラーを作成します
このハンドラー関数がないとsubmitする際に値がない状態でsubmitハンドラーに渡されてしまうので
useStateで作成した関数を使用します

```react
const handleChangeEmployeeNumber = (e) => {
    setEmployeeNumber(e.target.value);
};
const handleChangePassword = (e) => {
    setPassword(e.target.value);
};
```

### eって何？
eはReactのイベントオブジェクトで公式ドキュメントによると標準のEventプロパティの一部を実装してるとのことです
```react
const handleChangeEmployeeNumber = (e) => {
    console.log(e)
};
```
```
{_reactName: 'onChange', _targetInst: null, type: 'change', nativeEvent: InputEvent, target: HTMLInputElement, …}
```

eイベントオブジェクト内にtargetというイベントが発生したDOMのノードが含まれており、
e.target.valueからemployeeNumberのDOMのノードから入力した値を取得できます
今回はinput内の値を取得したいので以下のようにsetEmployeeNumber関数内にe.target.valueを記載します

```react
// 社員番号00000001を入力した時
const handleChangeEmployeeNumber = (e) => {
    console.log(e.target.value) // 00000001
    setEmployeeNumber(e.target.value);
};
```

## onSubmitハンドラー
ReactのEventハンドラ関数でフォームが送信されたときに実行されます
```react
const handleSubmit = (e) => {
    // Prevent the browser from reloading the page
    e.preventDefault();
    console.log({
      employeeNumber,
      password
    });
};
```

### e.preventDefault
onSubmitハンドラのデフォルトの挙動について説明すると、ブラウザ側でFormに入力したデータを現在のURLに送信し、ページを更新します
今回はブラウザを再読み込みさせずにsubmitHandlerが実行されたらhandleSubmit内の処理を実行させたいので
```react
e.preventDefault()
```
と明記することで、デフォルトの処理をオーバーライドさせます

## フォームを操作してみよう
フォームに任意の値を入力し、ログインボタンを押します

![スクリーンショット 2023-09-03 10.14.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8b298ca9-4d21-dd01-ed50-f8fbedea2154.png)

コンソール上に以下のように値が表示されたら成功です
```
{employeeNumber: '00000001', password: 'test'}
```

https://codesandbox.io/embed/react-form-usestate-xlqjh3?file=/src/App.js&fontsize=14&hidenavigation=1&view=split

## まとめ
今回は非常に簡単なフォームを作成してみました
今後バリデーションやリダイレクト機能も実装してみたいのでまた別の記事を作成してみたいと思います

## 参考
https://reffect.co.jp/react/react-hook-form/#%E3%83%A9%E3%82%A4%E3%83%96%E3%83%A9%E3%83%AA%E3%82%92%E5%88%A9%E7%94%A8%E3%81%97%E3%81%AA%E3%81%84%E5%A0%B4%E5%90%88

https://developer.mozilla.org/ja/docs/Web/HTML/Element/form

https://developer.mozilla.org/ja/docs/Web/API/HTMLFormElement/submit_event

https://developer.mozilla.org/ja/docs/Web/HTML/Element/input

https://ja.react.dev/reference/react-dom/components/select#props

https://ja.react.dev/reference/react-dom/components/common#react-event-object
