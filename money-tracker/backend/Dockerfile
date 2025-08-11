# 使用官方 Python 3.8 精简镜像
FROM python:3.8-slim


# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 复制项目文件到容器中
COPY . .

# 暴露 Flask 默认端口
EXPOSE 5000

# 设置 Flask 环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 创建等待脚本
COPY wait-for-db.py /app/wait-for-db.py

# 启动 Flask 应用
CMD ["python", "wait-for-db.py"]
