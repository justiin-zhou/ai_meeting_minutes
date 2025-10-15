#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议助手服务客户端示例

展示如何在Python项目中调用会议助手API
"""

import requests
import json
from typing import Generator, Dict, Any


class MeetingAssistantClient:
    """会议助手客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            base_url: 服务地址
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def generate_summary(
        self,
        srt_text: str,
        meeting_id: str,
        log_id: str = None,
        stream: bool = False
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        生成会议纪要
        
        Args:
            srt_text: SRT格式的会议转写文本
            meeting_id: 会议ID
            log_id: 日志ID（可选）
            stream: 是否流式返回
            
        Returns:
            如果stream=False，返回完整结果字典
            如果stream=True，返回生成器
        """
        if log_id is None:
            log_id = f"summary_{meeting_id}"
        
        data = {
            "log_id": log_id,
            "srt_text": srt_text,
            "meeting_id": meeting_id,
            "stream": stream
        }
        
        response = self.session.post(
            f"{self.base_url}/summary",
            json=data,
            stream=stream
        )
        
        if stream:
            return self._stream_response(response)
        else:
            return response.json()
    
    def chat(
        self,
        srt_text: str,
        meeting_id: str,
        messages: list,
        log_id: str = None,
        stream: bool = False
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        会议问答
        
        Args:
            srt_text: SRT格式的会议转写文本
            meeting_id: 会议ID
            messages: 对话历史
            log_id: 日志ID（可选）
            stream: 是否流式返回
            
        Returns:
            如果stream=False，返回完整结果字典
            如果stream=True，返回生成器
        """
        if log_id is None:
            log_id = f"chat_{meeting_id}"
        
        data = {
            "log_id": log_id,
            "srt_text": srt_text,
            "meeting_id": meeting_id,
            "messages": messages,
            "stream": stream
        }
        
        response = self.session.post(
            f"{self.base_url}/chat",
            json=data,
            stream=stream
        )
        
        if stream:
            return self._stream_response(response)
        else:
            return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            服务状态信息
        """
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def _stream_response(self, response) -> Generator[Dict[str, Any], None, None]:
        """
        处理流式响应
        
        Args:
            response: requests响应对象
            
        Yields:
            每行的JSON数据
        """
        for line in response.iter_lines():
            if line:
                try:
                    yield json.loads(line.decode('utf-8'))
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    continue


# ===== 使用示例 =====

def example_non_stream():
    """示例1: 非流式调用"""
    print("=" * 60)
    print("示例1: 非流式调用会议纪要生成")
    print("=" * 60)
    
    client = MeetingAssistantClient()
    
    # 检查服务状态
    health = client.health_check()
    print(f"服务状态: {health}\n")
    
    # 会议文本
    srt_text = """1
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
    
    # 生成会议纪要
    result = client.generate_summary(
        srt_text=srt_text,
        meeting_id="meeting_001",
        stream=False
    )
    
    print(f"状态码: {result['status']}")
    print(f"会议纪要:\n{result['data']['answer']}\n")


def example_stream():
    """示例2: 流式调用"""
    print("=" * 60)
    print("示例2: 流式调用会议纪要生成")
    print("=" * 60)
    
    client = MeetingAssistantClient()
    
    srt_text = """1
00:00:01,000 --> 00:00:03,000
大家好，欢迎参加今天的产品讨论会。

2
00:00:04,500 --> 00:00:08,000
今天我们主要讨论新版本的功能规划。
"""
    
    # 流式生成会议纪要
    print("会议纪要: ", end='', flush=True)
    
    for chunk in client.generate_summary(
        srt_text=srt_text,
        meeting_id="meeting_002",
        stream=True
    ):
        if chunk['status'] == 200:
            answer = chunk['data']['answer']
            is_end = chunk['data']['is_end']
            
            if answer:
                print(answer, end='', flush=True)
            
            if is_end == 1:
                print("\n\n✓ 生成完成\n")
                break


def example_chat():
    """示例3: 会议问答"""
    print("=" * 60)
    print("示例3: 会议问答")
    print("=" * 60)
    
    client = MeetingAssistantClient()
    
    srt_text = """1
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
    
    # 先生成会议纪要（非流式）
    print("正在生成会议纪要...")
    client.generate_summary(
        srt_text=srt_text,
        meeting_id="meeting_003",
        stream=False
    )
    print("会议纪要生成完成\n")
    
    # 进行问答
    messages = [
        {"role": "user", "content": "会议主要讨论了什么内容？"}
    ]
    
    result = client.chat(
        srt_text=srt_text,
        meeting_id="meeting_003",
        messages=messages,
        stream=False
    )
    
    print(f"问题: {messages[0]['content']}")
    print(f"回答: {result['data']['answer']}\n")


def example_multi_turn_chat():
    """示例4: 多轮对话"""
    print("=" * 60)
    print("示例4: 多轮对话")
    print("=" * 60)
    
    client = MeetingAssistantClient()
    
    srt_text = """1
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
    
    # 先生成会议纪要
    print("正在生成会议纪要...")
    client.generate_summary(
        srt_text=srt_text,
        meeting_id="meeting_004",
        stream=False
    )
    print("会议纪要生成完成\n")
    
    # 模拟多轮对话
    conversation = []
    
    # 第一轮
    question1 = "会议讨论了哪些功能？"
    conversation.append({"role": "user", "content": question1})
    
    result1 = client.chat(
        srt_text=srt_text,
        meeting_id="meeting_004",
        messages=conversation,
        stream=False
    )
    
    answer1 = result1['data']['answer']
    conversation.append({"role": "assistant", "content": answer1})
    
    print(f"用户: {question1}")
    print(f"助手: {answer1}\n")
    
    # 第二轮
    question2 = "发布时间定了吗？"
    conversation.append({"role": "user", "content": question2})
    
    result2 = client.chat(
        srt_text=srt_text,
        meeting_id="meeting_004",
        messages=conversation,
        stream=False
    )
    
    answer2 = result2['data']['answer']
    
    print(f"用户: {question2}")
    print(f"助手: {answer2}\n")


if __name__ == "__main__":
    try:
        # 运行各个示例
        example_non_stream()
        example_stream()
        example_chat()
        example_multi_turn_chat()
        
        print("=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到服务器")
        print("请确保服务已启动: python src/run_server.py")
    except Exception as e:
        print(f"❌ 运行示例时出错: {str(e)}")

