# ComfyUI Prompt Skills - 三层解耦架构 v2.0

基于三层服务架构（Three-Tier SOA）的智能提示词生成插件。

## 架构概览

```
┌─────────────────────────────────────────┐
│  Tier 1: Vue Container (ComfyUI Node)   │
│  - 纯UI渲染，无业务逻辑                  │
│  - WebSocket连接到Logic Layer           │
└──────────────────┬──────────────────────┘
                   │ WebSocket
                   ▼
┌─────────────────────────────────────────┐
│  Tier 2: Logic Layer (Flask + SocketIO) │
│  - 消息路由、会话隔离                   │
│  - 支持独立测试                         │
└──────────────────┬──────────────────────┘
                   │ Python
                   ▼
┌─────────────────────────────────────────┐
│  Tier 3: Opencode Core                  │
│  - SessionManager (全局状态)             │
│  - SkillRegistry (技能加载)              │
│  - OpencodeClient (HTTP通信)            │
└─────────────────────────────────────────┘
```

## 安装

### 1. Python 依赖

```bash
cd custom_nodes/comfyui-prompt-skills
pip install -e .
```

或使用 uv:

```bash
uv pip install -e .
```

### 2. 构建 Vue 前端

```bash
cd web
npm install
npm run build
```

### 3. 安装 OpenCode CLI

```bash
npm install -g opencode
```

### 4. 配置 OpenCode (Z.AI GLM Coding Plan)

本项目默认配置使用 Z.AI 的 GLM Coding Plan。请在项目根目录使用提供的 `opencode.json` 文件。

**opencode.json**:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "zai": {}
  },
  "model": "zai/glm-4.7"
}
```

**连接 Z.AI**:

1. 获取 API Key: [Z.AI API Console](https://z.ai/manage-apikey/apikey-list)
2. 连接账号:
   ```bash
   opencode /connect
   # 选择 Z.AI -> 输入 API Key
   ```
3. 验证模型:
   ```bash
   opencode /models
   # 确认可以看到 glm-4.7
   ```

## 使用方法

1. 在 ComfyUI 中添加 **Prompt Skills Generator** 节点
2. 在节点界面中选择技能（Skills）
3. 输入描述文字，点击发送
4. 实时查看生成过程和输出

## 技能列表

- **z-photo**: 摄影写实专家
- **z-manga**: 二次元动漫专家
- **z-hanfu**: 汉服中国风专家

## 开发

### 运行测试

```bash
cd custom_nodes/comfyui-prompt-skills
pytest tests/ -v
```

### 目录结构

```
comfyui-prompt-skills/
├── __init__.py              # Flask启动 + 节点注册
├── backend/
│   ├── logic/               # Tier 2: Flask + SocketIO
│   └── core/                # Tier 3: Session, Skills, Client
├── web/                     # Vue.js 源代码
├── js/                      # Vite构建产物
├── nodes/                   # ComfyUI节点定义
├── skills/                  # 技能文件
├── data/                    # 风格库
└── tests/                   # 测试套件
```

## API 端点

- `GET /health` - 健康检查
- `GET /api/sessions` - 列出会话
- `GET /api/skills` - 列出技能

## WebSocket 事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `connect` | Client → Server | 建立连接 |
| `configure` | Client → Server | 更新配置 |
| `user_message` | Client → Server | 发送消息 |
| `stream_delta` | Server → Client | 流式响应 |
| `debug_log` | Server → Client | 调试日志 |
| `complete` | Server → Client | 生成完成 |

## License

GPL-3.0
