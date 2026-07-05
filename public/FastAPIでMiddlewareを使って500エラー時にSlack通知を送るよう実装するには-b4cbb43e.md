---
title: FastAPIでMiddlewareを使って500エラー時にSlack通知を送るよう実装するには
tags:
  - Slack
  - middleware
  - FastAPI
  - Starlette
private: false
updated_at: '2025-02-24T18:48:42+09:00'
id: b4cbb43ec42f598e64e9
organization_url_name: null
slide: false
---
## 概要
500エラー発生時にFastAPIのアプリケーションのMiddlewareをoverrideしてSlackへ通知を送る方法について解説します

## 実装
### FastAPIのMiddlewareについて
FastAPIのアプリケーションのMiddlewareはStarletteのBaseHTTPMiddlewareクラスを継承しています
`@app.middleware("http")`のデコレータをメソッドに加えるだけでメソッド自体がBaseHTTPMiddlewareとして認識されます

```fastapi/applications.py
class FastAPI(Starlette):
    def middleware(
        self,
        middleware_type: Annotated[
            str,
            Doc(
                """
                The type of middleware. Currently only supports `http`.
                """
            ),
        ],
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """
        Add a middleware to the application.

        Read more about it in the
        [FastAPI docs for Middleware](https://fastapi.tiangolo.com/tutorial/middleware/).

        ## Example

        ```python
        import time

        from fastapi import FastAPI, Request

        app = FastAPI()


        @app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        ```
        """

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_middleware(BaseHTTPMiddleware, dispatch=func)
            return func

        return decorator
```

BaseHTTPMiddleware内の`__init__`メソッドのself.dispatch_funcにデコレータを追加したMiddlewareのインスタンスが代入されます
また、API実行時に`__call__`メソッドが呼ばれ、
```python
response = await self.dispatch_func(request, call_next)
```
内でdispatch_func、つまり作成したMiddlewareのメソッドが呼ばれます
BaseHTTPMiddlewareクラスを継承し、dispatch関数をoverrideすることでMiddlewareの処理をoverrideできますがデコレータを使用する際は定義したMiddlewareのメソッドがdispatch関数の役割を果たします

https://www.starlette.io/middleware/#basehttpmiddleware

そのため、Middleware用のメソッドを作成する際はrequestとcall_nextを引数に入れる必要があります

```starlette.middleware.base.py
class BaseHTTPMiddleware:
    def __init__(self, app: ASGIApp, dispatch: DispatchFunction | None = None) -> None:
        self.app = app
        self.dispatch_func = self.dispatch if dispatch is None else dispatch

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = _CachedRequest(scope, receive)
        wrapped_receive = request.wrapped_receive
        response_sent = anyio.Event()

        async def call_next(request: Request) -> Response:
            app_exc: Exception | None = None

            async def receive_or_disconnect() -> Message:
                if response_sent.is_set():
                    return {"type": "http.disconnect"}

                async with anyio.create_task_group() as task_group:

                    async def wrap(func: typing.Callable[[], typing.Awaitable[T]]) -> T:
                        result = await func()
                        task_group.cancel_scope.cancel()
                        return result

                    task_group.start_soon(wrap, response_sent.wait)
                    message = await wrap(wrapped_receive)

                if response_sent.is_set():
                    return {"type": "http.disconnect"}

                return message

            async def send_no_error(message: Message) -> None:
                try:
                    await send_stream.send(message)
                except anyio.BrokenResourceError:
                    # recv_stream has been closed, i.e. response_sent has been set.
                    return

            async def coro() -> None:
                nonlocal app_exc

                with send_stream:
                    try:
                        await self.app(scope, receive_or_disconnect, send_no_error)
                    except Exception as exc:
                        app_exc = exc

            task_group.start_soon(coro)

            try:
                message = await recv_stream.receive()
                info = message.get("info", None)
                if message["type"] == "http.response.debug" and info is not None:
                    message = await recv_stream.receive()
            except anyio.EndOfStream:
                if app_exc is not None:
                    raise app_exc
                raise RuntimeError("No response returned.")

            assert message["type"] == "http.response.start"

            async def body_stream() -> typing.AsyncGenerator[bytes, None]:
                async for message in recv_stream:
                    assert message["type"] == "http.response.body"
                    body = message.get("body", b"")
                    if body:
                        yield body
                    if not message.get("more_body", False):
                        break

                if app_exc is not None:
                    raise app_exc

            response = _StreamingResponse(status_code=message["status"], content=body_stream(), info=info)
            response.raw_headers = message["headers"]
            return response

        streams: anyio.create_memory_object_stream[Message] = anyio.create_memory_object_stream()
        send_stream, recv_stream = streams
        with recv_stream, send_stream, collapse_excgroups():
            async with anyio.create_task_group() as task_group:
                response = await self.dispatch_func(request, call_next)
                await response(scope, wrapped_receive, send)
                response_sent.set()
                recv_stream.close()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raise NotImplementedError()  # pragma: no cover
```

### ミドルウェアの作成
以下のようにMiddlewareを作成します
FastAPIではuvicorn側でloggerの設定が行われているのでMiddleware内でカスタムログを出力するには
```python
logger = logging.getLogger("uvicorn")
```

と記載する必要があります

```main.py
import logging
import traceback

from fastapi import FastAPI, Request, status, Response
from utils.slack import send_slack_notification

logger = logging.getLogger("uvicorn")

app = FastAPI()


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = request.url.path

    try:
        response = await call_next(request)
    except Exception as e:
        response = Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.error(f"Request: {method} {url} {response.status_code} ip: {client_ip}")
        send_slack_notification(traceback.format_exc())
    finally:
        return response

```

### Incomming Webhookの作成
作成方法についてはかなりわかりやすい記事があるので紹介します

https://documents.trocco.io/docs/how-to-generate-slack-webhook-url

Webhookを作成後、.envファイルに環境変数を記載します
```.env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXXXXXXXXXXXXXXXXX
```

### Slack通知を送るメソッドの作成

attachmentsを使用することでSlackのメッセージの横に定義した色の線が入る上に長いメッセージを折り畳めるようになるので見やすくなります
詳細はこちらの公式ドキュメントを参照してください

https://api.slack.com/reference/messaging/attachments

```utils/slack.py
import logging
import requests
import os
import json


logger = logging.getLogger("uvicorn")


def send_slack_notification(message: str):
    try:
        alarm_emoji = ":rotating_light:"
        text = alarm_emoji + message
        data = json.dumps(
            {
                "attachments": [{"color": "#e01d5a", "text": text}],
            }
        )
        headers = {"Content-Type": "application/json"}
        requests.post(
            url=os.environ.get("SLACK_WEBHOOK_URL"), data=data, headers=headers
        )
    except Exception as e:
        logger.error(f"Slack送信エラー: {e}")

```

## 実際に検証してみよう！
API実行時に500エラーが発生してしまった時、以下のようにSlack通知が来たら成功です

![スクリーンショット 2025-02-24 16.27.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/86e99f9e-1038-44a6-823f-7b34cc174f8f.png)

## 参考
https://fastapi.tiangolo.com/ja/tutorial/middleware/

https://fastapi.tiangolo.com/advanced/middleware/#integrated-middlewares

https://www.starlette.io/middleware/#basehttpmiddleware

[FastAPI and Uvicorn Logging](https://gist.github.com/liviaerxin/d320e33cbcddcc5df76dd92948e5be3b)

