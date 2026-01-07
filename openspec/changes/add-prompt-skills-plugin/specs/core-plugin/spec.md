# Core Plugin Capability

本规范定义了ComfyUI智能提示词生成插件的核心能力。

## ADDED Requirements

### Requirement: Plugin Initialization

The system MUST correctly initialize the plugin and register all nodes when ComfyUI starts.

#### Scenario: 插件成功加载

- **GIVEN** 插件目录位于 `custom_nodes/comfyui-prompt-skills/`
- **AND** 所有Python依赖已安装
- **WHEN** ComfyUI启动
- **THEN** 插件节点在节点菜单中可见（分类：`OpenCode/Z-Image`）
- **AND** 无错误日志输出

#### Scenario: 依赖缺失时的优雅降级

- **GIVEN** 插件目录存在但缺少Python依赖
- **WHEN** ComfyUI启动
- **THEN** 系统输出明确的错误信息，指示缺失的依赖
- **AND** ComfyUI其他功能正常运行

---

### Requirement: ZPromptGenerator Node

The system MUST provide a `ZPromptGenerator` node that accepts user input and outputs intelligently generated prompts.

#### Scenario: 节点正确定义INPUT_TYPES

- **GIVEN** 节点类 `ZPromptGenerator` 已定义
- **WHEN** 查询 `INPUT_TYPES`
- **THEN** 返回以下必需输入：
  - `user_prompt` (STRING): 用户提示词输入，支持多行
  - `target_model` (COMBO): 目标模型选择，选项为 `["Z-Image Turbo", "SDXL"]`
  - `skill_type` (COMBO): 技能类型选择，选项为 `["z-photo", "z-manga", "z-hanfu"]`
- **AND** 返回以下可选输入：
  - `api_key` (STRING): API密钥（可选，默认从环境变量读取）
  - `seed` (INT): 随机种子

#### Scenario: 节点正确定义RETURN_TYPES

- **GIVEN** 节点类 `ZPromptGenerator` 已定义
- **WHEN** 查询 `RETURN_TYPES`
- **THEN** 返回三种输出类型：
  - `prompt_english` (STRING): 逗号分隔的英文提示词
  - `prompt_json` (STRING): JSON结构化提示词
  - `prompt_bilingual` (STRING): 中英双语提示词
- **AND** `RETURN_NAMES` 返回对应的可读名称

---

### Requirement: Model Selection

The system MUST support user selection between Z-Image Turbo and SDXL models.

#### Scenario: 选择Z-Image Turbo模型

- **GIVEN** 用户在节点中选择 `target_model = "Z-Image Turbo"`
- **WHEN** 执行提示词生成
- **THEN** 生成的提示词符合Z-Image Turbo的最佳实践：
  - `negative_prompt` 为空字符串
  - 包含技术参数（如镜头、光影）
  - 优先使用JSON结构化格式

#### Scenario: 选择SDXL模型

- **GIVEN** 用户在节点中选择 `target_model = "SDXL"`
- **WHEN** 执行提示词生成
- **THEN** 生成的提示词符合SDXL的最佳实践：
  - 包含合理的 `negative_prompt`
  - 支持权重语法 `(word:1.5)`
  - 包含质量标签（如 `masterpiece, best quality`）

---

### Requirement: API Key Management

The system MUST support API key configuration via node input or environment variables.

#### Scenario: 通过节点输入提供API密钥

- **GIVEN** 用户在节点的 `api_key` 输入框中填写了有效密钥
- **WHEN** 执行提示词生成
- **THEN** 系统使用用户提供的密钥进行API认证

#### Scenario: 通过环境变量提供API密钥

- **GIVEN** 节点的 `api_key` 输入框为空
- **AND** 环境变量 `OPENCODE_API_KEY` 已设置
- **WHEN** 执行提示词生成
- **THEN** 系统从环境变量读取密钥进行API认证

#### Scenario: 使用OpenCode默认模型（无需API密钥）

- **GIVEN** 节点的 `api_key` 输入框为空
- **AND** 环境变量 `OPENCODE_API_KEY` 未设置
- **WHEN** 执行提示词生成
- **THEN** 系统使用OpenCode内置的免费模型
- **AND** 生成功能正常工作

---

### Requirement: Language Support

The system MUST support mixed Chinese-English user input.

#### Scenario: 中文输入

- **GIVEN** 用户输入中文提示词：`"一个穿着汉服的少女在桃花林中"`
- **WHEN** 执行提示词生成
- **THEN** 系统正确理解中文描述
- **AND** 输出的 `prompt_english` 为正确的英文翻译

#### Scenario: 英文输入

- **GIVEN** 用户输入英文提示词：`"a girl wearing traditional Chinese dress in a peach blossom forest"`
- **WHEN** 执行提示词生成
- **THEN** 系统正确处理英文描述
- **AND** 输出的 `prompt_english` 保持英文

#### Scenario: 中英混合输入

- **GIVEN** 用户输入混合提示词：`"一个 cyberpunk style 的武士"`
- **WHEN** 执行提示词生成
- **THEN** 系统正确理解混合表达
- **AND** 输出的 `prompt_english` 为统一的英文表达
