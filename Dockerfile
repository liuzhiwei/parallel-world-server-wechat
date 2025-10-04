# 选择基础镜像：Alpine 太精简，很多科学包/依赖会缺失，建议直接用 Debian slim
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 拷贝代码
COPY . /app

# 设置 pip 源（用腾讯云的 PyPI 镜像，加速）
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
 && pip config set global.trusted-host mirrors.cloud.tencent.com \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

# 暴露端口（云托管会自动注入 $PORT，这里只是声明）
EXPOSE 80

# 启动命令 —— 使用 gunicorn + geventwebsocket 支持 WebSocket
CMD ["sh", "-c", "gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -b 0.0.0.0:$PORT run:app"]
