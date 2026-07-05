---
title: '[初心者向け] これだけは覚えておこう！ReactのComponentとPropsについて徹底解説'
tags:
  - JavaScript
  - React
private: false
updated_at: '2023-08-10T18:38:46+09:00'
id: 4a947675153a32a4e9ab
organization_url_name: null
slide: false
---
## 概要
フロントエンド開発でよく使用されるReactの概要と知っておくべき基本的な用語について解説していきたいと思います

## Reactとは
Javascriptのライブラリの1つでUIを作成することに特化しています
Reactを使うことで効率よくUIを作成できます
Reactを理解するには後述する項目について知る必要があります

## 説明する項目一覧
- Component
- Props

### Component
> A component is a piece of the UI (user interface) that has its own logic and appearance. A component can be as small as a button, or as large as an entire page.

公式ドキュメントに記載の通りUIのひとまとまり(部品)です
componentの中にはボタンであったりページ全体として扱うものもあります
componentを使用することでよく使うUIを共通化して再利用しやすくしたり拡張しやすくなるなどメリットが大きいです

#### Componentの作成方法
一般的にcomponentはcomponentsフォルダ内に作成します
今回は例としてComponentItem.jsフォルダ内に作成します

```
tree
・
├── src
|   ├── components
|   |   └── ComponentItem.js
|   ├── App.js
|   ├── index.js
|   └── styles.css
└── package.json
```

一般的に作成する際はfunction Componentつまり関数として以下のように作成します
戻り値の中にJSXというHTML に似た構文を使用して、JavaScriptのコード内でUIを直感的かつ簡単に記述できる構文を使用します
別のファイルで使用する際は
```
export default component名
```
を記載します

```src/components/ComponentItem.js
function ComponentPractice() {
  return <h2>This is a component</h2>;
}

export default ComponentPractice;
```

```
import　component名　from componentのパス
```

を記載するとcomponentを使用できます
また、CSSを適用させる際は適用させるタグ内に
```
<div className="App">
```

という風にclassNameを記載します
TailwindなどのCSSのライブラリを使う際も同様です

```src/App.js
import "./styles.css";
import ComponentPractice from "./components/ComponentItem";

export default function App() {
  return (
    <div className="App">
      <h1>Hello World</h1>
      <ComponentPractice />
    </div>
  );
}
```

以下のように表示されたら成功です

https://codesandbox.io/embed/react-playground-xvw972?fontsize=14&hidenavigation=1&view=split

### Props
> React components use props to communicate with each other. Every parent component can pass some information to its child components by giving them props. Props might remind you of HTML attributes, but you can pass any JavaScript value through them, including objects, arrays, and functions.

Reactでは親componentと子component間へ値を渡すなどの連携をする際にPropsを使用します
Propsとして渡すことができるものはオブジェクト、配列、関数含めて多岐に渡ります
いわゆる引数のようなものだと思えばイメージしやすいかと思います

#### Propsを使ったcomponentの作成方法
今回はInput.jsを作成してpropsを使ったcomponentを作成していきます

```
tree
・
├── src
|   ├── components
|   |   └── Input.js
|   ├── App.js
|   ├── index.js
|   └── styles.css
└── package.json
```

今回はfunction Componentを使うため、Propsを使うときは以下のように
```
function function_name(props) {
```
という風に引数にpropsと記載します
また、componentの使用先の引数をJSX内に指定することで
指定した引数を使って値を参照させることができます
今回は別のファイルでcomponentを使用した際の引数をlabelとして定義します

```src/components/Input.js
function Input(props) {
  return (
    <div>
      <label>{props.label}</label>
      <input />
    </div>
  );
}

export default Input;
```

下記のようにInputのcomponent内に
```
label="社員番号"
```

という風に渡したいPropsの値を記載します

```src/app.js
import "./styles.css";
import Input from "./components/Input";

export default function App() {
  return (
    <div className="App">
      <h1>ログイン画面</h1>
      <Input label="社員番号" />
      <Input label="パスワード" />
    </div>
  );
}
```

以下のように表示されたら成功です

https://codesandbox.io/embed/react-playground-props-6h8khl?file=/src/App.js:0-231&fontsize=14&hidenavigation=1&view=split


## 参考
https://react.dev/

https://zenn.dev/web_tips/articles/c3851133f52d16

https://www.webstaff.jp/guide/trend/react/#case01
