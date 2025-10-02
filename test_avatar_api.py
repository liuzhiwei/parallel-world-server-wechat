#!/usr/bin/env python3
"""
测试数字分身API接口
"""
import requests
import json

# 测试配置
BASE_URL = "http://127.0.0.1:5000"  # 本地测试
# BASE_URL = "https://your-domain.wxcloudrun.com"  # 微信云托管测试

def test_upload_avatar():
    """测试头像上传接口"""
    print("=== 测试头像上传接口 ===")
    
    # 创建一个测试图片文件（1x1像素的PNG）
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {
        'file': ('test_avatar.png', test_image_data, 'image/png')
    }
    data = {
        'type': 'avatar'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json().get('data', {}).get('url')
    except Exception as e:
        print(f"上传失败: {e}")
        return None

def test_create_profile(avatar_url):
    """测试创建分身接口"""
    print("\n=== 测试创建分身接口 ===")
    
    data = {
        "user_id": "test_user_123",
        "name": "我的数字分身",
        "description": "一个友善、聪明的AI助手，喜欢帮助用户解决问题",
        "avatar_url": avatar_url
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/profile", 
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"创建分身失败: {e}")
        return None

def main():
    """主测试函数"""
    print("开始测试数字分身API...")
    
    # 测试头像上传
    avatar_url = test_upload_avatar()
    if not avatar_url:
        print("头像上传失败，跳过创建分身测试")
        return
    
    # 测试创建分身
    result = test_create_profile(avatar_url)
    if result and result.get('code') == 0:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":
    main()
