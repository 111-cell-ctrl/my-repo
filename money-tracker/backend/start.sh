#!/bin/bash

# 等待数据库启动
echo "等待数据库启动..."
while ! nc -z db 3306; do
  sleep 1
done

echo "数据库已启动，开始启动Flask应用..."
python app.py