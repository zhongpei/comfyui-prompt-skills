# Change: 添加智能提示词生成插件 (Add Prompt Skills Plugin)

## Why

ComfyUI用户在使用Z-Image Turbo和SDXL等模型时，面临以下痛点：
1. **提示词编写复杂**：不同模型架构需要不同的提示词策略，用户需要记忆大量的风格触发词和技术参数
2. **风格一致性差**：手动编写的提示词难以保持风格一致性，缺乏系统化的风格库支持
3. **语言障碍**：中文用户难以将创意转化为英文提示词，丢失文化特定的视觉概念

本插件通过集成OpenCode智能体，将复杂的提示词工程知识封装为可复用的"技能（Skills）"，为用户提供智能化的提示词生成能力。

## What Changes

### 新增功能

- **ComfyUI节点**：
  - `ZPromptGenerator` - 主节点，支持中英文输入，三种输出格式
  - 模型选择下拉框（Z-Image Turbo / SDXL）
  - API密钥配置（节点输入或环境变量）

- **OpenCode集成**：
  - 自动启动OpenCode Server进程（单实例）
  - 通过HTTP REST API与OpenCode Server通信
  - 会话管理（创建、复用、清理）

- **技能系统**：
  - `z-photo` - 摄影写实专家技能
  - `z-manga` - 二次元动漫专家技能
  - `z-hanfu` - 汉服中国风专家技能

- **风格库**：
  - 预置JSON风格数据库（摄影、插画、3D设计）
  - 用户可手动添加JSON文件扩展

- **日志系统**：
  - 记录所有用户请求和输出到日志文件
  - 日志存储在 `custom_nodes/comfyui-prompt-skills/logs/`

### 输出格式

1. **Comma-separated English** - 纯逗号分隔的英文字符串
2. **JSON Structured** - 结构化JSON（主体、环境、风格、技术参数）
3. **Bilingual** - 中英双语输出

## Impact

- **Affected specs**:
  - `core-plugin` (新增)
  - `opencode-integration` (新增)
  - `skills-engine` (新增)
  - `style-library` (新增)

- **Affected code**:
  - `custom_nodes/comfyui-prompt-skills/` - 插件主目录
  - `skills/` - OpenCode技能文件
  - `data/` - 风格库JSON文件
  - `logs/` - 日志目录

- **Dependencies**:
  - OpenCode CLI (需预先安装)
  - Python `requests` / `httpx` 库
  - ComfyUI (节点运行环境)
