#!/usr/bin/env python3
"""
DeepSeek V3 持续对话测试脚本
"""

import os
import sys


from ai_service import DeepSeekV3Service

def main():
    """主对话函数"""
    print("🤖 DeepSeek V3 单轮对话测试")
    print("=" * 50)
    print("输入 'quit' 或 'exit' 退出对话")
    print("=" * 50)
    
    try:
        # 初始化AI服务
        ai_service = DeepSeekV3Service()
        print("✅ AI服务初始化成功")
        
        while True:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            # 跳过空输入
            if not user_input:
                continue
            
            try:
                # 构建单轮对话消息
                messages = [
                    {"role": "user", "content": user_input}
                ]
                
                # 调用AI服务
                print("🤖 AI正在思考...")
                result = ai_service.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000,
                )
                
                # 获取AI回复
                ai_response = ai_service.get_response_text(result)
                usage_info = ai_service.get_usage_info(result)
                
                # 显示AI回复
                print(f"🤖 AI: {ai_response}")
                
                # 显示Token使用情况
                if usage_info:
                    total_tokens = usage_info.get('total_tokens', 0)
                    print(f"📊 Token使用: {total_tokens}")
                
            except Exception as e:
                print(f"❌ 错误: {str(e)}")
                print("请检查API Key配置或网络连接")
    
    except ValueError as e:
        print(f"❌ 初始化失败: {str(e)}")
        print("请检查DEEPSEEK_API_KEY环境变量配置")
    except KeyboardInterrupt:
        print("\n👋 对话已中断")
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")

if __name__ == "__main__":
    main()
