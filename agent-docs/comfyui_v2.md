# **ComfyUI 架构演进与插件开发权威指南：Frontend V2、Vue 模式与 2025 社区标准深度解析**

## **1\. 执行摘要：ComfyUI 生态系统的工业化转型**

ComfyUI 正处于其历史上最关键的架构转型期。从早期作为一个灵活但粗糙的 Stable Diffusion 节点编辑器，它已迅速演变为生成式 AI 领域的各种基础设施的核心引擎。截至 2024 年末并进入 2025 年，随着 **ComfyUI Frontend V2**（基于 Vue.js）的全面采用以及 **Comfy Registry**（官方注册表）的标准化，ComfyUI 的开发范式发生了根本性的转变。

对于自定义节点（Custom Node）开发者而言，过去那种依赖非托管 JavaScript 注入和 Python 动态补丁（monkey-patching）的“西部荒野”时代已宣告结束。取而代之的是一个强调类型安全、组件化 UI、严格内存管理和标准化分发的工业级开发环境。这一转变不仅是技术栈的升级，更是整个社区对稳定性、安全性和可维护性需求的响应。

本报告将基于最新的官方文档、GitHub 代码库变更记录以及社区技术讨论，对 ComfyUI Frontend V2 的架构进行详尽的剖析，并结合 2025 年的开发标准，为开发者提供一份详尽的迁移与开发指南。报告将深入探讨从 LiteGraph 到 Vue 的渲染范式转移，分析 comfy.model\_management 的内存安全机制，并详细阐述基于 pyproject.toml 的注册表发布流程，旨在帮助开发者构建符合未来标准的生产级扩展。

## ---

**2\. 架构演进：Frontend V2 的范式转移与技术动因**

要掌握现代 ComfyUI 插件开发的精髓，首先必须深入剖析从 Legacy Frontend（V1）向 Frontend V2 迁移的底层技术动因。这并非简单的界面换肤，而是底层渲染引擎与状态管理机制的彻底重构。

### **2.1 遗留 Canvas 系统（Legacy V1）的局限性分析**

长期以来，ComfyUI 的前端依赖于 litegraph.js 库。这是一种基于 HTML5 Canvas 的即时模式（Immediate Mode）渲染系统。在这种架构下，整个节点图谱、连线、以及节点内部的每一个微小控件（Widget），都是通过每一帧重绘 Canvas 像素来实现的。

这种架构在早期展现了极高的灵活性，允许开发者通过劫持 onDraw 方法随意绘制图形。然而，随着 ComfyUI 工作流的复杂度呈指数级增长，其弊端逐渐暴露无遗：

* **渲染循环瓶颈与交互延迟**：在 Legacy 系统中，UI 的交互逻辑与渲染逻辑紧密耦合。当工作流包含数千个节点时，单一的 Canvas 渲染循环（Render Loop）承受了巨大的计算压力。即使是微小的 UI 状态变更（如鼠标悬停高亮），也可能触发大面积的重绘。这导致了 UI 响应延迟与后端推理速度的脱节，即所谓的“界面卡顿”现象 1。  
* **开发效率与维护成本**：在 Canvas 上开发复杂的交互控件（如颜色选择器、曲线编辑器或文本输入框）极其痛苦。开发者必须手动计算每一个点击事件的坐标（Raycasting），并处理复杂的坐标系转换。这种命令式的绘图代码难以维护，且极易出现视觉故障 1。  
* **状态同步的脆弱性**：Legacy 系统缺乏现代化的状态管理库（如 Redux 或 Pinia）。前端的视觉状态与底层的图谱数据（Graph State）往往需要手动同步。这种松散的耦合导致了大量的“幻影状态”问题，即 UI 显示的值与实际传给后端的值不一致 3。

### **2.2 Frontend V2 的 Vue.js 架构深度解析**

Frontend V2 的推出，标志着 ComfyUI 全面拥抱声明式 UI（Declarative UI）和现代 Web 开发标准。该项目现托管于 Comfy-Org/ComfyUI\_frontend 仓库，核心技术栈锁定为 **Vue.js 3**、**TypeScript** 和 **Vite** 4。

#### **2.2.1 核心架构组件与职责**

| 组件名称 | V2 架构中的核心职责 | 对开发者生态的影响 |
| :---- | :---- | :---- |
| **Vue.js Framework** | 接管 UI 层，利用虚拟 DOM（Virtual DOM）和响应式系统（Reactivity System）处理界面更新。 | 开发者现在可以使用标准的 .vue 单文件组件构建复杂的自定义控件，而不再需要在 Canvas 上“画”按钮 6。 |
| **TypeScript** | 在前端代码库中强制执行静态类型检查。 | 引入了 @comfyorg/comfyui-frontend-types 包，强制开发者遵循严格的接口定义，大幅减少了运行时错误 7。 |
| **Pinia** | 集中式状态管理。 | 提供了全局的 Store 来管理应用设置、扩展状态和图谱数据，消除了组件间透传 Props 的混乱。 |
| **PrimeVue** | 标准化 UI 组件库。 | 提供了现成的、风格统一的 UI 元素（如滑块、下拉菜单、对话框），确保了不同插件之间的视觉一致性 6。 |
| **Compatibility Shim (垫片层)** | 遗留代码的兼容性桥梁。 | 尝试在 Vue 架构中渲染旧版 litegraph.js 扩展。这是一个临时的过渡机制，存在已知的图层叠加（Z-Index）和事件传播问题 2。 |

#### **2.2.2 抽象层与“生成后控制”**

V2 架构最显著的改进之一是实现了**视觉表现与逻辑图谱的解耦**。虽然底层的执行逻辑仍可能依赖 LiteGraph 的数据结构，但 UI 渲染完全由 Vue 接管。这种分离使得“Control After Generate”（生成后控制）成为可能。在旧版中，一旦后端开始生成，前端的主循环往往会被锁定或无法响应；而在 V2 中，得益于 Vue 的异步更新队列，UI 控件即使在后端忙碌时仍能保持交互活性，允许用户在生成过程中调整参数以备下一次执行 4。

## ---

**3\. 前端开发实战：Vue 组件与扩展注册标准**

在 V2 时代，开发 ComfyUI 扩展不再是编写零散的脚本，而是构建结构化的前端应用。虽然传统的将 JS 文件放入 web/ 目录的方法仍然有效，但其内部实现必须遵循新的注册 API 和组件模式。

### **3.1 扩展注册 API：app.registerExtension**

所有现代 ComfyUI 前端扩展的入口点都是 app.registerExtension 方法。V2 对此 API 进行了增强，引入了更丰富的生命周期钩子（Lifecycle Hooks），允许扩展在应用启动、节点创建、图谱加载等关键时刻介入。

**标准化的注册模式：**

JavaScript

import { app } from "../../scripts/app.js";

app.registerExtension({  
    name: "MyOrganization.MyExtension", // 必须使用命名空间以避免冲突  
      
    // 初始化钩子：应用启动时调用  
    async setup(app) {  
        console.log("Extension setup initiated");  
        // 这里可以进行全局设置的注册  
    },

    // 节点创建钩子：每当图谱中添加新节点时调用  
    async nodeCreated(node, app) {  
        // 通过 comfyClass 过滤目标节点  
        if (node.comfyClass \=== "MyCustomNode") {  
            // 在此处挂载 Vue 组件或初始化特定逻辑  
        }  
    },

    // 定义拦截钩子：在节点定义注册到系统前进行修改  
    async beforeRegisterNodeDef(nodeType, nodeData, app) {  
        // 可以修改 nodeType.prototype 来注入默认行为  
    }  
});

这种模式确保了扩展的加载顺序可控，并且避免了全局命名空间的污染 4。

### **3.2 使用 Vue 构建自定义控件 (Custom Widgets)**

这是 V2 开发中最大的变革点。开发者不再需要通过计算像素来绘制控件，而是可以将 Vue 组件“挂载”到节点上。

#### **3.2.1 Portal 渲染模式**

由于底层的节点图谱仍然基于 Canvas 坐标系，而 Vue 组件基于 DOM，因此 V2 实际上是使用了一种类似“Portal”（传送门）的技术。Vue 组件被渲染在 Canvas 之上的一个独立的 DOM 层中，并通过位置同步逻辑跟随节点移动。

**实现步骤：**

1. **定义 Vue 组件**：创建一个标准的 .vue 文件，例如 MyWidget.vue。可以使用 PrimeVue 的组件，如 \<p-slider\> 或 \<p-dropdown\>，以保持原生外观 6。  
2. **挂载组件**：在 nodeCreated 钩子中，开发者需要创建一个 DOM 容器元素，并将其附加到 ComfyUI 的覆盖层中。然后，使用 Vue 的 createApp 或组件挂载 API 将 MyWidget 渲染到该容器中。  
3. **位置同步**：这是最棘手的部分。尽管 V2 试图自动处理，但在处理缩放（Zoom）和平移（Pan）时，DOM 元素往往会出现“漂移”。稳健的做法是在节点的 onResize 和 onDrawForeground 事件中手动触发布局更新，强制 DOM 元素对齐到节点的坐标 2。

#### **3.2.2 类型安全与开发工具**

为了适应这种复杂的开发模式，引入 TypeScript 类型定义是必须的。@comfyorg/comfyui-frontend-types 包提供了 app、graph、widget 等核心对象的类型签名。

Bash

npm install \-D @comfyorg/comfyui-frontend-types

这不仅提供了智能代码补全，还能在编译阶段捕获对已废弃 API 的调用，这对于在快速迭代的 ComfyUI 代码库中保持插件稳定性至关重要 7。

### **3.3 设置系统与命令菜单 API**

V2 废弃了直接操作 DOM 添加菜单项的做法，转而提供了一套声明式的 API 来注册全局设置和上下文菜单。

#### **3.3.1 强类型设置注册**

通过 settings 数组，扩展可以向 ComfyUI 的全局设置面板注册配置项。这些设置支持布尔值、文本、数字等类型，并提供变更回调。

JavaScript

app.registerExtension({  
    name: "MyExtension.Settings",  
    settings:  
});

4

#### **3.3.2 选择工具箱 (Selection Toolbox)**

V2 引入了一个新的 UI 元素——“选择工具箱”，当用户在画布上选中节点时，该工具箱会浮现。扩展可以通过 getSelectionToolboxCommands 动态向其中注入命令。

JavaScript

app.registerExtension({  
    name: "MyExtension.Commands",  
    commands:,  
    getSelectionToolboxCommands: (selectedItems) \=\> {  
        // 根据选中的节点类型决定是否显示该命令  
        return \["my-ext.process-nodes"\];  
    }  
});

这种设计极大地提升了用户体验，使得常用操作触手可及 11。

### **3.4 兼容性挑战：Shim 层的局限与应对**

尽管 V2 提供了 Shim 层来兼容旧版插件，但实际测试表明，对于高度定制化的 UI 插件，兼容性并不完美。

* **覆盖层错位（Overlay Problem）**：旧版插件常使用 document.body.appendChild 添加浮动窗口。在 V2 中，由于 Canvas 容器层级的变化，这些元素可能会被遮挡，或者在画布缩放时位置计算错误 2。  
* **事件穿透**：Vue 的事件处理机制与原生 Canvas 事件循环可能发生冲突，导致点击 DOM 元素时误触背后的节点。  
* **2025 标准应对策略**：对于所有新开发的插件，**强制建议直接使用 Vue 编写**。对于必须维护的旧插件，建议在代码中检测 app.ui.version，如果是 V2 环境，则加载 Vue 版本的组件；如果是 V1，则回退到 Canvas 绘制逻辑。这是一种“双栈”维护策略 3。

## ---

**4\. 后端工程标准：2025 Python 规范与内存安全**

在前端全面现代化的同时，ComfyUI 的后端也在经历一场从“脚本化”到“工程化”的变革。2025 年的社区标准对代码的类型安全性、内存管理和执行效率提出了严苛的要求。

### **4.1 基于 comfy.comfy\_types 的严格类型系统**

为了配合前端的类型检查并支持注册表的自动验证，后端 Python 代码现在必须包含详尽的类型提示（Type Hinting）。comfy.comfy\_types 模块为此提供了标准定义。

**现代化节点定义示例：**

Python

from comfy.comfy\_types import IO, ComfyNodeABC, InputTypeDict  
from typing import Tuple

class ModernNode(ComfyNodeABC):  
    @classmethod  
    def INPUT\_TYPES(s) \-\> InputTypeDict:  
        return {  
            "required": {  
                "image": ("IMAGE",),  
                \# 使用字典定义参数的元数据，这是 V2 UI 渲染滑块的依据  
                "param": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1})  
            }  
        }

    RETURN\_TYPES: Tuple\[str\] \= ("IMAGE",)  
    RETURN\_NAMES: Tuple\[str\] \= ("processed\_image",)  
    FUNCTION \= "process"  
    CATEGORY \= "Advanced/Image"

    def process(self, image, param):  
        \# 具体的处理逻辑  
        return (image,)

这种写法不仅清晰，还能被 IDE 和 ComfyUI Manager 静态分析，从而在用户安装前就检测出潜在的兼容性问题 12。

### **4.2 动态输入与 ContainsAnyDict 模式**

在构建“总线”（Bus）节点或“通用管道”节点时，开发者往往需要节点能够接收任意类型、任意数量的输入。由于 INPUT\_TYPES 通常要求固定的键值对，社区演化出了一种标准化的黑客技巧——ContainsAnyDict。

**ContainsAnyDict 的原理与实现：**

ComfyUI 的前端在验证连接时，会检查输入名称是否存在于后端的 INPUT\_TYPES 返回的字典中。ContainsAnyDict 是一个重写了 \_\_contains\_\_ 魔术方法的字典类，它对任何键的查询都返回 True。

Python

class ContainsAnyDict(dict):  
    def \_\_contains\_\_(self, key):  
        return True

class DynamicBusNode:  
    @classmethod  
    def INPUT\_TYPES(s):  
        return {  
            "required": {},  
            \# 这个 optional 字典会“吞噬”所有尝试连接到它的输入  
            "optional": ContainsAnyDict()   
        }

    def run(self, \*\*kwargs):  
        \# 所有动态连接的输入都会出现在 kwargs 中  
        return (list(kwargs.values()),)

这种模式在 2025 年的复杂工作流中已成为标准配置，用于实现灵活的数据路由 14。

### **4.3 延迟求值（Lazy Evaluation）与 V3 标准**

为了优化大规模工作流的性能，ComfyUI 引入了延迟求值机制。这允许节点在执行前声明它真正需要的输入，从而跳过不必要的分支计算。

**check\_lazy\_status 的实现细节：**

这是 V3 标准中的核心方法。它在节点执行之前被调用。

Python

    @classmethod  
    def check\_lazy\_status(cls, switch\_val, input\_a, input\_b):  
        """  
        根据 switch\_val 的值决定需要计算哪个输入。  
        """  
        \# 如果开关值为 0，则声明只需求值 input\_a  
        \# 系统将不会计算 input\_b 的上游节点，从而节省大量 VRAM 和时间  
        if switch\_val \== 0:  
            return \["input\_a"\]  
        return \["input\_b"\]

注意：在 V3 标准中，check\_lazy\_status 必须被定义为 @classmethod。这是与旧版 API 的重要区别，旧版中它可能被视为实例方法 15。

### **4.4 内存安全与 comfy.model\_management**

显存（VRAM）管理是 ComfyUI 后端的生命线。在 2025 年的标准中，直接调用 torch.cuda.empty\_cache() 是被严格禁止的“反模式”，因为它会导致严重的 GPU 同步阻塞，降低整体吞吐量。

**soft\_empty\_cache 协议：**

开发者应始终使用 comfy.model\_management 模块来管理内存。

* **机制**：soft\_empty\_cache() 不会盲目清空缓存。它会首先检查当前系统的 VRAM 压力状态。只有当空闲显存低于特定阈值（通常是总空闲量的 25%）或系统处于“High VRAM”压力状态时，它才会触发底层的 Torch 缓存清理。  
* **临时大内存操作的范式**：对于需要临时占用大量显存的操作（如模型合并 Model Merge 或高分辨率 Latent Upscale），标准的内存管理流程如下：  
  1. comfy.model\_management.unload\_all\_models()：请求系统将当前未使用的模型权重卸载到 CPU 或系统 RAM。  
  2. comfy.model\_management.soft\_empty\_cache()：尝试整理碎片化的 VRAM。  
  3. 执行高负载操作。  
  4. 操作完成后，无需手动重新加载模型。ComfyUI 的 LRU（最近最少使用）缓存机制会在后续节点需要时自动将模型移回 GPU 17。

## ---

**5\. 注册表与分发标准：pyproject.toml 生态**

2024 年下半年起，ComfyUI 社区开始从分散的 Git 仓库管理转向中心化的 **Comfy Registry** (comfyregistry.org)。这一举措极大地提高了插件的安全性和依赖管理的可靠性。

### **5.1 pyproject.toml 规范详解**

现在，每个自定义节点项目都必须在根目录下包含一个 pyproject.toml 文件。这个文件不仅是 Python 项目的标准配置，更是 Comfy Registry 识别插件元数据的依据。

**标准配置示例：**

Ini, TOML

\[project\]  
name \= "comfyui-my-node" \# 项目的唯一标识符  
version \= "1.0.0"  
description \= "High-performance image processing nodes"  
dependencies \= \["numpy\>=1.20", "scikit-image"\] \# 明确声明 Python 依赖  
license \= { file \= "LICENSE" }

\[tool.comfy\]  
PublisherId \= "my\_publisher\_handle" \# 从 Registry 网站获取的发布者 ID  
DisplayName \= "My Studio Nodes" \# 在 Manager 中显示的友好名称  
Icon \= "https://example.com/icon.png"  
requires-comfyui \= "\>=0.3.0" \# 关键：声明对 ComfyUI 核心版本的最低要求

requires-comfyui 字段至关重要，它能防止用户在旧版核心上安装使用了 V3 API（如延迟求值）的插件，从而避免崩溃 20。

### **5.2 安全性与 install.py 的消亡**

在旧标准中，开发者常使用 install.py 来在用户机器上运行任意命令（如 pip install）。这带来了巨大的安全隐患。2025 标准强烈建议废弃 install.py，转而完全依赖 pyproject.toml 中的 dependencies 列表。ComfyUI Manager 和 Registry CLI 会解析这个列表并在隔离的环境中安全地安装依赖。

## ---

**6\. 高级实现模式**

### **6.1 前后端异步通信：PromptServer 路由**

对于复杂的交互式节点（例如，需要浏览服务器文件系统或从外部 API 获取数据的节点），标准的数据流无法满足需求。此时需要建立前后端直通的 API 路由。

后端实现（Python）：  
利用 PromptServer 单例注册 aiohttp 路由。

Python

from server import PromptServer  
from aiohttp import web

@PromptServer.instance.routes.get("/my-ext/get-data")  
async def get\_data(request):  
    \# 处理请求，返回 JSON  
    return web.json\_response({"data": "value", "status": "success"})

前端实现（JavaScript/Vue）：  
在 Vue 组件或扩展脚本中使用原生的 fetch API。

JavaScript

const response \= await fetch("/my-ext/get-data");  
const json \= await response.json();  
console.log(json.data);

这种模式使得 ComfyUI 能够演变为一个全栈应用平台 22。

### **6.2 动态模型加载与 Patch 系统**

对于加载非标准模型（如 Flux 或 SD3.5 的量化版本），开发者必须遵循 ComfyUI 的 Patch 系统，而不是直接加载 PyTorch 模型。

最佳实践：  
使用 comfy.model\_management.LoadedModel 上下文管理器，或者调用 load\_models\_gpu 工具函数。这些 API 会自动处理设备分配（CPU 到 GPU 的数据搬运），并根据用户的启动参数（--lowvram 或 \--highvram）自动优化显存使用策略。违背这一原则会导致插件独占显存，引发 OOM（Out Of Memory）错误 18。

## ---

**7\. 迁移策略与故障排查**

### **7.1 从 Legacy 到 V2 的迁移清单**

对于维护旧版节点套件的开发者，以下是迈向 V2 的必经之路：

1. **审计 Canvas 代码**：搜索代码中的 onDraw、onMouseDown 等 LiteGraph 特定方法。这些在 V2 中大概率会失效或表现异常。  
2. **Vue 重构**：将复杂的 UI 交互逻辑提取出来，重写为 Vue 组件。  
3. **注册方式升级**：将直接操作 LiteGraph.registerNodeType 的代码替换为 app.registerExtension 模式。  
4. **Z-Index 修正**：如果使用了自定义的浮动层，必须检查其在 V2 中的层级关系，必要时使用 Vue 的 \<Teleport\> 组件将其渲染到 body 层级，以脱离 Canvas 的裁剪区域。

### **7.2 常见错误与调试**

* **错误：Extension named... already registered**：这是由于 V2 对扩展命名的唯一性检查更为严格。在热重载（Hot Reload）开发时常见。**解决方案**：在注册前检查扩展是否已存在，或者确保使用唯一的命名空间 25。  
* **现象：控件无法点击或事件错乱**：通常是因为 DOM 元素遮挡了 Canvas，或者 Canvas 事件拦截了 DOM 事件。**解决方案**：在 CSS 中正确设置 pointer-events，并确保 Vue 组件的事件冒泡逻辑正确处理了停止传播（stopPropagation）。

## ---

**8\. 结论与展望**

2025 年的 ComfyUI 生态系统，已经从一个极客的实验场转变为一个标准化的生产环境。**Frontend V2** 的引入虽然带来了陡峭的学习曲线（Vue、TypeScript），但它赋予了开发者构建复杂、响应式、高性能界面的能力，这是旧版 Canvas 架构无法比拟的。

对于开发者而言，紧跟 **Comfy Registry** 的分发标准，遵守 **comfy.model\_management** 的内存协议，并掌握 **Vue 组件化** 开发，是构建下一代 ComfyUI 插件的基石。随着架构的日益成熟，我们可以预见，ComfyUI 将不仅是一个生图工具，更将成为一个通用的、高度可扩展的节点式应用开发平台。

### ---

**附录：关键技术对比表**

#### **表 1：前端架构深度对比 (Legacy vs. V2)**

| 特性维度 | Legacy (V1 / LiteGraph) | Modern (V2 / Vue.js) | 核心差异影响 |
| :---- | :---- | :---- | :---- |
| **渲染引擎** | HTML5 Canvas (即时模式) | Vue.js Virtual DOM \+ Canvas (混合模式) | V2 实现了逻辑与渲染分离，极大提升了 UI 性能和灵活性。 |
| **开发语言** | Vanilla JavaScript (ES5/ES6) | TypeScript / Vue / Vite | V2 引入了静态类型检查，显著降低了大型项目的维护成本。 |
| **状态管理** | 手动同步，易出错 | 响应式系统 (Pinia/Reactivity) | V2 实现了数据驱动视图，消除了“幻影状态” bug。 |
| **自定义控件** | ctx.drawImage / 原始 DOM 注入 | Vue 单文件组件 (.vue) | V2 允许使用成熟的 UI 库 (PrimeVue)，开发效率提升数倍。 |
| **性能瓶颈** | 随图谱规模线性下降 | 优化 (虚拟列表 / 局部更新) | V2 在处理超大规模工作流时表现更佳。 |

#### **表 2：2025 后端输入配置标准速查**

| 需求场景 | 实现代码模式 | 目的与优势 |
| :---- | :---- | :---- |
| **强类型连接** | ("IMAGE",) | 强制仅允许图像类型的输出连接，保证数据流安全。 |
| **UI 可配置参数** | ("FLOAT", {"default": 0.5, "min": 0.0, "step": 0.01}) | 自动在 V2 前端生成对应的滑块控件，并带有边界检查。 |
| **万能/动态输入** | ("ANY", ContainsAnyDict()) | 允许用户连接任意类型的节点，适用于总线或通用处理节点。 |
| **性能优化** | INPUT\_TYPES 中添加 {"lazy": True} | 标记该输入为惰性，仅在必要时计算。 |
| **运行时剪枝** | @classmethod check\_lazy\_status(...) | 配合 Lazy 标记，在运行时动态决定跳过哪些输入的计算，节省资源。 |

#### **Works cited**

1. Nodes 2.0 \- ComfyUI, accessed January 7, 2026, [https://docs.comfy.org/interface/nodes-2](https://docs.comfy.org/interface/nodes-2)  
2. Comfyui UI 2.0 breaking your custom widgets too? \- Reddit, accessed January 7, 2026, [https://www.reddit.com/r/comfyui/comments/1pnnpa7/comfyui\_ui\_20\_breaking\_your\_custom\_widgets\_too/](https://www.reddit.com/r/comfyui/comments/1pnnpa7/comfyui_ui_20_breaking_your_custom_widgets_too/)  
3. This is a shame. I've not used Nodes 2.0 so can't comment but I hope this doesn't cause a split in the node developers or mean that tgthree eventually can't be used because they're great\! : r/comfyui \- Reddit, accessed January 7, 2026, [https://www.reddit.com/r/comfyui/comments/1pd1r0k/this\_is\_a\_shame\_ive\_not\_used\_nodes\_20\_so\_cant/](https://www.reddit.com/r/comfyui/comments/1pd1r0k/this_is_a_shame_ive_not_used_nodes_20_so_cant/)  
4. Comfy-Org/ComfyUI\_frontend: Official front-end implementation of ComfyUI \- GitHub, accessed January 7, 2026, [https://github.com/Comfy-Org/ComfyUI\_frontend](https://github.com/Comfy-Org/ComfyUI_frontend)  
5. \[Announcement\] ComfyUI Frontend Modernization: Transitioning to a New Era on August 15, 2024 · Issue \#4169 \- GitHub, accessed January 7, 2026, [https://github.com/comfyanonymous/ComfyUI/issues/4169](https://github.com/comfyanonymous/ComfyUI/issues/4169)  
6. ComfyUI\_frontend\_vue\_basic Custom Node \- ComfyAI.run, accessed January 7, 2026, [https://comfyai.run/custom\_node/ComfyUI\_frontend\_vue\_basic](https://comfyai.run/custom_node/ComfyUI_frontend_vue_basic)  
7. @comfyorg/comfyui-frontend-types \- NPM, accessed January 7, 2026, [https://www.npmjs.com/package/@comfyorg/comfyui-frontend-types?activeTab=code](https://www.npmjs.com/package/@comfyorg/comfyui-frontend-types?activeTab=code)  
8. Javascript Extensions \- ComfyUI, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/js/javascript\_overview](https://docs.comfy.org/custom-nodes/js/javascript_overview)  
9. Comfy-Org/ComfyUI-React-Extension-Template \- GitHub, accessed January 7, 2026, [https://github.com/Comfy-Org/ComfyUI-React-Extension-Template](https://github.com/Comfy-Org/ComfyUI-React-Extension-Template)  
10. Settings \- ComfyUI Official Documentation, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/js/javascript\_settings](https://docs.comfy.org/custom-nodes/js/javascript_settings)  
11. Selection Toolbox \- ComfyUI, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/js/javascript\_selection\_toolbox](https://docs.comfy.org/custom-nodes/js/javascript_selection_toolbox)  
12. comfy/comfy\_types/README.md · gokaygokay/Chroma at 36d32c1595a05c75dc2e20a1bef2f276854de17c \- Hugging Face, accessed January 7, 2026, [https://huggingface.co/spaces/gokaygokay/Chroma/blob/36d32c1595a05c75dc2e20a1bef2f276854de17c/comfy/comfy\_types/README.md](https://huggingface.co/spaces/gokaygokay/Chroma/blob/36d32c1595a05c75dc2e20a1bef2f276854de17c/comfy/comfy_types/README.md)  
13. comfy/comfy\_types/README.md · multimodalart/wan-2-2-first-last-frame at 7deba667aa8b19f2cf854766aa9292b2bb161aa4 \- Hugging Face, accessed January 7, 2026, [https://huggingface.co/spaces/multimodalart/wan-2-2-first-last-frame/blame/7deba667aa8b19f2cf854766aa9292b2bb161aa4/comfy/comfy\_types/README.md](https://huggingface.co/spaces/multimodalart/wan-2-2-first-last-frame/blame/7deba667aa8b19f2cf854766aa9292b2bb161aa4/comfy/comfy_types/README.md)  
14. Hidden and Flexible inputs \- ComfyUI Official Documentation, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/backend/more\_on\_inputs](https://docs.comfy.org/custom-nodes/backend/more_on_inputs)  
15. Lazy Evaluation \- ComfyUI, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/backend/lazy\_evaluation](https://docs.comfy.org/custom-nodes/backend/lazy_evaluation)  
16. V3 Migration \- ComfyUI Official Documentation, accessed January 7, 2026, [https://docs.comfy.org/custom-nodes/v3\_migration](https://docs.comfy.org/custom-nodes/v3_migration)  
17. Comfyui-Memory\_Cleanup Custom Node \- ComfyAI.run, accessed January 7, 2026, [https://comfyai.run/custom\_node/Comfyui-Memory\_Cleanup](https://comfyai.run/custom_node/Comfyui-Memory_Cleanup)  
18. ComfyUI/comfy/model\_management.py at master \- GitHub, accessed January 7, 2026, [https://github.com/comfyanonymous/ComfyUI/blob/master/comfy/model\_management.py](https://github.com/comfyanonymous/ComfyUI/blob/master/comfy/model_management.py)  
19. ShmuelRonen/ComfyUI-FreeMemory \- GitHub, accessed January 7, 2026, [https://github.com/ShmuelRonen/ComfyUI-FreeMemory](https://github.com/ShmuelRonen/ComfyUI-FreeMemory)  
20. pyproject.toml \- ComfyUI Official Documentation, accessed January 7, 2026, [https://docs.comfy.org/registry/specifications](https://docs.comfy.org/registry/specifications)  
21. pyproject.toml \- ComfyAssets/ComfyUI\_PromptManager \- GitHub, accessed January 7, 2026, [https://github.com/ComfyAssets/ComfyUI\_PromptManager/blob/main/pyproject.toml](https://github.com/ComfyAssets/ComfyUI_PromptManager/blob/main/pyproject.toml)  
22. ComfyUI/custom\_nodes/example\_node.py.example at master \- GitHub, accessed January 7, 2026, [https://github.com/comfyanonymous/ComfyUI/blob/master/custom\_nodes/example\_node.py.example](https://github.com/comfyanonymous/ComfyUI/blob/master/custom_nodes/example_node.py.example)  
23. Upload 836 files · DegMaTsu/ComfyUI-Reactor-Fast-Face-Swap at 50e6701, accessed January 7, 2026, [https://huggingface.co/spaces/DegMaTsu/ComfyUI-Reactor-Fast-Face-Swap/commit/50e6701f085fbe960a0ba5c460894e0dbc95aa21](https://huggingface.co/spaces/DegMaTsu/ComfyUI-Reactor-Fast-Face-Swap/commit/50e6701f085fbe960a0ba5c460894e0dbc95aa21)  
24. CLAUDE.md \- EnragedAntelope/comfyui-sdnq \- GitHub, accessed January 7, 2026, [https://github.com/EnragedAntelope/comfyui-sdnq/blob/main/CLAUDE.md](https://github.com/EnragedAntelope/comfyui-sdnq/blob/main/CLAUDE.md)  
25. Widgets loading 3 times · Issue \#869 · yolain/ComfyUI-Easy-Use \- GitHub, accessed January 7, 2026, [https://github.com/yolain/ComfyUI-Easy-Use/issues/869](https://github.com/yolain/ComfyUI-Easy-Use/issues/869)