# Project Context

## Purpose

ComfyUI智能提示词生成插件（comfyui-prompt-skills），通过集成OpenCode智能体为用户提供基于LLM的智能提示词生成能力。

**核心价值**:
- 将复杂的提示词工程知识封装为可复用的"技能（Skills）"
- 赋予智能体读取并理解外部风格库的能力
- 针对Z-Image Turbo和SDXL模型制定精准的提示词策略

## Tech Stack

- **Runtime**: Python 3.10+ (ComfyUI环境)
- **HTTP Client**: httpx (异步HTTP请求)
- **External Service**: OpenCode Server (REST API)
- **LLM Backend**: OpenCode内置模型 / GLM-4 / 可配置
- **Target Models**: Z-Image Turbo, SDXL

## Project Conventions

### Code Style

- 遵循 PEP 8 规范
- 使用 Type Hints 进行类型标注
- 类名使用 PascalCase，函数名使用 snake_case
- 私有方法以单下划线开头 `_method_name`
- 常量使用全大写 `CONSTANT_NAME`

### Architecture Patterns

- **单例模式**：OpenCode Server管理器
- **桥接模式**：Python与OpenCode Server通信
- **策略模式**：不同模型的提示词生成策略
- **工厂模式**：输出格式化器

### Testing Strategy

- 使用 pytest 作为测试框架
- 单元测试覆盖核心模块
- Mock外部HTTP调用进行集成测试
- 测试文件命名：`test_<module_name>.py`

### Git Workflow

- 主分支：`main`
- 功能分支：`feature/<feature-name>`
- 修复分支：`fix/<issue-name>`
- Commit消息格式：`type(scope): description`
  - type: feat, fix, docs, refactor, test, chore

## Domain Context

### ComfyUI节点开发

- 节点类需要定义 `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`
- 通过 `NODE_CLASS_MAPPINGS` 注册节点
- 节点在每次工作流执行时被调用

### OpenCode技能系统

- 技能文件使用YAML前置元数据 + Markdown格式
- 技能通过懒加载机制在需要时加载
- 技能可以使用 `fs_read` 工具读取外部文件

### Prompt Engineering

- Z-Image Turbo: S3-DiT架构，忽略negative prompt，需要显式技术参数
- SDXL: U-Net架构，支持negative prompt和权重语法

## Important Constraints

- OpenCode Server必须预先启动或由插件自动启动
- ComfyUI节点运行在主线程，需要避免阻塞操作
- 风格库JSON文件必须符合预定义Schema
- 日志文件不应无限增长

## External Dependencies

- **OpenCode CLI**: `npm install -g opencode` (必需)
- **OpenCode Server**: 通过HTTP API通信 (http://127.0.0.1:4096)
- **ComfyUI**: 提供节点运行环境
