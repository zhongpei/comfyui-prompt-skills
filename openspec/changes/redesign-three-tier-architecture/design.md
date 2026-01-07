# 技术设计文档: 三层解耦架构重构

## Context

### 背景

根据 `agent-docs/设计v2.md` 的深度研究报告，现有架构存在本质缺陷：

1. **状态持久化缺失**：节点生命周期仅限于一次"Queue Prompt"执行过程
2. **交互性的单向壁垒**：缺乏双向、低延迟的通信通道
3. **测试的紧耦合困境**：必须启动整个ComfyUI才能测试业务逻辑

### 约束

- ComfyUI Frontend V2 基于 Vue.js 3（参考 `comfyui_v2.md`）
- OpenCode Server 暴露 REST API（参考 `opencode_api.md`）
- Flask 服务必须在独立守护线程中运行，避免阻塞ComfyUI主进程

### 利益相关者

- **最终用户**：需要实时看到LLM思考过程
- **开发者**：需要独立测试能力
- **运维**：需要服务可观测性

---

## Goals / Non-Goals

### Goals

1. 实现前端与业务逻辑的彻底解耦
2. 支持WebSocket双向实时通信
3. 确保逻辑层可独立测试（无需ComfyUI）
4. 支持多角色Skills并发执行

### Non-Goals

1. 不实现分布式Opencode Core部署（保持单机模式）
2. 不支持WebSocket之外的通信协议
3. 不实现前端的SSR渲染

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tier 1: ComfyUI Node (Vue Container)         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Vue.js 3 App (Vite Build)                                   ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐││
│  │  │ Session ID  │  │ Skills Multi │  │ Chat Interface       │││
│  │  │ Selector    │  │ Selection    │  │ (Stream Display)     │││
│  │  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘││
│  │         └────────────────┼─────────────────────┘             ││
│  │                          │ WebSocket (socket.io-client)       ││
│  └──────────────────────────┼───────────────────────────────────┘│
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tier 2: Logic Layer (Flask + SocketIO)        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Flask App (Daemon Thread)                                   ││
│  │  ├── WebSocket Event Handlers                                ││
│  │  │   ├── connect → join_room(session_id)                    ││
│  │  │   ├── configure → update api_key, skills                 ││
│  │  │   ├── user_message → forward to Core                     ││
│  │  │   └── disconnect → cleanup                               ││
│  │  ├── Room-based Session Isolation                            ││
│  │  └── Pytest Test Interface (/test/*)                         ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │ Python Call                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tier 3: Opencode Core (Business Service)      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Singleton SessionManager                                    ││
│  │  _global_sessions = {                                        ││
│  │      "session_id_A": {                                       ││
│  │          "history": [...],                                   ││
│  │          "skills": ["z-photo", "z-manga"],                   ││
│  │          "config": {...},                                    ││
│  │      }                                                       ││
│  │  }                                                           ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │                                       │
│  ┌───────────────────────▼─────────────────────────────────────┐│
│  │  Skill Registry (Dynamic Loading)                            ││
│  │  ├── z-photo (Photography Expert)                            ││
│  │  ├── z-manga (Anime/Manga Expert)                            ││
│  │  └── z-hanfu (Chinese Traditional Style)                     ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │ HTTP                                  │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  OpenCode Server (http://127.0.0.1:4096)                     ││
│  │  Sessions, Messages, Tools API                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Decisions

### Decision 1: Flask独立守护线程

**决定**：Flask服务在ComfyUI加载自定义节点时启动为守护线程

**实现**：
```python
# __init__.py (ComfyUI入口)
import threading
from backend.logic.app import create_app, socketio

def run_flask_service():
    app = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)

# 启动独立线程
threading.Thread(target=run_flask_service, daemon=True).start()
```

**理由**：
- 不阻塞ComfyUI主线程
- 守护线程随ComfyUI退出自动退出
- 独立端口支持跨进程访问

### Decision 2: WebSocket Room机制

**决定**：使用Flask-SocketIO的Room功能实现会话隔离

**事件路由表**：

| 事件名称 | 方向 | 携带数据 | 处理逻辑 |
|---------|------|---------|---------|
| `connect` | Vue → Flask | session_id | 建立连接，加入Room |
| `configure` | Vue → Flask | api_key, skills | 更新配置，持久化到Session |
| `user_message` | Vue → Flask | prompt, attachments | 调用Core执行，流式推送 |
| `stream_delta` | Flask → Vue | delta, index | LLM生成的流式文本 |
| `debug_log` | Flask → Vue | level, message | 调试信息（Chain of Thought） |
| `sync_state` | Flask → Vue | history, status | 重连时恢复状态 |

### Decision 3: Vue Widget劫持

**决定**：通过`app.registerExtension`劫持ComfyUI节点DOM，挂载Vue应用

**实现**：
```javascript
// 在nodeCreated钩子中
app.registerExtension({
    name: "PromptSkills.VueContainer",
    async nodeCreated(node, app) {
        if (node.comfyClass === "OpencodeContainerNode") {
            const container = document.createElement("div");
            node.addDOMWidget("vue_app", "div", container);
            createApp(App).mount(container);
        }
    }
});
```

**理由**：
- 利用ComfyUI的Widget持久化机制保存配置
- Vue应用完全控制UI渲染
- 符合Frontend V2标准

### Decision 4: 独立测试策略

**决定**：逻辑层使用pytest-flask进行独立测试

**测试架构**：
```python
# tests/conftest.py
import pytest
from backend.logic.app import create_app, socketio

@pytest.fixture
def app():
    app = create_app(debug=True, testing=True)
    return app

@pytest.fixture
def socket_client(app):
    return socketio.test_client(app)
```

**理由**：
- 无需ComfyUI环境即可测试
- Mock Opencode Core返回值
- CI/CD友好

---

## Data Structures

### WebSocket协议Schema

**前端 → 后端**：
```json
{
  "event": "user_message",
  "data": {
    "session_id": "UUID-v4",
    "content": "一个穿着红色汉服的女孩在樱花树下",
    "model_target": "z-image-turbo",
    "active_skills": ["z-photo", "z-hanfu"]
  }
}
```

**后端 → 前端**：
```json
{
  "event": "stream_delta",
  "data": {
    "session_id": "UUID-v4",
    "delta": " cinematic",
    "index": 12
  }
}
```

---

## File Structure

```
custom_nodes/comfyui-prompt-skills/
├── __init__.py                    # 启动Flask线程 + 注册节点
├── nodes/
│   └── container_node.py          # Tier 1: 纯容器节点 (无业务逻辑)
├── backend/
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── app.py                 # Tier 2: Flask应用工厂
│   │   ├── socket_handlers.py     # WebSocket事件处理器
│   │   └── routes.py              # HTTP测试路由
│   └── core/
│       ├── __init__.py
│       ├── session_manager.py     # Tier 3: 全局Session单例
│       ├── skill_registry.py      # 技能注册中心
│       ├── opencode_client.py     # OpenCode Server客户端
│       └── output_formatter.py    # 输出格式化器
├── web/
│   ├── src/
│   │   ├── main.js                # Vue入口
│   │   ├── App.vue                # 主组件
│   │   └── components/
│   │       ├── ChatPanel.vue      # 聊天面板
│   │       ├── SkillSelector.vue  # 技能多选
│   │       └── DebugPanel.vue     # 调试信息面板
│   ├── vite.config.js             # Vite配置 (输出到js/)
│   └── package.json
├── js/                            # Vite构建产物 (WEB_DIRECTORY)
│   └── opencode-vue.es.js
├── skills/                        # 技能文件
├── data/                          # 风格库
├── tests/
│   ├── conftest.py
│   ├── test_socket_handlers.py    # 逻辑层独立测试
│   └── test_session_manager.py    # 核心层单元测试
└── requirements.txt
```

---

## Risks / Trade-offs

### Risk 1: Flask线程资源竞争

**风险**：Flask与ComfyUI主线程共享GIL

**缓解**：
- WebSocket使用eventlet/gevent异步模式
- 重CPU操作提交到ThreadPoolExecutor

### Risk 2: Vue组件Z-Index冲突

**风险**：DOM层覆盖Canvas导致事件穿透

**缓解**：
- 使用`<Teleport>`将浮动层渲染到body
- 正确设置pointer-events

### Risk 3: 前后端版本不一致

**风险**：Vite构建产物与后端协议不匹配

**缓解**：
- 协议版本号校验
- 连接时检查client_version

---

## Migration Plan

### 从旧版迁移

1. 备份现有 `comfyui-prompt-skills_old/` 目录
2. 删除旧节点，安装新版插件
3. 重新配置Session和API Key（通过Vue界面）
4. 现有风格库JSON可直接复用

### 回滚计划

- 保留 `comfyui-prompt-skills_old/` 作为回退选项
- 新旧版本可共存（使用不同端口）

---

## Open Questions

1. **Q: 是否需要支持多个ComfyUI实例共享Session？**
   - 当前设计每个ComfyUI实例独立Session

2. **Q: WebSocket断线重连策略？**
   - 建议使用socket.io内置的重连机制
   - 重连后通过`sync_state`恢复状态

3. **Q: 是否需要持久化Session到磁盘？**
   - 当前设计为内存存储，ComfyUI重启后丢失
   - 可扩展为SQLite/JSON文件持久化

---

## References

- [设计v2.md](file:///Users/fofo/Work/comfyui-prompt-skills/agent-docs/设计v2.md) - 三层架构详细设计
- [comfyui_v2.md](file:///Users/fofo/Work/comfyui-prompt-skills/agent-docs/comfyui_v2.md) - ComfyUI Frontend V2指南
- [opencode_api.md](file:///Users/fofo/Work/comfyui-prompt-skills/agent-docs/opencode_api.md) - OpenCode Server API规范
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [ComfyUI JavaScript Extensions](https://docs.comfy.org/custom-nodes/js/javascript_overview)
