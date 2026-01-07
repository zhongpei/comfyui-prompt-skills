# Skills Engine Capability

本规范定义了OpenCode技能系统的能力，包括三个核心技能：z-photo、z-manga、z-hanfu。

## ADDED Requirements

### Requirement: Skill File Structure

Each skill file MUST follow the standard OpenCode SKILL.md format.

#### Scenario: 技能元数据定义

- **GIVEN** 技能文件 `skills/z-photo/SKILL.md`
- **WHEN** OpenCode解析该文件
- **THEN** 提取出以下YAML前置元数据：
  - `name`: 技能标识符（如 `z-photo`）
  - `description`: 技能简短描述，用于路由匹配
  - `license`: 许可证信息

#### Scenario: 技能指令内容

- **GIVEN** 技能文件包含Markdown指令
- **WHEN** LLM读取技能内容
- **THEN** 能够理解并执行以下指令类型：
  - 风格搜索指令（如何查询风格库）
  - 提示词构建规则
  - 输出格式规范

---

### Requirement: Z-Photo Skill (摄影写实技能)

The system MUST provide a `z-photo` skill specifically for generating photorealistic style prompts.

#### Scenario: 风格库读取

- **GIVEN** 技能被激活
- **AND** 用户输入包含"写实"、"照片"、"人像"等关键词
- **WHEN** LLM执行技能指令
- **THEN** LLM使用 `fs_read` 工具读取 `data/z_styles_db.json`
- **AND** 在 `photography` 类别中搜索匹配的风格

#### Scenario: Z-Image Turbo适配

- **GIVEN** 目标模型为 `Z-Image Turbo`
- **WHEN** 生成提示词
- **THEN** 提示词结构遵循：`[风格触发词], [技术参数], [主体描述], [环境与光影], [构图]`
- **AND** `negative_prompt` 为空

#### Scenario: SDXL适配

- **GIVEN** 目标模型为 `SDXL`
- **WHEN** 生成提示词
- **THEN** 提示词结构遵循：`[质量标签], [风格], [主体], [细节], [负面提示词]`
- **AND** 包含合理的 `negative_prompt`

#### Scenario: 摄影技术参数

- **GIVEN** 用户请求"电影感"或"胶片"风格
- **WHEN** 生成提示词
- **THEN** 输出包含以下技术参数之一：
  - 镜头规格：`35mm lens`, `85mm f/1.2`, `anamorphic lens`
  - 胶片模拟：`Kodak Portra 400`, `Fuji Pro 400H`, `film grain`
  - 光影效果：`rim light`, `volumetric lighting`, `golden hour`

---

### Requirement: Z-Manga Skill (二次元动漫技能)

The system MUST provide a `z-manga` skill specifically for generating anime and 2D illustration style prompts.

#### Scenario: 反3D策略

- **GIVEN** 用户请求动漫/二次元风格
- **WHEN** 生成提示词
- **THEN** 输出必须包含以下反3D关键词之一：
  - `flat color`, `cel shaded`, `2d illustration`
  - `anime screenshot`, `hand drawn`
- **目的**: 防止Z-Image的3D训练数据污染

#### Scenario: 赛璐璐渲染

- **GIVEN** 用户请求"复古动漫"或"90年代"风格
- **WHEN** 生成提示词
- **THEN** 输出包含：
  - `cel shaded` (赛璐璐着色)
  - `1990s anime screenshot`
  - `VHS glitch` (可选)

#### Scenario: 吉卜力风格

- **GIVEN** 用户提及"吉卜力"、"宫崎骏"
- **WHEN** 生成提示词
- **THEN** 输出包含：
  - `Ghibli style`
  - `detailed background painting`
  - `cumulonimbus clouds`
  - `pastoral atmosphere`

#### Scenario: 国漫风格

- **GIVEN** 用户提及"国漫"、"中国动画"
- **WHEN** 生成提示词
- **THEN** 输出包含中国特色关键词：
  - `wuxia style` (武侠)
  - `ink wash painting` (水墨)
  - `Chinese animation style`

---

### Requirement: Z-Hanfu Skill (汉服中国风技能)

The system MUST provide a `z-hanfu` skill specifically for generating Hanfu and traditional Chinese element prompts.

#### Scenario: 汉服描述

- **GIVEN** 用户请求汉服相关内容
- **WHEN** 生成提示词
- **THEN** 输出包含详细的服饰描述：
  - 朝代风格：`Tang dynasty style`, `Han dynasty clothing`, `Ming dynasty hanfu`
  - 款式类型：`ruqun`, `beizi`, `aoqun`, `shenyi`
  - 配饰：`jade hairpin`, `silk ribbon`, `embroidered pattern`

#### Scenario: 仙侠元素

- **GIVEN** 用户提及"仙侠"、"修仙"、"玄幻"
- **WHEN** 生成提示词
- **THEN** 输出包含仙侠视觉元素：
  - `xianxia style`
  - `immortal cultivator`
  - `flowing robes`, `ethereal glow`
  - `cloud mountains`, `celestial palace`

#### Scenario: 武侠元素

- **GIVEN** 用户提及"武侠"、"江湖"、"侠客"
- **WHEN** 生成提示词
- **THEN** 输出包含武侠视觉元素：
  - `wuxia style`
  - `martial artist`, `swordsman`
  - `bamboo forest`, `ancient China`

#### Scenario: 传统场景

- **GIVEN** 用户请求中国传统场景
- **WHEN** 生成提示词
- **THEN** 输出包含场景关键词：
  - 自然：`peach blossom`, `willow tree`, `lotus pond`, `bamboo grove`
  - 建筑：`ancient Chinese architecture`, `pavilion`, `temple`
  - 氛围：`ink wash atmosphere`, `misty mountains`

---

### Requirement: Skill Selection Logic

The system MUST invoke the corresponding skill based on user selection.

#### Scenario: 显式技能选择

- **GIVEN** 用户在节点中选择 `skill_type = "z-manga"`
- **WHEN** 执行提示词生成
- **THEN** 系统加载 `skills/z-manga/SKILL.md`
- **AND** 按照该技能的指令生成提示词

#### Scenario: 技能文件不存在

- **GIVEN** 用户选择的技能文件不存在
- **WHEN** 执行提示词生成
- **THEN** 系统输出警告日志
- **AND** 使用无技能的默认生成模式

---

### Requirement: Output Three Formats

Each skill MUST be able to generate three output formats.

#### Scenario: 英文逗号分隔格式

- **GIVEN** 技能生成完成
- **WHEN** 格式化输出
- **THEN** `prompt_english` 格式为：
  ```
  cinematic, 35mm film, Kodak Portra 400, portrait of a woman, soft lighting, golden hour
  ```

#### Scenario: JSON结构化格式

- **GIVEN** 技能生成完成
- **WHEN** 格式化输出
- **THEN** `prompt_json` 格式为：
  ```json
  {
    "subject": "portrait of a woman with freckles",
    "environment": "outdoor, golden hour lighting",
    "style": "cinematic, film photography",
    "tech_specs": "35mm lens, Kodak Portra 400, shallow depth of field",
    "negative_prompt": ""
  }
  ```

#### Scenario: 中英双语格式

- **GIVEN** 技能生成完成
- **WHEN** 格式化输出
- **THEN** `prompt_bilingual` 格式为：
  ```
  电影感(cinematic), 35mm胶片(35mm film), 柯达Portra 400(Kodak Portra 400), 女性肖像(portrait of a woman), 柔和光线(soft lighting)
  ```
