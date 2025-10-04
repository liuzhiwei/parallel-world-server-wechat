FROM alpine:3.13

# 安装证书、python3、pip、编译工具
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories \
 && apk add --no-cache ca-certificates bash build-base python3 py3-pip \
 && rm -rf /var/cache/apk/*

# pip 镜像
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
 && pip config set global.trusted-host mirrors.cloud.tencent.com \
 && pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 80

# 正确的启动命令（必须通过 sh -c 展开 $PORT）
CMD ["sh", "-c", "gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:${PORT} run:app"]
