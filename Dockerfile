FROM alpine:3.13

# 国内源加速
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories

# 必备：python3 + pip + 证书（证书为了配合云托管启动时的证书注入hook）
RUN apk add --no-cache python3 py3-pip ca-certificates \
    && python3 -m ensurepip \
    && pip3 install --no-cache --upgrade pip \
    && pip3 config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip3 config set global.trusted-host mirrors.cloud.tencent.com

WORKDIR /app
COPY . /app

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 80

# 用 shell 形式展开 PORT，兼容云托管的端口注入
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-80} run:app"]
