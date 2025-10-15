# 快速开始指南

## 1. 环境准备

### 系统要求
- Python 3.8 或更高版本
- pip 包管理器

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 2. 配置LLM提供商和API密钥

服务支持两种 LLM 提供商：**百度千帆** 和 **DeepSeek**。选择其中一个进行配置。

### 选项一：使用百度千帆（默认）

#### 获取千帆API密钥

1. 访问 [百度智能云控制台](https://console.bce.baidu.com/)
2. 开通千帆大模型平台服务
3. 创建应用获取 Access Key 和 Secret Key

#### 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# LLM提供商
LLM_PROVIDER=qianfan

# 千帆API配置
QIANFAN_ACCESS_KEY=你的AccessKey
QIANFAN_SECRET_KEY=你的SecretKey

# 服务配置
HOST=0.0.0.0
PORT=8000
DEFAULT_MODEL=ERNIE-4.0-8K
LOG_LEVEL=INFO
```

### 选项二：使用 DeepSeek

#### 获取 DeepSeek API密钥

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账号并创建 API Key

#### 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# LLM提供商
LLM_PROVIDER=deepseek

# DeepSeek API配置
DEEPSEEK_API_KEY=你的DeepSeekAPIKey
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 服务配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 快捷配置

也可以直接复制示例文件：

```bash
cp env.example .env
# 然后编辑 .env 文件，填入相应的配置
```

## 3. 启动服务

### 方法一：使用启动脚本（推荐）

```bash
chmod +x start.sh
./start.sh
```

### 方法二：直接启动

```bash
python src/run_server.py
```

服务将在 `http://0.0.0.0:8000` 启动。

## 4. 测试服务

### 检查服务状态

```bash
curl http://localhost:8000/health
```

### 测试会议纪要生成

```bash
curl --location 'http://localhost:8000/summary' \
--header 'Content-Type: application/json' \
--data '{
  "log_id": "test_001",
  "srt_text": "1\n00:00:01,000 --> 00:00:03,000\n大家好，欢迎参加今天的产品讨论会。\n\n2\n00:00:04,500 --> 00:00:08,000\n今天我们主要讨论新版本的功能规划。\n\n",
  "meeting_id": "test_meeting",
  "stream": true
}'
```

### 测试会议问答

```bash
curl --location 'http://localhost:8000/chat' \
--header 'Content-Type: application/json' \
--data '{
    "log_id": "test_002",
    "srt_text": "1\n00:00:01,000 --> 00:00:03,000\n大家好，欢迎参加今天的产品讨论会。\n\n",
    "meeting_id": "test_meeting",
    "messages": [
        {
            "role": "user",
            "content": "会议主要讨论了什么？"
        }
    ],
    "stream": false
}'
```

### 运行完整测试套件

```bash
python test_api.py
```

## 5. 使用示例

### Python 客户端示例

```python
import requests
import json

# 流式调用示例
def test_stream_summary():
    data = {
        "log_id": "client_001",
        "srt_text": "你的SRT格式文本",
        "meeting_id": "meeting_001",
        "stream": True
    }
    
    response = requests.post(
        "http://localhost:8000/summary",
        json=data,
        stream=True
    )
    
    # 处理流式响应
    for line in response.iter_lines():
        if line:
            result = json.loads(line.decode('utf-8'))
            print(result['data']['answer'], end='', flush=True)
            
            if result['data']['is_end'] == 1:
                print("\n完成！")
                break

# 非流式调用示例
def test_non_stream_chat():
    data = {
        "log_id": "client_002",
        "srt_text": "你的SRT格式文本",
        "meeting_id": "meeting_001",
        "messages": [
            {"role": "user", "content": "会议主要内容是什么？"}
        ],
        "stream": False
    }
    
    response = requests.post("http://localhost:8000/chat", json=data)
    result = response.json()
    print(result['data']['answer'])

if __name__ == "__main__":
    test_stream_summary()
    test_non_stream_chat()
```

### curl 流式调用示例

```bash
# 流式调用会议纪要
curl -N --location 'http://localhost:8000/summary' \
--header 'Content-Type: application/json' \
--data '{
  "log_id": "123",
  "srt_text": "1\n00:00:01,000 --> 00:00:03,000\n会议内容...\n\n",
  "meeting_id": "meeting_123",
  "stream": true
}'
```

## 6. 常见问题

### Q: 服务启动报错 "qianfan" 或 "openai" 模块未找到
A: 请确保已安装依赖：`pip install -r requirements.txt`

### Q: API 调用返回认证错误
A: 请检查 `.env` 文件中的 API 密钥是否正确配置
- 使用千帆: 检查 `QIANFAN_ACCESS_KEY` 和 `QIANFAN_SECRET_KEY`
- 使用 DeepSeek: 检查 `DEEPSEEK_API_KEY`

### Q: 如何在千帆和 DeepSeek 之间切换？
A: 在 `.env` 文件中修改 `LLM_PROVIDER` 的值：
- 使用千帆: `LLM_PROVIDER=qianfan`
- 使用 DeepSeek: `LLM_PROVIDER=deepseek`

修改后重启服务即可。

### Q: DeepSeek 的优势是什么？
A: 
- 成本更低：相比商业API，DeepSeek性价比更高
- 开源透明：模型开源，可自部署
- 代码能力强：特别是 deepseek-coder 模型

### Q: 千帆的优势是什么？
A: 
- 中文能力强：文心大模型针对中文优化
- 稳定可靠：百度云服务支持
- 多种规格：可根据需求选择不同模型

### Q: 流式响应没有正常显示
A: 使用 curl 时添加 `-N` 参数禁用缓冲，Python 中使用 `stream=True`

### Q: 如何修改服务端口
A: 在 `.env` 文件中设置 `PORT=你的端口号`

## 7. 生产环境部署

### 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务（4个工作进程）
gunicorn -w 4 -b 0.0.0.0:8000 src.run_server:app
```

### 使用 Docker

```bash
# 构建镜像
docker build -t meeting-assistant .

# 运行容器
docker run -p 8000:8000 \
  -e QIANFAN_ACCESS_KEY=你的key \
  -e QIANFAN_SECRET_KEY=你的secret \
  meeting-assistant
```

## 8. 性能优化建议

1. **启用缓存**: 服务已内置会议缓存机制，相同 `meeting_id` 会复用已生成的纪要
2. **调整工作进程**: 根据服务器配置调整 gunicorn 的工作进程数
3. **使用 Redis**: 对于分布式部署，建议使用 Redis 替代内存缓存
4. **限流控制**: 添加请求限流避免API配额超限

## 9. 监控和日志

### 查看日志

```bash
# 默认输出到控制台
# 可以通过环境变量调整日志级别
export LOG_LEVEL=DEBUG
python src/run_server.py
```

### 监控指标

- 通过 `/health` 接口查看服务状态和缓存数量
- 建议集成 Prometheus + Grafana 进行生产监控

## 10. 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 查看 [API 文档](README.md#api-接口) 了解接口详情
- 运行 `test_api.py` 查看更多使用示例

