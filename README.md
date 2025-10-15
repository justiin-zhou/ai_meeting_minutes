# 会议助手服务

一个支持流式返回的Python服务，提供会议纪要生成和智能问答功能。

## 功能特性

- ✨ 支持流式和非流式两种响应模式
- 📝 自动生成会议纪要
- 💬 基于会议内容的智能问答
- 🔄 会议内容缓存机制
- 📊 支持SRT格式字幕文本解析

## 技术栈

- Flask: Web框架
- LLM支持: 
  - 百度千帆大模型API (ERNIE系列)
  - DeepSeek API (通过OpenAI接口)
- Python 3.8+

## 📚 项目文档

本项目提供完整的技术文档，遵循 Kiro-Workflow 规范：

- 📋 [需求文档](doc/01-requirements.md) - 功能需求、非功能需求、接口规范
- 🏗️ [架构设计文档](doc/02-architecture.md) - 系统架构、技术选型、模块设计
- 📅 [任务规划文档](doc/03-task-planning.md) - 任务分解、里程碑计划、资源规划
- 📖 [文档导航](doc/README.md) - 文档索引和使用指南

## 快速开始

> 💡 **提示**: 详细的快速开始指南请查看 [QUICKSTART.md](QUICKSTART.md)

### 方式一：直接运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp env.example .env
# 编辑 .env 文件，选择 LLM 提供商并配置相应的 API 密钥
# - 使用千帆: 设置 LLM_PROVIDER=qianfan 并填入千帆 API 密钥
# - 使用 DeepSeek: 设置 LLM_PROVIDER=deepseek 并填入 DeepSeek API 密钥

# 3. 启动服务
python src/run_server.py
```

### 方式二：使用启动脚本

```bash
chmod +x start.sh
./start.sh
```

### 方式三：Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 或直接使用 Docker
docker build -t meeting-assistant .
docker run -p 8000:8000 \
  -e QIANFAN_ACCESS_KEY=你的key \
  -e QIANFAN_SECRET_KEY=你的secret \
  meeting-assistant
```

服务将在 `http://0.0.0.0:8000` 启动。

## API 接口

### 1. 会议纪要生成 - POST /summary

根据会议转写内容，生成会议纪要。

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| log_id | string | 是 | 日志ID |
| srt_text | string | 是 | 会议转写文本（SRT格式） |
| meeting_id | string | 是 | 会议ID，用于缓存 |
| stream | bool | 是 | 是否采用流式返回 |

**请求示例:**

```bash
curl --location 'http://localhost:8000/summary' \
--header 'Content-Type: application/json' \
--data '{
  "log_id": "123456",
  "srt_text": "1\n00:00:01,000 --> 00:00:03,000\n你好，世界！\n\n2\n00:00:04,500 --> 00:00:06,000\n这是第二行字幕。\n\n",
  "meeting_id": "123456",
  "stream": true
}'
```

**响应示例:**

流式返回（每行一个JSON）：
```json
{"status": 200, "data": {"answer": "会议主题：\n", "is_end": 0}}
{"status": 200, "data": {"answer": "你好世界...", "is_end": 0}}
{"status": 200, "data": {"answer": "", "is_end": 1}}
```

非流式返回：
```json
{"status": 200, "data": {"answer": "会议主题：\n你好世界...", "is_end": 1}}
```

### 2. 会议问答 - POST /chat

基于会议纪要的智能问答。

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| log_id | string | 是 | 日志ID |
| srt_text | string | 是 | 会议转写文本（SRT格式） |
| meeting_id | string | 是 | 会议ID，用于缓存 |
| messages | list[dict] | 是 | 对话历史 |
| stream | bool | 是 | 是否采用流式返回 |

**请求示例:**

```bash
curl --location 'http://localhost:8000/chat' \
--header 'Content-Type: application/json' \
--data '{
    "log_id": "123456",
    "srt_text": "1\n00:00:01,000 --> 00:00:03,000\n你好，世界！\n\n2\n00:00:04,500 --> 00:00:06,000\n这是第二行字幕。\n\n",
    "meeting_id": "123456",
    "messages": [
        {
            "role": "user",
            "content": "会议主要讨论了什么？"
        }
    ],
    "stream": true
}'
```

**响应示例:**

流式返回（每行一个JSON）：
```json
{"status": 200, "data": {"answer": "根据会议", "is_end": 0}}
{"status": 200, "data": {"answer": "内容...", "is_end": 0}}
{"status": 200, "data": {"answer": "", "is_end": 1}}
```

### 3. 健康检查 - GET /health

检查服务状态。

**请求示例:**

```bash
curl http://localhost:8000/health
```

**响应示例:**

```json
{
  "status": "ok",
  "cached_meetings": 5
}
```

## 数据格式说明

### SRT格式示例

```
1
00:00:01,000 --> 00:00:03,000
你好，世界！

2
00:00:04,500 --> 00:00:06,000
这是第二行字幕。
```

### 对话历史格式

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮助你的吗？"
    },
    {
      "role": "user",
      "content": "会议主要讨论了什么？"
    }
  ]
}
```

## 缓存机制

服务会自动缓存每个会议的纪要和原文：
- 使用 `meeting_id` 作为唯一标识
- 首次调用 `/summary` 时生成并缓存会议纪要
- `/chat` 接口会优先使用缓存的会议纪要来回答问题
- 缓存在服务重启后会清空

## 注意事项

1. 需要配置有效的千帆API密钥才能正常使用
2. 流式返回时，每行是一个独立的JSON对象
3. `is_end=1` 表示响应结束
4. 请求参数中 `srt_text` 和 `src_text` 字段均支持（向后兼容）

## 开发说明

### 目录结构

```
meeting_assistant/
├── requirements.txt      # 项目依赖
├── env.example          # 环境变量示例（通用）
├── env.qianfan.example  # 千帆配置示例
├── env.deepseek.example # DeepSeek配置示例
├── README.md            # 项目说明
├── QUICKSTART.md        # 快速开始指南
├── LLM_COMPARISON.md    # LLM提供商对比指南
├── config.py            # 配置文件
├── Dockerfile           # Docker镜像构建文件
├── docker-compose.yml   # Docker Compose配置
├── start.sh             # 启动脚本
├── test_api.py          # API测试脚本
├── test_qianfan.py      # 千帆配置测试
├── test_deepseek.py     # DeepSeek配置测试
├── example_client.py    # 客户端使用示例
├── CHANGELOG.md         # 更新日志
├── .gitignore           # Git忽略文件
└── src/
    └── run_server.py    # 服务主程序
```

### 日志

服务会输出详细的运行日志，包括：
- 请求接收
- 处理进度
- 错误信息

## 测试

### 运行API测试

```bash
python test_api.py
```

测试脚本会自动测试：
- 健康检查接口
- 流式和非流式会议纪要生成
- 流式和非流式会议问答
- 多轮对话功能

### 客户端使用示例

项目提供了完整的Python客户端示例：

```bash
python example_client.py
```

示例代码展示了：
- 如何封装客户端类
- 非流式调用
- 流式调用
- 单轮和多轮对话
- 错误处理

### LLM 配置测试

在启动服务前，可以先测试 LLM API 配置是否正确：

**测试千帆配置：**
```bash
python test_qianfan.py
```

**测试 DeepSeek 配置：**
```bash
python test_deepseek.py
```

这些测试脚本会验证：
- API 密钥是否正确
- 网络连接是否正常
- 模型调用是否成功
- 流式和非流式调用

## 生产环境部署

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 120 src.run_server:app
```

### 性能建议

- 根据CPU核心数调整 Gunicorn 的 worker 数量（建议 2-4 * CPU核心数）
- 设置合理的超时时间（建议 120-300 秒）
- 使用 Nginx 作为反向代理
- 启用 HTTPS 加密传输
- 配置日志轮转避免日志文件过大

## LLM 提供商配置

服务支持两种 LLM 提供商，通过 `LLM_PROVIDER` 环境变量配置。

> 💡 **详细对比**: 查看 [LLM_COMPARISON.md](LLM_COMPARISON.md) 了解两种提供商的详细对比和选择建议

### 使用百度千帆（默认）

在 `.env` 文件中配置：
```bash
LLM_PROVIDER=qianfan
QIANFAN_ACCESS_KEY=你的AccessKey
QIANFAN_SECRET_KEY=你的SecretKey
DEFAULT_MODEL=ERNIE-4.0-8K  # 可选: ERNIE-3.5-8K, ERNIE-Speed-8K
```

获取千帆 API 密钥：访问 [百度智能云控制台](https://console.bce.baidu.com/)

### 使用 DeepSeek

在 `.env` 文件中配置：
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的DeepSeekAPIKey
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat  # 或 deepseek-coder
```

获取 DeepSeek API 密钥：访问 [DeepSeek 开放平台](https://platform.deepseek.com/)

## 常见问题

### Q1: 如何切换 LLM 提供商？

在 `.env` 文件中修改 `LLM_PROVIDER`：
- 使用千帆: `LLM_PROVIDER=qianfan`
- 使用 DeepSeek: `LLM_PROVIDER=deepseek`

然后重启服务即可。

### Q2: DeepSeek 和千帆有什么区别？

- **千帆**: 百度自研的文心大模型，中文能力强，支持多种模型规格
- **DeepSeek**: 深度求索开源模型，性价比高，支持代码生成

### Q3: 如何修改使用的AI模型？

**千帆模型**（在 `.env` 文件中设置 `DEFAULT_MODEL`）：
- `ERNIE-4.0-8K` - 文心4.0，能力最强
- `ERNIE-3.5-8K` - 文心3.5，性价比高
- `ERNIE-Speed-8K` - 速度优先

**DeepSeek模型**（在 `.env` 文件中设置 `DEEPSEEK_MODEL`）：
- `deepseek-chat` - 通用对话模型
- `deepseek-coder` - 代码专用模型

### Q4: 如何处理长文本会议？

服务会自动解析SRT格式文本。对于超长会议，建议：
1. 分段调用 `/summary` 接口
2. 使用 `meeting_id` 管理不同会议的缓存

### Q5: 缓存数据何时清除？

当前版本使用内存缓存，服务重启后会清空。生产环境建议使用 Redis 等持久化方案。

## 许可证

MIT

