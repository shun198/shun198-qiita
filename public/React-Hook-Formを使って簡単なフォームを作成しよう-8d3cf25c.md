---
title: React Hook Formを使って簡単なフォームを作成しよう！
tags:
  - React
  - react-hook-form
private: false
updated_at: '2023-10-09T15:49:30+09:00'
id: 8d3cf25cc366d8478bf5
organization_url_name: null
slide: false
---
## 概要
React Hook Formを使ったフォームの作成について今回はログイン用のフォームを例に解説します

## 前提
- React Hook Formをインストール済み
- React Hook Formの使い方についての記事なのでSubmitした後のログイン処理等については本記事では解説しません

## React Hook Formとは？
Reactでフォームを簡単に作成できるライブラリです
input要素に入力した値を取得するだけではなく、バリデーション機能なども備えています

https://react-hook-form.com/

## フォームを作成してみよう！
以下がログイン用のフォームです
今回は
- 社員番号(8桁)
- パスワード(8文字以上、32文字以下で少なくとも1つ以上の半角英字と数字で構成される)

を入力する想定で記載しております

```react
import { useForm } from 'react-hook-form';

function Login() {
  const { 
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    // ログインボタンを押した時のみバリデーションを行う
    reValidateMode: 'onSubmit',
  });

  const onSubmit = (data) => {
    console.log(data);
  }

  return (
    <div className="Login">
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <input
            id="employee_number"
            name="employee_number"
            placeholder="社員番号"
            {...register('employee_number', {
              required: {
                value: true, 
                message: '社員番号を入力してください',
              },
              pattern: {
                value: /^[0-9]{8}$/,
                message: '8桁の数字のみ入力してください。',
              },
            })} 
          />
            {errors.employee_number?.message && <div>{errors.employee_number.message}</div>}
        </div>
        <div>
          <input
            id="password"
            name="password"
            placeholder="パスワード"
            type="password"
            {...register('password', { 
              required: {
                value: true,
                message: 'パスワードを入力してください'
              },
              pattern: {
                value: /^(?=.*[a-zA-Z])(?=.*\d).{8,32}$/,
                message: '8文字以上、32文字以下の少なくとも1つ以上の半角英字と数字をもつパスワードを入力してください。',
              },
            })}
          />
            {errors.password?.message && <div>{errors.password.message}</div>}
        </div>
        <button type="submit">ログイン</button>
      </form>
    </div>
  );
}

export default Login;
```

また、今回はCSSを適用させずに作成するので見た目は以下の通りです

![スクリーンショット 2023-10-09 11.30.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ec8c0674-3db4-f9e6-f317-7046b22b08cf.png)

では、一つずつ解説していきます

### useForm
React Hook Formを使ってフォームを簡単に作成する際にためのカスタムフックです
今回は引数として
- register
- handleSubmit
- formState

を使用します
引数の使用方法については後ほど解説します

```react
  const { 
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    // ログインボタンを押した時のみバリデーションを行う
    reValidateMode: 'onSubmit',
  });
```

また、フォームをSubmitする際のreValidateModeはデフォルトでonChange(フォームに入力した内容が変化するたびにバリデーションメッセージを表示)になっていますが、今回はフォームをSubmitしたタイミングの時だけバリデーションメッセージを表示させたいので
```react
reValidateMode: 'onSubmit',
```
と記載します

reValidateModeの詳細は以下の通りです

https://react-hook-form.com/docs/useform#reValidateMode


### onSubmit
フォームをSubmitした後の挙動ですが今回はReact Hook Formでフォームを作成することをゴールにしているのでSubmitしたデータをコンソール上で表示させることだけにとどめておきます

```react
  const onSubmit = (data) => {
    console.log(data);
  }
```

### フォームのJSX
JSX内に
- 社員番号
- パスワード

のバリデーションなどの詳細な設定を記載します

```react
  return (
    <div className="Login">
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <input
            id="employee_number"
            name="employee_number"
            placeholder="社員番号"
            {...register('employee_number', {
              required: {
                value: true, 
                message: '社員番号を入力してください',
              },
              pattern: {
                value: /^[0-9]{8}$/,
                message: '8桁の数字のみ入力してください。',
              },
            })} 
          />
            {errors.employee_number?.message && <div>{errors.employee_number.message}</div>}
        </div>
        <div>
          <input
            id="password"
            name="password"
            placeholder="パスワード"
            type="password"
            {...register('password', { 
              required: {
                value: true,
                message: 'パスワードを入力してください'
              },
              pattern: {
                value: /^(?=.*[a-zA-Z])(?=.*\d).{8,32}$/,
                message: '8文字以上、32文字以下の少なくとも1つ以上の半角英字と数字をもつパスワードを入力してください。',
              },
            })}
          />
            {errors.password?.message && <div>{errors.password.message}</div>}
        </div>
        <button type="submit">ログイン</button>
      </form>
    </div>
  );
```

#### handleSubmit
フォーム内のバリデーションが成功したらこの関数を使って入力した内容を自身で作成したonSubmit関数に渡します

```react
      <form onSubmit={handleSubmit(onSubmit)}>
```

handleSubmitの詳細は以下の通りです

https://react-hook-form.com/docs/useform/handlesubmit

#### register
registerを使ってフォームにバリデーションを適用します

```react
            {...register('employee_number', {
              required: {
                value: true, 
                message: '社員番号を入力してください',
              },
              pattern: {
                value: /^[0-9]{8}$/,
                message: '8桁の数字のみ入力してください。',
              },
            })} 
```

#### register内ってどうなっているの？
上記のコードでスプレッド構文を使ってname(今回だとemployee_number)を取得しています
また、今回は設定していませんが任意で
- onChange
- onBlur
- ref

を指定できます

```react
const { onChange, onBlur, name, ref } = register('employee_number'); 
// include type check against field path with the name you have supplied.
        
<input 
  onChange={onChange} // assign onChange event 
  onBlur={onBlur} // assign onBlur event
  name={name} // assign name prop
  ref={ref} // assign ref prop
/>
// same as above
<input {...register('employee_number')} />
```

#### 適用されているバリデーション
社員番号には
- required
- pattern

の2種類のバリデーションを適用させています

requiredは必須項目かどうかのバリデーションで今回は必須にしています
社員番号が未入力の場合のバリデーションメッセージを指定します

patternは正規表現のバリデーションで今回は8桁の半角数字以外を入力した場合のバリデーションメッセージを設定します

バリデーションエラーになった場合はsubmitハンドラーが実行されないようになっています

```react
{...register('employee_number', {
              required: {
                value: true, 
                message: '社員番号を入力してください',
              },
              pattern: {
                value: /^[0-9]{8}$/,
                message: '8桁の数字のみ入力してください。',
              },
            })} 
```

パスワードも同様にregisterを使ってバリデーションを行います

```react
          <input
            id="password"
            name="password"
            placeholder="パスワード"
            type="password"
            {...register('password', { 
              required: {
                value: true,
                message: 'パスワードを入力してください'
              },
              pattern: {
                value: /^(?=.*[a-zA-Z])(?=.*\d).{8,32}$/,
                message: '8文字以上、32文字以下の少なくとも1つ以上の半角英字と数字をもつパスワードを入力してください。',
              },
            })}
          />
```

registerの詳細は以下の通りです

https://react-hook-form.com/docs/useform/register

#### formState
formStateを使ってフォーム全体の状態を管理します
今回はformStateのerrorsオブジェクトを使用します
errorsオブジェクトからemployee_numberのエラーメッセージを取得できます
もしバリデーションエラーが発生したら下記のdivタグを表示させるよう記載します

```
{errors.employee_number?.message && <div>{errors.employee_number.message}</div>}
```

formStateの詳細は以下の通りです

https://react-hook-form.com/docs/useform/formstate

## 実際に触ってみよう！
何も入力せずにログインボタンを押すと以下のように未入力のバリデーションエラーが表示されます

![スクリーンショット 2023-10-09 15.43.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79308556-0360-1ea0-81a0-7c62254d5080.png)

社員番号が8文字の半角数字以外の場合は以下のようにpatternで記載したバリデーションエラーが表示されます
![スクリーンショット 2023-10-09 15.44.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7da385f3-7313-3af0-35fc-f9630585688c.png)

パスワードも全てのパターンはここでは紹介しませんがpatternで記載したバリデーションエラーが表示されます
![スクリーンショット 2023-10-09 15.45.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/647bd7a2-6ec3-9c41-e339-9e26fa4a07c3.png)

以下のようにバリデーションを満たした上で社員番号とパスワードを入力し、コンソールに表示されたら成功です
![スクリーンショット 2023-10-09 15.46.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7b822831-71ab-d38a-df75-87dfdfd98bcc.png)

![スクリーンショット 2023-10-09 15.48.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/806a8551-45e5-e777-524f-2067043f55cd.png)

以上です

## 参考
https://react-hook-form.com/

https://reffect.co.jp/react/react-hook-form/
