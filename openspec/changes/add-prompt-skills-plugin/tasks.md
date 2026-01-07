# 任务清单: 智能提示词生成插件

## 1. 项目初始化

- [x] 1.1 创建插件目录结构 (`custom_nodes/comfyui-prompt-skills/`)
- [x] 1.2 创建 `requirements.txt` (httpx, pydantic)
- [x] 1.3 创建 `README.md` 使用文档
- [x] 1.4 创建 `__init__.py` 入口文件

## 2. OpenCode Server集成 (core/server_manager.py)

- [x] 2.1 实现 `OpenCodeServerManager` 单例类
- [x] 2.2 实现 Server进程自动启动逻辑
- [x] 2.3 实现健康检查 (`GET /health`)
- [x] 2.4 实现优雅关闭逻辑
- [x] 2.5 添加错误处理和日志记录

## 3. 会话管理 (core/session_manager.py)

- [x] 3.1 实现 `SessionManager` 类
- [x] 3.2 实现会话创建 (`POST /session`)
- [x] 3.3 实现消息发送 (`POST /session/:id/message`)
- [x] 3.4 实现响应获取 (`GET /session/:id/message`)
- [x] 3.5 实现会话复用逻辑
- [x] 3.6 实现会话清理机制

## 4. OpenCode通信桥接 (core/opencode_bridge.py)

- [x] 4.1 实现 `OpenCodeBridge` 类
- [x] 4.2 封装HTTP客户端 (httpx)
- [x] 4.3 实现系统提示词注入（技能加载）
- [x] 4.4 实现用户提示词发送
- [x] 4.5 实现响应解析
- [x] 4.6 添加超时和重试机制

## 5. 输出格式化器 (core/output_formatter.py)

- [x] 5.1 实现 `OutputFormatter` 类
- [x] 5.2 实现逗号分隔英文格式化
- [x] 5.3 实现JSON结构化格式化
- [x] 5.4 实现中英双语格式化
- [x] 5.5 添加格式验证逻辑

## 6. 风格库系统 (data/)

- [x] 6.1 设计并创建 `z_styles_db.json` Schema
- [x] 6.2 填充摄影类风格数据
- [x] 6.3 填充插画类风格数据
- [x] 6.4 填充3D设计类风格数据
- [x] 6.5 添加Z-Image Turbo特定风格
- [x] 6.6 添加SDXL特定风格
- [x] 6.7 创建用户扩展目录 (`data/custom/`)

## 7. 技能文件开发 (skills/)

- [x] 7.1 编写 `z-photo/SKILL.md` (摄影写实技能)
  - [x] 7.1.1 定义技能元数据
  - [x] 7.1.2 编写风格搜索指令
  - [x] 7.1.3 编写Z-Image/SDXL差异化策略
  - [x] 7.1.4 编写输出格式规范

- [x] 7.2 编写 `z-manga/SKILL.md` (二次元动漫技能)
  - [x] 7.2.1 定义技能元数据
  - [x] 7.2.2 编写反3D策略
  - [x] 7.2.3 编写动漫风格触发词
  - [x] 7.2.4 编写赛璐璐渲染指令

- [x] 7.3 编写 `z-hanfu/SKILL.md` (汉服中国风技能)
  - [x] 7.3.1 定义技能元数据
  - [x] 7.3.2 编写中国元素关键词库
  - [x] 7.3.3 编写仙侠/武侠风格策略
  - [x] 7.3.4 编写传统服饰描述模板

## 8. ComfyUI节点开发 (nodes/)

- [x] 8.1 实现 `ZPromptGenerator` 节点类
- [x] 8.2 定义 `INPUT_TYPES` (用户输入、模型选择、API密钥)
- [x] 8.3 定义 `RETURN_TYPES` (三种输出格式)
- [x] 8.4 实现 `generate_prompt` 主方法
- [x] 8.5 实现模型选择逻辑 (Z-Image Turbo / SDXL)
- [x] 8.6 实现技能动态选择逻辑
- [x] 8.7 创建节点映射 (`NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`)

## 9. 日志系统 (core/logger.py)

- [x] 9.1 实现日志配置
- [x] 9.2 实现请求日志记录
- [x] 9.3 实现响应日志记录
- [x] 9.4 实现错误日志记录
- [x] 9.5 实现日志轮转 (可选)

## 10. 测试用例

- [x] 10.1 编写 `test_server_manager.py`
  - [x] 10.1.1 测试Server启动
  - [x] 10.1.2 测试健康检查
  - [x] 10.1.3 测试单例模式

- [x] 10.2 编写 `test_session_manager.py`
  - [x] 10.2.1 测试会话创建
  - [x] 10.2.2 测试消息发送
  - [x] 10.2.3 测试会话复用

- [x] 10.3 编写 `test_output_formatter.py`
  - [x] 10.3.1 测试英文格式化
  - [x] 10.3.2 测试JSON格式化
  - [x] 10.3.3 测试双语格式化

- [x] 10.4 编写 `test_prompt_generator.py`
  - [x] 10.4.1 测试节点INPUT_TYPES
  - [x] 10.4.2 测试节点RETURN_TYPES
  - [x] 10.4.3 集成测试（模拟OpenCode响应）

## 11. 文档与收尾

- [x] 11.1 完善 `README.md` 安装说明
- [x] 11.2 添加使用示例
- [x] 11.3 添加故障排除指南
- [x] 11.4 创建 `.gitignore`
- [x] 11.5 验证所有功能正常工作

---

## 实现状态

**总任务数**: 57
**已完成**: 57
**完成率**: 100%
