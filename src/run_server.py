#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from typing import Generator, Dict, Any
from flask import Flask, request, Response, stream_with_context
import qianfan
from openai import OpenAI

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置
try:
    from config import (
        LLM_PROVIDER, QIANFAN_ACCESS_KEY, QIANFAN_SECRET_KEY,
        DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
        HOST, PORT, DEFAULT_MODEL, LOG_LEVEL
    )
except ImportError:
    # 如果没有配置文件，使用默认值
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'qianfan')
    QIANFAN_ACCESS_KEY = os.getenv('QIANFAN_ACCESS_KEY', '')
    QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY', '')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'ERNIE-4.0-8K')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局缓存：存储会议的分段总结
meeting_cache: Dict[str, Dict[str, Any]] = {}

# 初始化LLM客户端
qianfan_client = None
deepseek_client = None

if LLM_PROVIDER == 'qianfan':
    qianfan_client = qianfan.ChatCompletion()
    logger.info(f"Using Qianfan LLM provider with model: {DEFAULT_MODEL}")
elif LLM_PROVIDER == 'deepseek':
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    logger.info(f"Using DeepSeek LLM provider with model: {DEEPSEEK_MODEL}")
else:
    logger.warning(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}, defaulting to qianfan")
    qianfan_client = qianfan.ChatCompletion()
    LLM_PROVIDER = 'qianfan'


def parse_srt_text(srt_text: str) -> str:
    """
    解析SRT格式文本，提取纯文本内容
    
    Args:
        srt_text: SRT格式的字幕文本
        
    Returns:
        提取后的纯文本内容
    """
    lines = srt_text.strip().split('\n')
    text_content = []
    
    for line in lines:
        line = line.strip()
        # 跳过序号行和时间轴行
        if line and not line.isdigit() and '-->' not in line:
            text_content.append(line)
    
    return '\n'.join(text_content)


def call_llm_stream(messages: list) -> Generator[str, None, None]:
    """
    统一的LLM流式调用接口
    
    Args:
        messages: 消息列表
        
    Yields:
        生成的文本内容
    """
    if LLM_PROVIDER == 'qianfan':
        # 千帆API调用
        resp = qianfan_client.do(
            messages=messages,
            stream=True,
            model=DEFAULT_MODEL
        )
        
        for chunk in resp:
            if chunk.get('result'):
                yield chunk['result']
                
    elif LLM_PROVIDER == 'deepseek':
        # DeepSeek API调用（通过OpenAI接口）
        response = deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def call_llm_non_stream(messages: list) -> str:
    """
    统一的LLM非流式调用接口
    
    Args:
        messages: 消息列表
        
    Returns:
        生成的完整文本
    """
    if LLM_PROVIDER == 'qianfan':
        # 千帆API调用
        resp = qianfan_client.do(
            messages=messages,
            stream=False,
            model=DEFAULT_MODEL
        )
        return resp.get('result', '')
        
    elif LLM_PROVIDER == 'deepseek':
        # DeepSeek API调用（通过OpenAI接口）
        response = deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content if response.choices else ''
    
    return ''


def generate_summary_stream(log_id: str, text_content: str, meeting_id: str) -> Generator[str, None, None]:
    """
    生成会议纪要的流式响应
    
    Args:
        log_id: 日志ID
        text_content: 会议文本内容
        meeting_id: 会议ID
        
    Yields:
        JSON格式的响应数据
    """
    try:
        # 构建提示词
        prompt = f"""请根据以下会议转写内容，生成一份完整的会议纪要。要求：
1. 提取会议主题
2. 总结主要讨论内容
3. 列出关键决策和行动项
4. 简洁清晰，重点突出

会议转写内容：
{text_content}

请生成会议纪要："""

        messages = [{"role": "user", "content": prompt}]
        
        # 调用LLM进行流式生成
        full_answer = ""
        for content in call_llm_stream(messages):
            full_answer += content
            
            # 返回中间结果
            yield json.dumps({
                "status": 200,
                "data": {
                    "answer": content,
                    "is_end": 0
                }
            }, ensure_ascii=False) + "\n"
        
        # 缓存完整的会议纪要
        if meeting_id not in meeting_cache:
            meeting_cache[meeting_id] = {}
        meeting_cache[meeting_id]['summary'] = full_answer
        meeting_cache[meeting_id]['text_content'] = text_content
        
        # 返回结束标志
        yield json.dumps({
            "status": 200,
            "data": {
                "answer": "",
                "is_end": 1
            }
        }, ensure_ascii=False) + "\n"
        
        logger.info(f"[{log_id}] Summary generation completed for meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"[{log_id}] Error generating summary: {str(e)}")
        yield json.dumps({
            "status": 500,
            "data": {
                "answer": f"生成会议纪要时出错: {str(e)}",
                "is_end": 1
            }
        }, ensure_ascii=False) + "\n"


def generate_summary_non_stream(log_id: str, text_content: str, meeting_id: str) -> Dict[str, Any]:
    """
    生成会议纪要的非流式响应
    
    Args:
        log_id: 日志ID
        text_content: 会议文本内容
        meeting_id: 会议ID
        
    Returns:
        JSON格式的响应数据
    """
    try:
        prompt = f"""请根据以下会议转写内容，生成一份完整的会议纪要。要求：
1. 提取会议主题
2. 总结主要讨论内容
3. 列出关键决策和行动项
4. 简洁清晰，重点突出

会议转写内容：
{text_content}

请生成会议纪要："""

        messages = [{"role": "user", "content": prompt}]
        
        # 调用LLM进行非流式生成
        answer = call_llm_non_stream(messages)
        
        # 缓存完整的会议纪要
        if meeting_id not in meeting_cache:
            meeting_cache[meeting_id] = {}
        meeting_cache[meeting_id]['summary'] = answer
        meeting_cache[meeting_id]['text_content'] = text_content
        
        logger.info(f"[{log_id}] Summary generation completed for meeting {meeting_id}")
        
        return {
            "status": 200,
            "data": {
                "answer": answer,
                "is_end": 1
            }
        }
        
    except Exception as e:
        logger.error(f"[{log_id}] Error generating summary: {str(e)}")
        return {
            "status": 500,
            "data": {
                "answer": f"生成会议纪要时出错: {str(e)}",
                "is_end": 1
            }
        }


def generate_chat_stream(log_id: str, text_content: str, meeting_id: str, messages: list) -> Generator[str, None, None]:
    """
    生成QA问答的流式响应
    
    Args:
        log_id: 日志ID
        text_content: 会议文本内容
        meeting_id: 会议ID
        messages: 对话历史
        
    Yields:
        JSON格式的响应数据
    """
    try:
        # 获取缓存的会议纪要
        summary = ""
        if meeting_id in meeting_cache and 'summary' in meeting_cache[meeting_id]:
            logger.info(f"[{log_id}] Found cached summary for meeting {meeting_id}")
            summary = meeting_cache[meeting_id]['summary']
        else:
            # 实时生成会议纪要
            logger.info(f"[{log_id}] No cached summary for meeting {meeting_id}, generating summary...")
            summary = generate_summary_non_stream(log_id, text_content, meeting_id)['data']['answer']

        # 构建系统提示词
        system_prompt = f"""你是一个会议助手，请基于以下会议信息回答用户的问题：

会议纪要：
{summary if summary else '暂无会议纪要'}

会议原文：
{text_content}

请根据以上信息回答用户问题，如果信息中没有相关内容，请如实告知。"""

        # 构建完整的消息列表
        full_messages = [{"role": "user", "content": system_prompt}]
        full_messages.extend(messages)
        
        # 调用LLM进行流式生成
        for content in call_llm_stream(full_messages):
            # 返回中间结果
            yield json.dumps({
                "status": 200,
                "data": {
                    "answer": content,
                    "is_end": 0
                }
            }, ensure_ascii=False) + "\n"
        
        # 返回结束标志
        yield json.dumps({
            "status": 200,
            "data": {
                "answer": "",
                "is_end": 1
            }
        }, ensure_ascii=False) + "\n"
        
        logger.info(f"[{log_id}] Chat response completed for meeting {meeting_id}")
        
    except Exception as e:
        logger.error(f"[{log_id}] Error generating chat response: {str(e)}")
        yield json.dumps({
            "status": 500,
            "data": {
                "answer": f"生成回答时出错: {str(e)}",
                "is_end": 1
            }
        }, ensure_ascii=False) + "\n"


def generate_chat_non_stream(log_id: str, text_content: str, meeting_id: str, messages: list) -> Dict[str, Any]:
    """
    生成QA问答的非流式响应
    
    Args:
        log_id: 日志ID
        text_content: 会议文本内容
        meeting_id: 会议ID
        messages: 对话历史
        
    Returns:
        JSON格式的响应数据
    """
    try:
        # 获取缓存的会议纪要
        summary = ""
        if meeting_id in meeting_cache and 'summary' in meeting_cache[meeting_id]:
            logger.info(f"[{log_id}] Found cached summary for meeting {meeting_id}")
            summary = meeting_cache[meeting_id]['summary']
        else:
            # 实时生成会议纪要
            logger.info(f"[{log_id}] No cached summary for meeting {meeting_id}, generating summary...")
            summary = generate_summary_non_stream(log_id, text_content, meeting_id)['data']['answer']
        
        # 构建系统提示词
        system_prompt = f"""你是一个会议助手，请基于以下会议信息回答用户的问题：

会议纪要：
{summary if summary else '暂无会议纪要'}

会议原文：
{text_content}

请根据以上信息回答用户问题，如果信息中没有相关内容，请如实告知。"""

        # 构建完整的消息列表
        full_messages = [{"role": "user", "content": system_prompt}]
        full_messages.extend(messages)
        
        # 调用LLM进行非流式生成
        answer = call_llm_non_stream(full_messages)
        
        logger.info(f"[{log_id}] Chat response completed for meeting {meeting_id}")
        
        return {
            "status": 200,
            "data": {
                "answer": answer,
                "is_end": 1
            }
        }
        
    except Exception as e:
        logger.error(f"[{log_id}] Error generating chat response: {str(e)}")
        return {
            "status": 500,
            "data": {
                "answer": f"生成回答时出错: {str(e)}",
                "is_end": 1
            }
        }


@app.route('/summary', methods=['POST'])
def summary():
    """
    会议纪要生成接口
    """
    try:
        data = request.get_json()
        
        # 参数验证
        log_id = data.get('log_id')
        srt_text = data.get('srt_text') or data.get('src_text')  # 兼容src_text字段
        meeting_id = data.get('meeting_id')
        stream = data.get('stream', False)
        
        if not all([log_id, srt_text, meeting_id]):
            return {
                "status": 400,
                "data": {
                    "answer": "缺少必填参数: log_id, srt_text, meeting_id",
                    "is_end": 1
                }
            }, 400
        
        logger.info(f"[{log_id}] Received summary request for meeting {meeting_id}, stream={stream}")
        
        # 解析SRT文本
        text_content = parse_srt_text(srt_text)
        
        if stream:
            # 流式返回
            return Response(
                stream_with_context(generate_summary_stream(log_id, text_content, meeting_id)),
                content_type='application/json; charset=utf-8'
            )
        else:
            # 非流式返回
            result = generate_summary_non_stream(log_id, text_content, meeting_id)
            return result, result['status']
            
    except Exception as e:
        logger.error(f"Error in summary endpoint: {str(e)}")
        return {
            "status": 500,
            "data": {
                "answer": f"服务器错误: {str(e)}",
                "is_end": 1
            }
        }, 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    会议QA问答接口
    """
    try:
        data = request.get_json()
        
        # 参数验证
        log_id = data.get('log_id')
        srt_text = data.get('srt_text') or data.get('src_text')  # 兼容src_text字段
        meeting_id = data.get('meeting_id')
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        
        if not all([log_id, srt_text, meeting_id]):
            return {
                "status": 400,
                "data": {
                    "answer": "缺少必填参数: log_id, srt_text, meeting_id",
                    "is_end": 1
                }
            }, 400
        
        if not messages:
            return {
                "status": 400,
                "data": {
                    "answer": "messages参数不能为空",
                    "is_end": 1
                }
            }, 400
        
        logger.info(f"[{log_id}] Received chat request for meeting {meeting_id}, stream={stream}")
        
        # 解析SRT文本
        text_content = parse_srt_text(srt_text)
        
        if stream:
            # 流式返回
            return Response(
                stream_with_context(generate_chat_stream(log_id, text_content, meeting_id, messages)),
                content_type='application/json; charset=utf-8'
            )
        else:
            # 非流式返回
            result = generate_chat_non_stream(log_id, text_content, meeting_id, messages)
            return result, result['status']
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {
            "status": 500,
            "data": {
                "answer": f"服务器错误: {str(e)}",
                "is_end": 1
            }
        }, 500


@app.route('/health', methods=['GET'])
def health():
    """
    健康检查接口
    """
    return {
        "status": "ok",
        "cached_meetings": len(meeting_cache)
    }


if __name__ == '__main__':
    logger.info(f"Starting server on {HOST}:{PORT}")
    logger.info(f"LLM Provider: {LLM_PROVIDER}")
    
    if LLM_PROVIDER == 'qianfan':
        logger.info(f"Using Qianfan model: {DEFAULT_MODEL}")
        if not QIANFAN_ACCESS_KEY or not QIANFAN_SECRET_KEY:
            logger.warning("Warning: QIANFAN API keys not configured. Please set them in .env file or environment variables.")
    elif LLM_PROVIDER == 'deepseek':
        logger.info(f"Using DeepSeek model: {DEEPSEEK_MODEL}")
        logger.info(f"DeepSeek API base URL: {DEEPSEEK_BASE_URL}")
        if not DEEPSEEK_API_KEY:
            logger.warning("Warning: DEEPSEEK_API_KEY not configured. Please set it in .env file or environment variables.")
    
    app.run(host=HOST, port=PORT, debug=False)

