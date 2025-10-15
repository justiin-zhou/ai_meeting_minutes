#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek 配置测试脚本

快速验证 DeepSeek API 配置是否正确
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

def test_deepseek_connection():
    """测试 DeepSeek API 连接"""
    
    print("=" * 60)
    print("DeepSeek API 配置测试")
    print("=" * 60)
    
    # 读取配置
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    print(f"\n配置信息：")
    print(f"  API Key: {'✓ 已配置' if api_key else '✗ 未配置'}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    
    if not api_key:
        print("\n❌ 错误: DEEPSEEK_API_KEY 未配置")
        print("请在 .env 文件中设置: DEEPSEEK_API_KEY=sk-xxxxx")
        return False
    
    # 初始化客户端
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        print(f"\n✓ OpenAI 客户端初始化成功")
    except Exception as e:
        print(f"\n❌ 客户端初始化失败: {str(e)}")
        return False
    
    # 测试非流式调用
    print(f"\n测试 1: 非流式调用...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            stream=False
        )
        
        answer = response.choices[0].message.content if response.choices else ''
        print(f"✓ 非流式调用成功")
        print(f"  回答: {answer}")
    except Exception as e:
        print(f"❌ 非流式调用失败: {str(e)}")
        return False
    
    # 测试流式调用
    print(f"\n测试 2: 流式调用...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "从1数到5"}
            ],
            stream=True
        )
        
        print(f"✓ 流式调用成功")
        print(f"  回答: ", end='', flush=True)
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end='', flush=True)
        
        print()  # 换行
    except Exception as e:
        print(f"❌ 流式调用失败: {str(e)}")
        return False
    
    # 测试会议纪要场景
    print(f"\n测试 3: 会议纪要生成...")
    try:
        meeting_text = """
今天我们讨论了新产品的发布计划。
主要决定了以下几点：
1. 产品将在下个月15号发布
2. 需要增加导出功能
3. 优化界面响应速度
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": f"请为以下会议内容生成简要纪要：\n\n{meeting_text}"}
            ],
            stream=False
        )
        
        summary = response.choices[0].message.content if response.choices else ''
        print(f"✓ 会议纪要生成成功")
        print(f"  纪要:\n{summary}")
    except Exception as e:
        print(f"❌ 会议纪要生成失败: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！DeepSeek API 配置正确")
    print("=" * 60)
    print("\n可以使用以下配置启动服务：")
    print("  LLM_PROVIDER=deepseek")
    print("  python src/run_server.py")
    
    return True


if __name__ == "__main__":
    try:
        success = test_deepseek_connection()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

