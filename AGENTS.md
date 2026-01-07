<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

---

# ComfyUI Prompt Skills - 项目指南 (v2.0)

## 项目概述

这是一个 **ComfyUI 智能提示词生成插件**，基于 **三层解耦架构（Three-Tier SOA）** 实现，通过 WebSocket 实时通信与 OpenCode Server 集成。

### 核心价值

1. **三层解耦**：Display (Vue) / Logic (Flask) / Core (Python) 完全分离
2. **实时通信**：WebSocket 实现流式响应和 CoT 调试日志
3. **独立测试**：Flask 层可独立于 ComfyUI 进行集成测试
4. **技能封装**：将提示词工程知识封装为可复用的"技能（Skills）"

## 项目状态：✅ v2.0 完成

- **38 个测试通过**（18 单元测试 + 20 集成测试）
- **三层架构**：Tier 1 Vue / Tier 2 Flask-SocketIO / Tier 3 Core
- **OpenSpec 验证**：`redesign-three-tier-architecture` 已通过

---

## 架构概览

```
┌─────────────────────────────────────────┐
│  Tier 1: Vue Container (ComfyUI Node)   │
│  - 纯UI渲染，无业务逻辑                  │
│  - WebSocket 连接到 Logic Layer         │
└──────────────────┬──────────────────────┘
                   │ WebSocket (socket.io)
                   ▼
┌─────────────────────────────────────────┐
│  Tier 2: Logic Layer (Flask + SocketIO) │
│  - 消息路由、会话隔离（Rooms）           │
│  - 独立测试（pytest-flask）              │
└──────────────────┬──────────────────────┘
                   │ Python calls
                   ▼
┌─────────────────────────────────────────┐
│  Tier 3: Opencode Core                  │
│  - SessionManager (全局状态)             │
│  - SkillRegistry (技能加载)              │
│  - OpencodeClient (HTTP 通信)           │
│  - OutputFormatter (输出格式化)          │
└─────────────────────────────────────────┘
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **Tier 1** | Vue.js 3, Vite, socket.io-client |
| **Tier 2** | Flask 3.0, Flask-SocketIO |
| **Tier 3** | Python 3.10+, httpx |
| **External** | OpenCode Server (REST API) |
| **Target Models** | Z-Image Turbo, SDXL |

---

## 目录结构

```
custom_nodes/comfyui-prompt-skills/
├── __init__.py                    # Flask 启动 + 节点注册
├── pyproject.toml                 # Python 依赖配置
├── Makefile                       # 构建/测试/部署命令
├── install.sh                     # 安装脚本
├── backend/
│   ├── core/                      # Tier 3: 业务逻辑
│   │   ├── session_manager.py     # 全局会话管理（单例）
│   │   ├── skill_registry.py      # 技能发现与加载
│   │   ├── opencode_client.py     # OpenCode Server HTTP 客户端
│   │   └── output_formatter.py    # 输出格式化器
│   └── logic/                     # Tier 2: 逻辑层
│       ├── app.py                 # Flask 应用工厂
│       ├── socket_handlers.py     # WebSocket 事件处理器
│       └── routes.py              # HTTP 测试端点
├── web/                           # Tier 1: Vue.js 源码
│   ├── src/
│   │   ├── App.vue                # 主组件
│   │   └── components/
│   │       ├── ChatPanel.vue      # 聊天面板（流式显示）
│   │       ├── SkillSelector.vue  # 技能多选
│   │       └── DebugPanel.vue     # CoT 调试日志
│   └── vite.config.js             # Vite 构建配置
├── js/                            # Vite 构建输出
│   └── extension.js               # ComfyUI JS 扩展
├── nodes/
│   └── container_node.py          # OpencodeContainerNode（哑节点）
├── skills/                        # 技能文件
├── data/                          # 风格库
└── tests/                         # 测试套件
    ├── test_session_manager.py    # 单元测试
    ├── test_socket_handlers.py    # Flask 层测试
    └── test_integration.py        # 集成测试
```

---

## 构建与部署

```bash
cd custom_nodes/comfyui-prompt-skills

# 开发环境
make dev-setup        # 安装依赖 + 构建 Vue

# 测试
make test             # 单元测试 (18个, 快速)
make test-integration # 集成测试 (20个, 启动 OpenCode Server)
make test-all         # 全部测试

# 打包与部署
make package          # 构建 Python wheel
make dist             # 创建发布包 (dist/deploy/)
make deploy           # 同步到远程服务器
```

---

## WebSocket 事件协议

### 客户端 → 服务器

| 事件 | 数据 | 说明 |
|------|------|------|
| `connect` | `?session_id=xxx` | 建立连接，加入 Room |
| `configure` | `{session_id, active_skills[], api_key}` | 更新配置 |
| `user_message` | `{session_id, content, model_target}` | 发送消息 |
| `list_skills` | `{session_id}` | 获取技能列表 |
| `abort` | `{session_id}` | 中止生成 |

### 服务器 → 客户端

| 事件 | 数据 | 说明 |
|------|------|------|
| `sync_state` | `{history[], status, skills[]}` | 状态同步 |
| `stream_delta` | `{delta, index}` | 流式文本 |
| `debug_log` | `{level, module, message}` | CoT 日志 |
| `complete` | `{prompt_english, prompt_json, prompt_bilingual}` | 生成完成 |
| `status_update` | `{status}` | 状态变更 |
| `error` | `{message}` | 错误信息 |

---

## OpenCode Server API

| 操作 | 方法 | 端点 |
|------|------|------|
| 获取配置 | GET | `/config` |
| 列出会话 | GET | `/session` |
| 创建会话 | POST | `/session` |
| 发送消息 | POST | `/session/{id}/message` |
| 获取消息 | GET | `/session/{id}/message` |

### 消息格式

```json
{
  "parts": [
    {"type": "text", "text": "消息内容"}
  ],
  "system": "可选系统提示词"
}
```

---

## 测试策略

| 层级 | 测试类型 | 数量 | 说明 |
|------|----------|------|------|
| Tier 3 Core | 单元测试 | 12 | SessionManager, SkillRegistry 等 |
| Tier 2 Logic | Flask 测试 | 6 | WebSocket + HTTP 端点 |
| Integration | 集成测试 | 20 | 真实 OpenCode Server 调用 |

```bash
# 集成测试自动管理 OpenCode Server 生命周期
make test-integration
```

---

## 代码规范

- **Python**: 类型标注, httpx (同步), Flask-SocketIO
- **Vue**: Composition API, socket.io-client
- **命名**: PascalCase (类), snake_case (函数/变量)
- **日志**: 使用 `debug_log` 事件推送 CoT 到前端

---

## 参考文档

- [三层架构设计](agent-docs/设计v2.md)
- [OpenCode API 规范](agent-docs/opencode_api.md)
- [ComfyUI 开发指南](agent-docs/comfyui_v2.md)
- [OpenSpec 变更: redesign-three-tier-architecture](openspec/changes/redesign-three-tier-architecture/)