FROM alpine:3.18

# 使用腾讯云镜像
RUN printf "https://mirrors.tencent.com/alpine/v3.18/main\nhttps://mirrors.tencent.com/alpine/v3.18/community\n" > /etc/apk/repositories

# 系统依赖：运行时 + 构建期（musl 上编 gevent/greenlet 常用）
RUN apk add --no-cache python3 py3-pip ca-certificates \
 && apk add --no-cache --virtual .build-deps build-base python3-dev musl-dev libffi-dev \
 && update-ca-certificates

# 设定工作目录
WORKDIR /app

# 1) 仅拷贝 requirements 到镜像（利用缓存）
COPY requirements.txt ./requirements.txt

# 2) 先安装依赖（镜像层可缓存）
RUN python3 -m ensurepip --upgrade \
 && pip3 install --no-cache-dir --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com \
 && pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

# 3) 再拷贝剩余源代码（改变代码不会让上面的依赖层失效）
COPY . .

# 4) 移除构建依赖，缩小体积
RUN apk del .build-deps

# 5) 暴露端口 & 启动命令
EXPOSE 80
CMD ["sh", "-c", "gunicorn -k gevent -w 1 -t 0 --keep-alive 75 -b 0.0.0.0:${PORT:-80} run:app"]
