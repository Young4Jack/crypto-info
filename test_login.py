#!/usr/bin/env python3
"""测试登录功能"""
import requests
import json

def test_login():
    """测试登录功能"""
    url = "http://localhost:8000/api/auth/login"
    data = {
        "email": "admin@crypto.local",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"获取到的 token: {token}")
            
            # 测试获取用户信息
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get("http://localhost:8000/api/auth/me", headers=headers)
            print(f"用户信息状态码: {me_response.status_code}")
            print(f"用户信息: {me_response.text}")
            
            return True
        else:
            print("登录失败")
            return False
            
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    test_login()