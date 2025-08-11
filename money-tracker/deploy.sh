#!/bin/bash

echo "开始部署记账系统到云服务器..."

# 停止现有服务
echo "停止现有服务..."
docker-compose down

# 清理旧的镜像和容器
echo "清理旧的镜像和容器..."
docker system prune -f

# 删除旧的镜像
echo "删除旧的后端镜像..."
docker rmi $(docker images | grep money_tracker | awk '{print $3}') 2>/dev/null || echo "没有找到旧镜像"

# 重新构建并启动服务
echo "重新构建并启动服务..."
docker-compose up --build -d

# 等待数据库启动
echo "等待数据库启动..."
sleep 20

# 检查数据库状态
echo "检查数据库状态..."
docker-compose logs db --tail=10

# 等待后端启动
echo "等待后端启动..."
sleep 20

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 检查后端容器日志
echo "检查后端容器日志..."
docker-compose logs backend --tail=30

# 检查前端容器日志
echo "检查前端容器日志..."
docker-compose logs frontend --tail=10

# 测试健康检查
echo "测试后端健康检查..."
sleep 5
curl -f http://localhost/api/health && echo "健康检查成功" || echo "健康检查失败"

echo "部署完成！"
echo "访问地址: http://8.153.106.141"
echo "测试页面: http://8.153.106.141/test.html"
echo "注册页面: http://8.153.106.141/register.html"
echo "登录页面: http://8.153.106.141/login.html"

echo "如果服务没有正常启动，请运行: docker-compose logs -f"