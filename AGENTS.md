# 本仓规矩（写给所有在这个仓里干活的 agent）

## 提交

- 用仓库已配置的身份（`git config user.name` / `user.email`）。⛔ 不要换成工具身份、机器人邮箱或占位名。
- ⛔ 不要加 `Co-authored-by:` 尾注。
- ⛔ 不要在没人要求时自己提交：改动留在工作区，等人看过。

## 分支与工作树

- ⛔ 不要建分支、worktree、checkpoint ref，除非明确要求。
- 用完清干净：不留 `.git/worktrees`、`refs/copilot/*`、指向旧提交的游离工作树。

## 文件

- `docs/` 是对外文档位。⛔ 往里放评审记录、会议纪要、任务分派记录、过程日志。
- ⛔ 在公开文件里提未发布项目、内部工具、私人来源、个人背景。
- 随包发布的文字要读起来像文档，不像工作流水账。
- 字体与第三方资产：本仓捆了第三方字体，改动 `assets/` 或 `references/` 里的字体前先读 `THIRD_PARTY_NOTICES.md`。⛔ 删掉其中任何一条署名。

## 中英两版

- `README.md` 是中文正本，`README.en.md` 是英文版。改一版必须同改另一版，否则另一边就是过期读数。
- 切换行固定在首行：中文版 `中文 · [English](README.en.md)`，英文版 `[中文](README.md) · English`。

## 推之前

本仓装了 `pre-push`：推的时候自动跑一次对外体检（文件 + 提交身份），不过就不推。⛔ 拿 `--no-verify` 绕过去；绕了请自己补跑一次：

```bash
node <对外体检工具>/fluensand.js outward ~/GitHub/lesciotia --git
```
