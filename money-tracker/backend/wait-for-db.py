#!/usr/bin/env python3
import time
import socket
import sys
import subprocess

def wait_for_db(host='db', port=3306, timeout=60):
    """等待数据库启动"""
    print(f"等待数据库 {host}:{port} 启动...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"数据库 {host}:{port} 已启动!")
                return True
        except Exception as e:
            pass
        
        print(f"等待数据库启动... ({int(time.time() - start_time)}s)")
        time.sleep(2)
    
    print(f"等待数据库超时 ({timeout}s)")
    return False

if __name__ == "__main__":
    if wait_for_db():
        print("启动 Flask 应用...")
        # 启动 Flask 应用
        subprocess.run([sys.executable, "app.py"])
    else:
        print("数据库连接失败，退出")
        sys.exit(1)