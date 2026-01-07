# Spec Delta: core-plugin

## MODIFIED Requirements

### Requirement: Plugin Architecture

本插件SHALL采用三层服务架构（Three-Tier SOA）实现前后端解耦。

- **Tier 1 (展示层)**: ComfyUI节点SHALL作为纯Vue容器，不含业务逻辑
- **Tier 2 (逻辑层)**: Flask Logic Layer SHALL提供WebSocket通信和独立测试能力
- **Tier 3 (核心层)**: Opencode Core SHALL持有全局Session状态和技能调度

#### Scenario: Flask服务自动启动
- **WHEN** ComfyUI加载自定义节点
- **THEN** Flask服务SHALL在守护线程中启动
- **AND** Flask服务SHALL监听 `127.0.0.1:5000`

#### Scenario: Vue应用挂载到节点
- **WHEN** 用户添加OpencodeContainerNode到工作流
- **THEN** Vue应用SHALL渲染在节点DOM内
- **AND** 配置数据SHALL通过Widget机制持久化

---

## ADDED Requirements

### Requirement: WebSocket双向通信

系统SHALL支持通过WebSocket进行实时双向通信。

#### Scenario: 建立WebSocket连接
- **WHEN** Vue应用初始化完成
- **THEN** 系统SHALL通过socket.io-client连接到Flask服务
- **AND** 系统SHALL发送session_id进行握手

#### Scenario: 接收流式响应
- **WHEN** LLM开始生成内容
- **THEN** 系统SHALL通过`stream_delta`事件推送增量文本
- **AND** Vue应用SHALL实时显示打字机效果

#### Scenario: 接收调试信息
- **WHEN** 后端执行技能时产生日志
- **THEN** 系统SHALL通过`debug_log`事件推送调试信息
- **AND** DebugPanel组件SHALL显示Chain of Thought

---

### Requirement: 会话状态管理

系统SHALL通过全局SessionManager管理会话状态。

#### Scenario: 创建新会话
- **WHEN** 用户首次连接且无现有会话
- **THEN** 系统SHALL创建新的Session对象
- **AND** Session SHALL包含history、skills、config字段

#### Scenario: 重连状态恢复
- **WHEN** WebSocket断线后重新连接
- **THEN** 系统SHALL通过`sync_state`事件推送完整历史
- **AND** Vue应用SHALL恢复之前的聊天界面

---

### Requirement: 多角色技能支持

系统SHALL支持同时激活多个技能（Skills）。

#### Scenario: 多选技能激活
- **WHEN** 用户在SkillSelector中选择多个技能
- **THEN** 系统SHALL将所有选中技能注入到会话上下文
- **AND** LLM SHALL根据所有激活技能生成提示词

#### Scenario: 动态切换技能
- **WHEN** 用户修改技能选择
- **THEN** 系统SHALL通过`configure`事件更新后端
- **AND** 后续请求SHALL使用新的技能配置

---

### Requirement: 独立测试能力

Logic Layer SHALL支持脱离ComfyUI环境进行独立测试。

#### Scenario: 使用pytest测试WebSocket
- **WHEN** 开发者运行`pytest tests/test_socket_handlers.py`
- **THEN** 测试SHALL在无ComfyUI环境下执行
- **AND** 测试SHALL使用Mock对象模拟Opencode Core

#### Scenario: 使用测试客户端
- **WHEN** 测试代码创建socketio.test_client
- **THEN** 系统SHALL创建虚拟WebSocket连接
- **AND** 测试SHALL能够验证事件路由和响应
