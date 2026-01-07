# Change: 重构为三层解耦架构 (Redesign Three-Tier Architecture)

## Why

现有的 `comfyui-prompt-skills_old` 实现存在以下架构缺陷：

1. **紧耦合设计**：Python后端直接通过同步HTTP调用OpenCode Server，无法实现真正的解耦
2. **缺乏实时交互**：无法实现LLM流式输出的实时显示（Chain of Thought调试）
3. **状态管理缺失**：节点执行完毕后会话状态丢失，无法实现持久化上下文
4. **测试困难**：业务逻辑与ComfyUI框架高度耦合，难以独立测试

根据 `设计v2.md` 设计文档，采用**三层服务架构（Three-Tier SOA）**进行重构，实现前后端彻底解耦。

## What Changes

### **BREAKING** 架构变更

- **Tier 1 (展示层)**: ComfyUI节点退化为"纯Vue容器"
  - 仅负责UI渲染、配置持久化（Widget劫持）
  - 不含任何业务逻辑
  - 使用Vue.js 3 + Vite构建前端组件

- **Tier 2 (逻辑层)**: 新增Flask Logic Layer
  - 独立的Flask子服务（守护线程运行）
  - WebSocket双向通信（Flask-SocketIO）
  - 消息路由、请求校验、独立测试接口
  - 支持Pytest独立集成测试

- **Tier 3 (核心层)**: Opencode Core业务层
  - 全局Session状态管理（单例模式）
  - 多角色技能调度（动态Skill加载）
  - LLM交互、持久化存储
  - 与前端完全解耦

### 新增功能

- **WebSocket实时通信**：
  - `stream_delta`事件支持LLM打字机效果
  - `debug_log`事件支持调试信息显示
  - `sync_state`事件支持重连状态恢复

- **多角色并发**：
  - 支持多选Skills同时激活
  - Room机制实现会话隔离
  - 异步执行模型（ThreadPoolExecutor）

- **独立测试能力**：
  - Flask层支持独立集成测试（无需ComfyUI环境）
  - 使用Mock对象模拟Opencode Core

### 废弃功能

- 移除直接HTTP同步调用模式
- 移除节点内的业务逻辑代码

## Impact

- **Affected specs**:
  - `core-plugin` (重大修改) - 架构重构为三层
  - `opencode-integration` (重大修改) - 改为WebSocket通信
  - `skills-engine` (新增) - 多角色并发调度
  - `vue-frontend` (新增) - Vue.js 3前端组件

- **Affected code**:
  - `custom_nodes/comfyui-prompt-skills/` - 完全重构
  - `backend/` - 新增Flask/Core层
  - `web/` - 新增Vue.js项目
  - `tests/` - 新增独立测试套件

- **Dependencies**:
  - 新增: Flask, Flask-SocketIO, pytest-flask
  - 新增: Vue.js 3, Vite, socket.io-client
  - 保留: OpenCode CLI, httpx

- **Migration**:
  - 现有工作流需更新节点配置
  - Session数据需重新初始化
