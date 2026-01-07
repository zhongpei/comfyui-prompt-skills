这是一个基于 ComfyUI 最新社区标准（2024/2025）编写的详细插件（Custom Node）开发指南。

本指南涵盖了从环境配置、标准目录结构、核心 Python 代码编写、到 UI 交互（JavaScript）以及发布到 Registry 的全流程。

---

# ComfyUI 插件开发指南 (Latest Edition)

## 1. 开发前准备

### 核心概念

ComfyUI 的插件本质上是一个 **Python 包**。ComfyUI 启动时会扫描 `custom_nodes` 目录，加载所有符合规范的文件夹。
一个标准的节点（Node）是一个 Python 类，必须包含特定的属性（如 `INPUT_TYPES`）和方法。

### 推荐工具

* **Git**: 版本控制。
* **VS Code**: 推荐安装 Python 和 JavaScript 插件。
* **ComfyUI 本地环境**: 建议使用便携版或虚拟环境进行调试。

---

## 2. 标准目录结构

现代 ComfyUI 插件推荐使用以下结构，支持 `ComfyUI-Manager` 和 `ComfyUI Registry` 自动索引。

```text
ComfyUI-MyCustomNode/           # 项目根目录
├── __init__.py                 # 入口文件，导出节点映射
├── nodes.py                    # (推荐) 核心逻辑代码
├── pyproject.toml              # (推荐) 项目元数据，用于发布到 Registry
├── requirements.txt            # Python 依赖库
├── README.md                   # 说明文档
├── js/                         # (可选) 前端扩展脚本
│   └── my_script.js
└── examples/                   # (可选) 示例工作流 JSON
    └── workflow.json

```

---

## 3. 编写核心节点 (Python)

在 `nodes.py` 中定义你的节点类。

### 3.1 基础节点模板

```python
import torch

class MyFirstNode:
    """
    一个简单的示例节点，实现整数加法。
    """
    
    # 1. 定义该节点在 UI 菜单中的分类
    CATEGORY = "My Custom/Math"

    # 2. 定义输入 (UI 控件或连接点)
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 格式: "变量名": ("类型", {配置字典})
                "int_a": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1, "display": "number"}),
                "int_b": ("INT", {"default": 0}),
            },
            "optional": {
                # 可选输入，未连接时为 None
                "optional_image": ("IMAGE",), 
            }
        }

    # 3. 定义输出类型
    RETURN_TYPES = ("INT", "STRING")
    
    # 4. (可选) 定义输出插槽的自定义名称
    RETURN_NAMES = ("Sum Result", "Log Message")

    # 5. 定义执行函数的主入口名称
    FUNCTION = "execute_math"

    # 6. 核心逻辑函数
    def execute_math(self, int_a, int_b, optional_image=None):
        # 执行逻辑
        result = int_a + int_b
        log = f"Calculated: {int_a} + {int_b} = {result}"
        
        # 必须返回一个元组，即使只有一个输出
        return (result, log)

    # 7. (可选) 缓存控制
    # 默认情况下，如果输入没变，ComfyUI 会使用缓存。
    # 如果节点有随机性（如 Seed），需要重写此方法。
    # @classmethod
    # def IS_CHANGED(s, int_a, int_b, optional_image):
    #    return float("nan") # 总是重新运行

```

### 3.2 常见输入类型参考

* **基础类型**: `"INT"`, `"FLOAT"`, `"STRING"`, `"BOOLEAN"`
* **ComfyUI 内部类型**: `"IMAGE"` (Tensor [B,H,W,C]), `"LATENT"` (Dict), `"MODEL"`, `"VAE"`, `"CLIP"`
* **下拉菜单**:
```python
"method": (["add", "subtract", "multiply"], {"default": "add"})

```


* **多行文本框**:
```python
"prompt": ("STRING", {"multiline": True, "dynamicPrompts": True})

```



---

## 4. 注册节点 (`__init__.py`)

在 `__init__.py` 中告诉 ComfyUI 如何加载你的类。

```python
from .nodes import MyFirstNode

# 1. 节点类映射：类名 -> Python 类
NODE_CLASS_MAPPINGS = {
    "MyFirstNode": MyFirstNode
}

# 2. (可选) 显示名称映射：UI 上显示的更友好的名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyFirstNode": "My Super Math Node 3000"
}

# 3. (可选) 指定前端文件目录
# 如果你有 js 文件夹，需要在这里声明，ComfyUI 会自动加载其中的 .js 文件
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

```

---

## 5. 进阶：前端扩展 (JavaScript)

如果你需要修改 UI 行为（例如：监听进度、在节点上绘制图像、添加右键菜单），需要在 `js/` 目录下编写 JavaScript。

**示例：在控制台打印节点创建信息**

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "My.Custom.Extension",
    async nodeCreated(node, app) {
        if (node.comfyClass === "MyFirstNode") {
            console.log("My custom node was created!", node);
            
            // 示例：修改节点组件颜色
            node.bgcolor = "#224466";
        }
    }
});

```

---

## 6. 发布与规范 (`pyproject.toml`)

为了让你的插件被 **Comfy Registry** ([https://registry.comfy.org](https://registry.comfy.org)) 收录，建议添加 `pyproject.toml`。

```toml
[project]
name = "comfyui-my-custom-node"
description = "A short description of your node pack"
version = "1.0.0"
license = { text = "MIT" }
dependencies = ["numpy", "torch"]  # 这里列出 pip 依赖

[project.urls]
Repository = "https://github.com/username/comfyui-my-custom-node"

[tool.comfy]
PublisherId = "username"           # 你的 Comfy Registry ID
DisplayName = "My Custom Nodes"
Icon = "https://example.com/icon.png"

```

## 7. 调试与热重载

1. **安装插件**: 将你的文件夹链接或复制到 `ComfyUI/custom_nodes/` 下。
2. **重启 ComfyUI**: Python 端的修改必须重启 ComfyUI 后端才能生效。
3. **刷新浏览器**: JavaScript 端的修改只需刷新网页即可（如果是便携版有时需要 Ctrl+F5）。

## 8. 最佳实践 Checklist

* [ ] **类型安全**: 始终检查输入的 Tensor 形状，避免因 batch size 变化导致的崩溃。
* [ ] **GPU 内存**: 不要在 `__init__` 中加载大型模型，应在 `execute` 中按需加载，并使用 `comfy.model_management` 进行显存管理。
* [ ] **依赖管理**: 必须提供 `requirements.txt`，方便 ComfyUI Manager 自动安装依赖。
* [ ] **命名空间**: 节点分类建议使用 `CATEGORY = "作者名/功能类"`，避免污染根目录。