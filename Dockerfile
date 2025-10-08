FROM alpine:3.18

# 使用腾讯云镜像
RUN printf "https://mirrors.tencent.com/alpine/v3.18/main\nhttps://mirrors.tencent.com/alpine/v3.18/community\n" > /etc/apk/repositories

# 运行时 + 构建依赖（gevent/greenlet 在 musl 上常需编译）
RUN apk add --no-cache python3 py3-pip ca-certificates \
    && apk add --no-cache --virtual .build-deps \
         build-base python3-dev musl-dev libffi-dev

WORKDIR /app
COPY . /app

# pip 源与安装
RUN python3 -m ensurepip \
 && pip3 install --no-cache-dir --upgrade pip \
      -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com \
 && pip3 install --no-cache-dir -r requirements.txt \
      -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com \
 && apk del .build-deps

EXPOSE 80

# gevent-websocket worker + 禁用超时 + 合理 keep-alive；单 worker 保障进程内注册表一致
CMD ["sh", "-c", "gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -t 0 --keep-alive 75 -b 0.0.0.0:${PORT:-80} run:app"]
