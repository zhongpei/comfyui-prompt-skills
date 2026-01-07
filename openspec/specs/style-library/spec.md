# style-library Specification

## Purpose
TBD - created by archiving change add-prompt-skills-plugin. Update Purpose after archive.
## Requirements
### Requirement: Style Database Structure

The system MUST provide a structured JSON style database.

#### Scenario: 风格库文件存在

- **GIVEN** 插件安装完成
- **WHEN** 检查 `data/z_styles_db.json`
- **THEN** 文件存在且为有效JSON格式

#### Scenario: 风格库Schema验证

- **GIVEN** 风格库JSON文件
- **WHEN** 系统加载并验证
- **THEN** JSON结构符合以下Schema：
  ```json
  {
    "meta": {
      "model_version": "string",
      "last_updated": "date string"
    },
    "styles": {
      "photography": [...],
      "illustration": [...],
      "design": [...]
    }
  }
  ```

#### Scenario: 单个风格项结构

- **GIVEN** 风格库中的一个风格项
- **WHEN** 解析该项
- **THEN** 必须包含以下字段：
  - `id` (string): 唯一标识符
  - `name` (string): 英文名称
  - `keywords` (array): 触发关键词列表
- **AND** 可选包含：
  - `name_zh` (string): 中文名称
  - `tech_specs` (string): 技术参数
  - `model_target` (array): 适用模型列表

---

### Requirement: Photography Styles

The style library MUST contain photography styles.

#### Scenario: 胶片摄影风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `photography` 类别
- **THEN** 包含 `analog_film` 风格，关键词包括：
  - `shot on film`
  - `film grain`
  - `Kodak Portra 400`
  - `35mm`

#### Scenario: 电影感风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `photography` 类别
- **THEN** 包含 `cinematic` 风格，关键词包括：
  - `cinematic lighting`
  - `anamorphic lens`
  - `movie still`
  - `dramatic lighting`

#### Scenario: 商业人像风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `photography` 类别
- **THEN** 包含 `studio_portrait` 风格，关键词包括：
  - `studio lighting`
  - `softbox`
  - `85mm lens`
  - `sharp focus`

#### Scenario: 街头摄影风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `photography` 类别
- **THEN** 包含 `street` 风格，关键词包括：
  - `street photography`
  - `candid`
  - `urban`
  - `documentary style`

---

### Requirement: Illustration Styles

The style library MUST contain illustration styles.

#### Scenario: 复古动漫风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `illustration` 类别
- **THEN** 包含 `vintage_anime` 风格，关键词包括：
  - `1990s anime screenshot`
  - `cel shaded`
  - `hand drawn`
  - `VHS quality`

#### Scenario: 吉卜力风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `illustration` 类别
- **THEN** 包含 `ghibli` 风格，关键词包括：
  - `Ghibli style`
  - `detailed background painting`
  - `watercolor`
  - `pastoral`

#### Scenario: 矢量插画风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `illustration` 类别
- **THEN** 包含 `vector` 风格，关键词包括：
  - `flat color`
  - `vector art`
  - `thick outline`
  - `minimalist`

#### Scenario: 水墨画风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `illustration` 类别
- **THEN** 包含 `ink_wash` 风格，关键词包括：
  - `ink wash painting`
  - `Chinese brush painting`
  - `sumi-e`
  - `traditional Chinese art`

---

### Requirement: Design Styles

The style library MUST contain 3D design styles.

#### Scenario: 盲盒公仔风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `design` 类别
- **THEN** 包含 `pop_mart` 风格，关键词包括：
  - `pop mart style`
  - `chibi`
  - `3d render`
  - `PVC texture`
  - `glossy finish`

#### Scenario: 体素艺术风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `design` 类别
- **THEN** 包含 `voxel` 风格，关键词包括：
  - `voxel art`
  - `isometric view`
  - `c4d render`
  - `low poly`

#### Scenario: 黏土材质风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `design` 类别
- **THEN** 包含 `clay` 风格，关键词包括：
  - `clay material`
  - `claymation`
  - `octane render`
  - `soft lighting`

---

### Requirement: Chinese Cultural Styles

The style library MUST contain Chinese cultural element styles.

#### Scenario: 汉服风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `chinese_culture` 类别
- **THEN** 包含 `hanfu` 风格，关键词包括：
  - `hanfu`
  - `traditional Chinese dress`
  - `Tang dynasty style`
  - `silk robes`

#### Scenario: 仙侠风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `chinese_culture` 类别
- **THEN** 包含 `xianxia` 风格，关键词包括：
  - `xianxia style`
  - `immortal cultivator`
  - `flowing robes`
  - `celestial`
  - `cloud mountains`

#### Scenario: 武侠风格

- **GIVEN** 风格库已加载
- **WHEN** 查询 `chinese_culture` 类别
- **THEN** 包含 `wuxia` 风格，关键词包括：
  - `wuxia style`
  - `martial artist`
  - `ancient China`
  - `bamboo forest`

---

### Requirement: User Style Extension

The system MUST support user manual extension of the style library.

#### Scenario: 自定义风格目录

- **GIVEN** 用户想添加自定义风格
- **WHEN** 检查目录结构
- **THEN** 存在 `data/custom/` 目录
- **AND** 目录中可放置用户自定义的JSON文件

#### Scenario: 加载自定义风格

- **GIVEN** 用户在 `data/custom/` 放置了 `my_styles.json`
- **AND** 文件符合风格库Schema
- **WHEN** 系统加载风格库
- **THEN** 自定义风格被合并到主风格库中
- **AND** 可在技能中使用

#### Scenario: 自定义文件格式错误

- **GIVEN** 用户放置的JSON文件格式不正确
- **WHEN** 系统加载风格库
- **THEN** 系统跳过该文件
- **AND** 输出警告日志：`"Failed to load custom style file: my_styles.json - Invalid JSON format"`
- **AND** 其他风格正常加载

---

### Requirement: Style Search

The system MUST support searching for matching styles in the style library.

#### Scenario: 关键词搜索

- **GIVEN** 风格库已加载
- **WHEN** LLM搜索关键词 `"电影感"`
- **THEN** 返回 `cinematic` 风格
- **AND** 包含所有相关的 `keywords` 和 `tech_specs`

#### Scenario: 类别筛选

- **GIVEN** 风格库已加载
- **WHEN** LLM搜索类别 `"photography"` 下的风格
- **THEN** 仅返回 `photography` 类别中的风格
- **AND** 不包含其他类别的结果

#### Scenario: 模型适配筛选

- **GIVEN** 风格项包含 `model_target: ["z-image-turbo"]`
- **AND** 当前目标模型为 `SDXL`
- **WHEN** LLM搜索该风格
- **THEN** 该风格被标记为"不推荐"
- **OR** 被排除在结果之外

