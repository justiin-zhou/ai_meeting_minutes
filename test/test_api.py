#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 测试数据
test_srt_text = """1
00:00:01,000 --> 00:00:03,000
大家好，欢迎参加今天的产品讨论会。

2
00:00:04,500 --> 00:00:08,000
今天我们主要讨论新版本的功能规划。

3
00:00:09,000 --> 00:00:12,000
首先，用户反馈希望增加导出功能。

4
00:00:13,000 --> 00:00:16,000
其次，需要优化界面的响应速度。

5
00:00:17,000 --> 00:00:20,000
最后，我们计划在下个月15号发布这个版本。
"""


def test_health():
    """测试健康检查接口"""
    print("=" * 50)
    print("测试健康检查接口...")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}\n")


def test_summary_stream():
    """测试流式会议纪要生成"""
    print("=" * 50)
    print("测试流式会议纪要生成...")
    print("=" * 50)
    
    data = {
        "log_id": "test_summary_001",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_001",
        "stream": True
    }
    
    response = requests.post(
        f"{BASE_URL}/summary",
        json=data,
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
    print()


def test_summary_non_stream():
    """测试非流式会议纪要生成"""
    print("=" * 50)
    print("测试非流式会议纪要生成...")
    print("=" * 50)
    
    data = {
        "log_id": "test_summary_002",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_002",
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/summary", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")


def test_chat_stream():
    """测试流式会议问答"""
    print("=" * 50)
    print("测试流式会议问答...")
    print("=" * 50)
    
    # 先生成会议纪要
    summary_data = {
        "log_id": "test_chat_summary",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_003",
        "stream": False
    }
    requests.post(f"{BASE_URL}/summary", json=summary_data)
    
    # 进行问答
    chat_data = {
        "log_id": "test_chat_001",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_003",
        "messages": [
            {
                "role": "user",
                "content": "会议主要讨论了什么内容？"
            }
        ],
        "stream": True
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=chat_data,
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
    print()


def test_chat_non_stream():
    """测试非流式会议问答"""
    print("=" * 50)
    print("测试非流式会议问答...")
    print("=" * 50)
    
    # 先生成会议纪要
    summary_data = {
        "log_id": "test_chat_summary_2",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_004",
        "stream": False
    }
    requests.post(f"{BASE_URL}/summary", json=summary_data)
    
    # 进行问答
    chat_data = {
        "log_id": "test_chat_002",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_004",
        "messages": [
            {
                "role": "user",
                "content": "新版本计划什么时候发布？"
            }
        ],
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")


def test_multi_turn_chat():
    """测试多轮对话"""
    print("=" * 50)
    print("测试多轮对话...")
    print("=" * 50)
    
    # 先生成会议纪要
    summary_data = {
        "log_id": "test_multi_chat_summary",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_005",
        "stream": False
    }
    requests.post(f"{BASE_URL}/summary", json=summary_data)
    
    # 多轮对话
    messages = [
        {
            "role": "user",
            "content": "会议讨论了哪些功能？"
        },
        {
            "role": "assistant",
            "content": "会议讨论了导出功能和界面响应速度优化。"
        },
        {
            "role": "user",
            "content": "发布时间定了吗？"
        }
    ]
    
    chat_data = {
        "log_id": "test_multi_chat",
        "srt_text": test_srt_text,
        "meeting_id": "meeting_005",
        "messages": messages,
        "stream": False
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}\n")


if __name__ == "__main__":
    try:
        # 测试健康检查
        test_health()
        
        # 测试会议纪要生成
        test_summary_stream()
        test_summary_non_stream()
        
        # 测试会议问答
        test_chat_stream()
        test_chat_non_stream()
        
        # 测试多轮对话
        test_multi_turn_chat()
        
        print("=" * 50)
        print("所有测试完成！")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请确保服务已启动（python src/run_server.py）")
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")

