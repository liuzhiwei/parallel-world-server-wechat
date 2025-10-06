FROM alpine:3.18

# 使用 3.18 的腾讯云镜像（HTTPS）
RUN printf "https://mirrors.tencent.com/alpine/v3.18/main\nhttps://mirrors.tencent.com/alpine/v3.18/community\n" > /etc/apk/repositories

# python + pip + 证书
RUN apk add --no-cache python3 py3-pip ca-certificates \
    && python3 -m ensurepip \
    && pip3 install --no-cache-dir --upgrade pip \
         -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

WORKDIR /app
COPY . /app

# 安装依赖（与 requirements.txt 保持一致；显式指定镜像）
RUN pip3 install --no-cache-dir -r requirements.txt \
        -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

EXPOSE 80

# 用 shell 展开 PORT，兼容云托管端口注入；Gunicorn 生产可用
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-80} run:app"]
