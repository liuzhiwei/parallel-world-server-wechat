# 基础镜像
FROM alpine:3.13

# 时区（可选，使用上海时间）
# RUN apk add --no-cache tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

# 安装 HTTPS 证书 & 基础工具
RUN apk add --no-cache ca-certificates bash build-base python3 py3-pip \
    && rm -rf /var/cache/apk/*

# 设置 pip 源（腾讯镜像，加速）
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install -r requirements.txt

# 拷贝代码
COPY . .

# 暴露端口（云托管会用 $PORT）
EXPOSE 80

# 启动命令 - 使用 gunicorn + geventwebsocket
CMD ["sh", "-c", "gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$PORT run:app"]
