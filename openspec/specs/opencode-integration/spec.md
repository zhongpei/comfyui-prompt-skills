# opencode-integration Specification

## Purpose
TBD - created by archiving change add-prompt-skills-plugin. Update Purpose after archive.
## Requirements
### Requirement: OpenCode Server Lifecycle Management

The system MUST automatically manage the OpenCode Server process lifecycle.

#### Scenario: 自动启动Server

- **GIVEN** 用户已安装OpenCode CLI (`opencode` 命令可用)
- **AND** 当前没有运行中的OpenCode Server
- **WHEN** 用户首次使用 `ZPromptGenerator` 节点
- **THEN** 系统自动启动OpenCode Server进程
- **AND** Server监听在 `http://127.0.0.1:4096`
- **AND** 系统等待Server就绪后再继续执行

#### Scenario: 复用已存在的Server

- **GIVEN** OpenCode Server已在运行（端口4096）
- **WHEN** 用户使用 `ZPromptGenerator` 节点
- **THEN** 系统检测到已有Server
- **AND** 不启动新的Server进程
- **AND** 直接使用现有Server

#### Scenario: Server单例保证

- **GIVEN** 多个 `ZPromptGenerator` 节点同时存在于工作流中
- **WHEN** 工作流被执行
- **THEN** 系统仅维护一个Server实例
- **AND** 所有节点共享同一Server连接

#### Scenario: OpenCode未安装时的错误处理

- **GIVEN** 用户未安装OpenCode CLI
- **WHEN** 用户尝试使用 `ZPromptGenerator` 节点
- **THEN** 系统输出明确的错误信息：`"OpenCode CLI not found. Please install: npm install -g opencode"`
- **AND** 节点返回空字符串而非崩溃

---

### Requirement: Health Check

The system MUST implement a Server health check mechanism.

#### Scenario: 健康检查成功

- **GIVEN** OpenCode Server正在运行
- **WHEN** 系统调用 `GET /health`
- **THEN** 返回状态码 200
- **AND** 返回体包含 `{"healthy": true}`

#### Scenario: 健康检查失败时重启

- **GIVEN** OpenCode Server之前启动过但已异常退出
- **WHEN** 系统调用 `GET /health` 失败
- **THEN** 系统尝试重新启动Server
- **AND** 最多重试3次
- **AND** 每次重试间隔2秒

---

### Requirement: HTTP Client Communication

The system MUST use an HTTP client to communicate with the OpenCode Server REST API.

#### Scenario: 创建会话

- **GIVEN** OpenCode Server健康运行
- **WHEN** 系统调用 `POST /session`
- **WITH** body: `{"title": "ComfyUI Prompt Generation"}`
- **THEN** 返回状态码 200
- **AND** 返回体包含有效的 `session.id`

#### Scenario: 发送提示词消息

- **GIVEN** 已创建有效会话 `session_id`
- **WHEN** 系统调用 `POST /session/{session_id}/message`
- **WITH** body包含用户提示词和系统指令
- **THEN** 返回状态码 200
- **AND** 返回体包含LLM生成的响应

#### Scenario: 请求超时处理

- **GIVEN** OpenCode Server响应缓慢
- **WHEN** HTTP请求超过30秒未响应
- **THEN** 系统取消请求
- **AND** 记录超时错误到日志
- **AND** 返回预定义的默认提示词模板

---

### Requirement: Session Management

The system MUST implement session management for performance optimization and context persistence.

#### Scenario: 会话创建

- **GIVEN** 没有可复用的现有会话
- **WHEN** 用户发起提示词生成请求
- **THEN** 系统创建新会话
- **AND** 会话ID被持久化到本地文件

#### Scenario: 会话复用

- **GIVEN** 存在有效的现有会话（5分钟内活跃）
- **WHEN** 用户发起新的提示词生成请求
- **THEN** 系统复用现有会话
- **AND** 无需重新注入系统提示词

#### Scenario: 会话过期清理

- **GIVEN** 会话超过30分钟未使用
- **WHEN** 用户发起新的提示词生成请求
- **THEN** 系统删除旧会话 (`DELETE /session/{id}`)
- **AND** 创建新会话

---

### Requirement: System Prompt Injection

The system MUST inject system prompts at session start to load skills.

#### Scenario: 技能加载提示词

- **GIVEN** 新创建的会话
- **AND** 用户选择了 `skill_type = "z-photo"`
- **WHEN** 系统初始化会话
- **THEN** 系统发送系统提示词，包含：
  - 技能文件路径：`skills/z-photo/SKILL.md`
  - 风格库路径：`data/z_styles_db.json`
  - 输出格式要求

#### Scenario: 无AI回复的上下文注入

- **GIVEN** 需要注入上下文而不触发LLM响应
- **WHEN** 系统调用 `POST /session/{id}/message`
- **WITH** body包含 `"noReply": true`
- **THEN** 消息被添加到会话上下文
- **AND** 不消耗LLM推理资源

