FROM python:3.10-slim

WORKDIR /app
COPY . /app

# 配置 pip 国内源（腾讯云镜像更稳定）
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple && \
    pip config set global.trusted-host mirrors.cloud.tencent.com

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80
CMD ["gunicorn", "-b", "0.0.0.0:80", "run:app"]
