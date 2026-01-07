# 技术设计文档: ComfyUI 智能提示词生成插件

## Context

### 背景

本插件旨在将OpenCode智能体能力引入ComfyUI，为用户提供基于LLM的智能提示词生成功能。核心挑战包括：

1. **跨运行时通信**：ComfyUI是Python环境，OpenCode是Node.js环境
2. **进程生命周期管理**：OpenCode Server需要持久运行
3. **技能系统集成**：通过会话机制加载和执行技能

### 约束

- OpenCode Server暴露OpenAPI 3.1规范的REST接口
- ComfyUI节点在每次图像生成时被调用
- 技能文件必须在会话中动态读取，而非全局加载

### 利益相关者

- **最终用户**：ComfyUI用户，需要简单直观的节点界面
- **插件开发者**：需要清晰的扩展机制

---

## Goals / Non-Goals

### Goals

1. 提供一键式智能提示词生成，用户无需了解底层实现
2. 支持Z-Image Turbo和SDXL两种主流模型架构
3. 提供三种输出格式满足不同工作流需求
4. 技能系统可扩展，用户可手动添加风格库

### Non-Goals

1. 不实现ComfyUI内的LLM推理（使用OpenCode托管）
2. 不支持图像输入的多模态分析（仅文本到文本）
3. 不实现实时流式输出（批量返回结果）
4. 不支持Flux、SD1.5等其他模型（仅Z-Image Turbo和SDXL）

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ComfyUI Environment                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    ZPromptGenerator Node                     ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐││
│  │  │ User Input  │  │ Model Select │  │ API Key (optional)   │││
│  │  │ (中/英文)   │  │ Z-Image/SDXL │  │ env or input         │││
│  │  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘││
│  │         │                │                     │             ││
│  │         └────────────────┼─────────────────────┘             ││
│  │                          ▼                                   ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │              OpenCodeBridge (Python)                   │  ││
│  │  │  - Auto-start OpenCode Server (singleton)              │  ││
│  │  │  - Session management (create/reuse/cleanup)           │  ││
│  │  │  - HTTP REST API calls                                 │  ││
│  │  │  - Response parsing and formatting                     │  ││
│  │  └───────────────────────┬───────────────────────────────┘  ││
│  │                          │ HTTP                              ││
│  │                          ▼                                   ││
│  └──────────────────────────┼───────────────────────────────────┘│
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OpenCode Server                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ REST API (http://127.0.0.1:4096)                            ││
│  │  - POST /session (create)                                    ││
│  │  - POST /session/:id/message (prompt)                        ││
│  │  - GET  /session/:id/message (get response)                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Skills Engine                             ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                   ││
│  │  │ z-photo  │  │ z-manga  │  │ z-hanfu  │                   ││
│  │  └──────────┘  └──────────┘  └──────────┘                   ││
│  │  Skills loaded via session context (fs_read tool)            ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Style Database                             ││
│  │  data/z_styles_db.json                                       ││
│  │  - photography: film_noir, hasselblad_studio, street, ...    ││
│  │  - illustration: ghibli, vintage_anime, impasto, ...         ││
│  │  - design: pop_mart, voxel, surrealism, ...                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    LLM Provider                              ││
│  │  Default: OpenCode built-in free model                       ││
│  │  Optional: GLM-4, Claude, GPT-4, etc. (via config)           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Decisions

### Decision 1: OpenCode Server通信方式

**决定**：使用Python HTTP客户端直接调用OpenCode Server REST API

**理由**：
- OpenCode Server暴露标准的OpenAPI 3.1接口
- 无需额外的Node.js桥接脚本
- Python生态有成熟的HTTP客户端（httpx/requests）

**备选方案**：
- ❌ subprocess调用Node.js SDK脚本 - 增加复杂度和启动延迟
- ❌ 直接调用LLM API - 失去OpenCode的技能系统和工具链能力

### Decision 2: OpenCode Server生命周期管理

**决定**：插件自动启动并管理单例OpenCode Server进程

**实现**：
```python
class OpenCodeServerManager:
    _instance = None
    _process = None
    _port = 4096
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._start_server()
        return cls._instance
    
    @classmethod
    def _start_server(cls):
        # Check if server already running
        try:
            response = requests.get(f"http://127.0.0.1:{cls._port}/health")
            if response.status_code == 200:
                return  # Server already running
        except:
            pass
        
        # Start new server process
        cls._process = subprocess.Popen(
            ["opencode", "serve", "--port", str(cls._port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
```

**理由**：
- 用户无需手动启动Server
- 单例模式确保资源高效利用
- 健康检查避免重复启动

### Decision 3: 技能加载机制

**决定**：通过会话上下文注入技能指令，而非全局加载

**流程**：
1. 创建新会话或复用现有会话
2. 发送系统提示词，包含技能文件路径
3. LLM使用fs_read工具读取技能文件
4. 根据技能指令执行提示词生成

**理由**：
- 符合OpenCode的设计理念（懒加载）
- 避免上下文窗口污染
- 支持动态切换技能

### Decision 4: 输出格式设计

**决定**：三种格式同时输出，通过不同输出端口提供

| 输出端口 | 格式 | 示例 |
|---------|------|------|
| `prompt_english` | 逗号分隔 | `cinematic, 35mm film, ...` |
| `prompt_json` | JSON结构 | `{"subject": "...", "style": "..."}` |
| `prompt_bilingual` | 中英对照 | `电影感(cinematic), 35mm胶片(35mm film)` |

**理由**：
- 满足不同下游节点的输入需求
- JSON格式便于程序化处理
- 双语格式便于用户理解和调试

### Decision 5: 模型适配策略

**决定**：根据目标模型选择不同的提示词策略

| 模型 | 策略 |
|------|------|
| Z-Image Turbo | 忽略negative_prompt，强调技术参数，使用JSON结构 |
| SDXL | 支持negative_prompt，使用权重语法(word:1.5) |

**理由**：
- Z-Image Turbo的蒸馏架构对negative prompt不响应
- SDXL需要更细粒度的权重控制

---

## Data Structures

### 风格库JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "model_version": { "type": "string" },
        "last_updated": { "type": "string", "format": "date" }
      }
    },
    "styles": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "name": { "type": "string" },
            "name_zh": { "type": "string" },
            "keywords": { "type": "array", "items": { "type": "string" } },
            "tech_specs": { "type": "string" },
            "model_target": { 
              "type": "array", 
              "items": { "enum": ["z-image-turbo", "sdxl"] }
            }
          },
          "required": ["id", "name", "keywords"]
        }
      }
    }
  }
}
```

### 输出JSON Schema

```json
{
  "type": "object",
  "properties": {
    "positive_prompt": { "type": "string" },
    "negative_prompt": { "type": "string" },
    "seed": { "type": "integer" },
    "model_target": { "type": "string" },
    "structured": {
      "type": "object",
      "properties": {
        "subject": { "type": "string" },
        "environment": { "type": "string" },
        "style": { "type": "string" },
        "tech_specs": { "type": "string" }
      }
    },
    "bilingual": {
      "type": "object",
      "properties": {
        "subject_zh": { "type": "string" },
        "subject_en": { "type": "string" }
      }
    }
  }
}
```

---

## File Structure

```
custom_nodes/comfyui-prompt-skills/
├── __init__.py                    # ComfyUI节点注册入口
├── nodes/
│   ├── __init__.py
│   ├── prompt_generator.py        # ZPromptGenerator节点实现
│   └── node_mappings.py           # 节点映射配置
├── core/
│   ├── __init__.py
│   ├── opencode_bridge.py         # OpenCode Server通信桥接
│   ├── server_manager.py          # Server进程管理
│   ├── session_manager.py         # 会话管理
│   └── output_formatter.py        # 输出格式化器
├── skills/
│   ├── z-photo/
│   │   └── SKILL.md               # 摄影写实技能
│   ├── z-manga/
│   │   └── SKILL.md               # 二次元动漫技能
│   └── z-hanfu/
│       └── SKILL.md               # 汉服中国风技能
├── data/
│   ├── z_styles_db.json           # 核心风格库
│   └── custom/                    # 用户扩展风格目录
│       └── .gitkeep
├── logs/
│   └── .gitkeep                   # 日志目录
├── tests/
│   ├── __init__.py
│   ├── test_opencode_bridge.py
│   ├── test_session_manager.py
│   └── test_output_formatter.py
├── requirements.txt               # Python依赖
└── README.md                      # 使用文档
```

---

## Risks / Trade-offs

### Risk 1: OpenCode Server启动失败

**风险**：用户未安装OpenCode或版本不兼容

**缓解措施**：
- 启动时检测opencode命令是否存在
- 提供清晰的错误提示和安装指引
- 记录详细日志便于调试

### Risk 2: 会话状态丢失

**风险**：ComfyUI重启或长时间未使用导致会话失效

**缓解措施**：
- 每次调用前检查会话状态
- 失效时自动创建新会话
- 会话ID持久化到本地文件

### Risk 3: LLM响应超时

**风险**：网络问题或模型负载过高导致API超时

**缓解措施**：
- 设置合理的超时时间（30秒）
- 提供重试机制（最多3次）
- 超时时返回默认模板提示词

### Risk 4: 风格库JSON格式错误

**风险**：用户手动添加的JSON文件格式不正确

**缓解措施**：
- 加载时进行Schema验证
- 格式错误时跳过该文件并记录警告
- 提供JSON验证工具或示例

---

## Migration Plan

**无需迁移**：本变更为新增功能，无现有数据或API需要迁移。

### 首次安装流程

1. 用户将插件目录复制到 `ComfyUI/custom_nodes/`
2. 安装Python依赖：`pip install -r requirements.txt`
3. 确保已安装OpenCode CLI：`npm install -g opencode`
4. 重启ComfyUI
5. 在节点菜单中找到 `OpenCode/Z-Image` 分类

---

## Open Questions

1. **Q: 是否需要支持多语言的风格库？**
   - 当前设计仅支持中英双语，未来可能需要扩展到日语、韩语等

2. **Q: 是否需要支持自定义技能？**
   - 当前仅提供三个预置技能，用户是否需要自定义技能的能力？

3. **Q: 会话是否需要持久化历史？**
   - 当前设计每次调用创建新上下文，是否需要保留对话历史用于渐进式修改？

---

## References

- [OpenCode SDK Documentation](https://opencode.ai/docs/sdk/)
- [OpenCode Server Documentation](https://opencode.ai/docs/server/)
- [ComfyUI Custom Nodes Documentation](https://docs.comfy.org/custom-nodes/backend/datatypes)
- [Z-Image Turbo Prompt Guide](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
