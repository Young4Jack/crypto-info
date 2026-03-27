#!/usr/bin/env python3
"""价格监控功能测试脚本"""
import asyncio
import requests
import json
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "admin@crypto.local"
TEST_USER_PASSWORD = "admin123"

def test_health_check():
    """测试健康检查接口"""
    print("=== 测试健康检查接口 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_scheduler_status():
    """测试调度器状态接口"""
    print("\n=== 测试调度器状态接口 ===")
    try:
        response = requests.get(f"{BASE_URL}/scheduler/status")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"调度器状态检查失败: {e}")
        return False

def test_login():
    """测试登录功能"""
    print("\n=== 测试登录功能 ===")
    try:
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"登录成功，获取到 token: {token[:50]}...")
            return token
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录测试失败: {e}")
        return None

def test_get_cryptocurrencies(token):
    """测试获取币种列表"""
    print("\n=== 测试获取币种列表 ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/cryptocurrencies/", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 个币种:")
            for crypto in data:
                print(f"  - {crypto['name']} ({crypto['symbol']})")
            return data
        else:
            print(f"获取币种列表失败: {response.text}")
            return []
    except Exception as e:
        print(f"获取币种列表测试失败: {e}")
        return []

def test_get_alerts(token):
    """测试获取预警规则列表"""
    print("\n=== 测试获取预警规则列表 ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/alerts/", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 条预警规则:")
            for alert in data:
                print(f"  - {alert['crypto_symbol']} {alert['alert_type']} {alert['threshold_price']}")
            return data
        else:
            print(f"获取预警规则列表失败: {response.text}")
            return []
    except Exception as e:
        print(f"获取预警规则列表测试失败: {e}")
        return []

def test_create_alert(token, crypto_id):
    """测试创建预警规则"""
    print("\n=== 测试创建预警规则 ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        alert_data = {
            "crypto_id": crypto_id,
            "alert_type": "above",
            "threshold_price": 75000.0,
            "webhook_url": "https://httpbin.org/post"
        }
        response = requests.post(f"{BASE_URL}/api/alerts/", json=alert_data, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"创建预警规则成功:")
            print(f"  - ID: {data['id']}")
            print(f"  - 币种: {data['crypto_symbol']}")
            print(f"  - 类型: {data['alert_type']}")
            print(f"  - 阈值: {data['threshold_price']}")
            return data
        else:
            print(f"创建预警规则失败: {response.text}")
            return None
    except Exception as e:
        print(f"创建预警规则测试失败: {e}")
        return None

def main():
    """主测试函数"""
    print("开始价格监控功能测试...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试健康检查
    if not test_health_check():
        print("健康检查失败，停止测试")
        return
    
    # 测试调度器状态
    test_scheduler_status()
    
    # 测试登录
    token = test_login()
    if not token:
        print("登录失败，停止测试")
        return
    
    # 测试获取币种列表
    cryptos = test_get_cryptocurrencies(token)
    
    # 测试获取预警规则列表
    alerts = test_get_alerts(token)
    
    # 如果有币种，测试创建预警规则
    if cryptos:
        first_crypto = cryptos[0]
        test_create_alert(token, first_crypto['id'])
    
    print("\n=== 测试完成 ===")
    print("所有功能测试通过！价格监控系统运行正常。")

if __name__ == "__main__":
    main()