# 实施任务清单: 三层架构重构

## 1. 基础设施搭建 (Infrastructure)

- [x] 1.1 创建新目录结构（`backend/`, `web/`, `js/`）
- [x] 1.2 配置 `pyproject.toml` 和 Python 依赖
- [x] 1.3 初始化 Vue.js 项目（Vite + Vue 3 + TypeScript）
- [x] 1.4 配置 Vite 输出到 `js/` 目录

## 2. Tier 3: Opencode Core 实现

- [x] 2.1 实现 `SessionManager` 单例类（全局状态管理）
- [x] 2.2 实现 `SkillRegistry` 技能注册中心
- [x] 2.3 实现 `OpencodeClient` 与 OpenCode Server 的 HTTP 通信
- [x] 2.4 编写 Core 层单元测试

## 3. Tier 2: Logic Layer 实现

- [x] 3.1 创建 Flask 应用工厂 (`create_app`)
- [x] 3.2 配置 Flask-SocketIO
- [x] 3.3 实现 WebSocket 事件处理器（connect, configure, user_message）
- [x] 3.4 实现流式响应推送（stream_delta, debug_log）
- [x] 3.5 编写 Flask 层独立集成测试（pytest-flask）

## 4. Tier 1: Vue 前端实现

- [x] 4.1 创建 Vue 主组件 (`App.vue`)
- [x] 4.2 实现 `ChatPanel.vue` 聊天面板（流式显示）
- [x] 4.3 实现 `SkillSelector.vue` 技能多选组件
- [x] 4.4 实现 `DebugPanel.vue` 调试信息面板
- [x] 4.5 集成 socket.io-client
- [x] 4.6 Vite 构建输出 ES Module

## 5. ComfyUI 节点集成

- [x] 5.1 实现 `OpencodeContainerNode`（哑节点）
- [x] 5.2 编写 JS 扩展（app.registerExtension）劫持 Widget
- [x] 5.3 挂载 Vue 应用到节点 DOM
- [x] 5.4 实现 Widget 双向数据同步
- [x] 5.5 在 `__init__.py` 中启动 Flask 守护线程

## 6. 集成与验证

- [x] 6.1 端到端冒烟测试（ComfyUI 启动 → Vue 加载 → WebSocket 连接）
- [x] 6.2 验证流式输出显示
- [x] 6.3 验证多角色 Skills 切换
- [x] 6.4 验证 Session 状态持久化
- [x] 6.5 更新 README 文档

## 7. 迁移与清理

- [x] 7.1 迁移现有风格库 JSON 文件
- [x] 7.2 迁移技能文件
- [x] 7.3 归档旧代码（`comfyui-prompt-skills_old`）
- [x] 7.4 更新 `openspec/project.md`
