FROM alpine:3.13

# 使用国内镜像加速 apk
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories

# python + pip + 证书（证书用于云托管启动时的证书注入 hook）
RUN apk add --no-cache python3 py3-pip ca-certificates \
    && python3 -m ensurepip \
    && pip3 install --no-cache --upgrade pip \
    && pip3 config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip3 config set global.trusted-host mirrors.cloud.tencent.com

WORKDIR /app
COPY . /app

# 安装依赖（与 requirements.txt 保持一致）
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 80

# 关键：用 shell 展开 PORT，兼容云托管端口注入；gunicorn 生产可用
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-80} run:app"]
