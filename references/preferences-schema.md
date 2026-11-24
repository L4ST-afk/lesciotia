# EXTEND.md Schema

Preferences file for 来雪亭Lesciotia.

## 文件位置（按序第一个命中生效）

路径表见 `SKILL.md` 的 Step 0 与 `references/workflow.md`（配置目录与 skill 同名，无旧名兼容位）。

没有就按默认值走，首次使用不阻塞。

## Full Schema

```yaml
# 来雪亭Lesciotia preferences

## Defaults
default_exit: image           # image | html | editable   （A / B / C）
style: blueprint              # 风格键（见 references/styles-unified.md）或 "custom"
audience: general             # beginners | intermediate | experts | executives | general
language: auto                # auto | en | zh | ja | ...
review: true                  # true = 出产物前先审逐页记录
preferred_image_backend: auto # auto | ask | <backend-id>

## Custom Dimensions (only when style: custom)
dimensions:
  texture: clean
  mood: professional
  typography: geometric
  density: balanced

## Custom Styles (optional)
custom_styles:
  my-style:
    texture: organic
    mood: warm
    typography: humanist
    density: minimal
    description: "My custom warm style"
```

## 字段说明

| 字段 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `default_exit` | string | `image` | 确认门里 Q0 的默认选项。`image`=A 影像、`html`=B 网页、`editable`=C 可编辑。**只是默认值，不跳过确认** |
| `style` | string | `blueprint` | 风格键（21 个之一）或 `custom`；写不在表里的名字会被当作 `custom` |
| `audience` | string | `general` | 默认受众 |
| `language` | string | `auto` | 输出语言，`auto` = 跟随输入 |
| `review` | boolean | `true` | 是否默认先审逐页记录（确认门仍会问一次，用户可当场改） |
| `preferred_image_backend` | string | `auto` | 仅 A 出口用。`auto`=runtime 原生工具优先，只有一个外部后端就用它，多个才问；`ask`=每次问；`<backend-id>`=钉住某后端，不可用时回落 `auto` |
| `dimensions` | map | — | 仅 `style: custom` 时生效，四维取值见 `styles-unified.md` |
| `custom_styles` | map | — | 可复用的四维组合，`style: <名字>` 即可引用 |

## 常见一行改法

```yaml
default_exit: html          # 以后默认做能讲的网页 deck
style: swiss-grid           # 默认风格换成瑞士网格
review: false               # 跳过逐页评审（确认门仍会问）
language: zh                # 固定中文输出
preferred_image_backend: ask # 每次出图前确认后端
```

## 与确认门的关系

`EXTEND.md` 只提供**默认值**。Step 2 的六问照样问；用户当场的选择覆盖文件值，并把结果回写 `analysis.md`（不回写 EXTEND.md——除非用户明确要改默认）。
