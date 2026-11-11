# AutoHarness for Codex

把真实 Codex 会话中的有效经验整理成技能，在后续会话中召回，并维护自己生成的技能库。

这是 [tigerless-labs/autoharness](https://github.com/tigerless-labs/autoharness) 的 Codex fork，保留 MIT 许可证和上游的确定性校验、证据记录、去重、归档逻辑。原版 Claude 文档保留在 [README.upstream.md](README.upstream.md)。

## 安装

要求：macOS 或 Linux、Python 3.11+（`python3`）、已登录的 Codex CLI。已在 macOS、Python 3.13.2、Codex CLI 0.167.0 上验证。

```sh
git clone https://github.com/ertingxihu/autoharness-codex.git
cd autoharness-codex
codex plugin marketplace add "$PWD"
codex plugin add autoharness-codex@autoharness-codex
```

随后在 Codex CLI 输入 `/hooks`，检查并信任本插件的 5 个钩子。重新打开会话。桌面端也需要新会话重新加载插件；旧会话不会补跑启动钩子。

无需另配 API Key，后台使用本机 Codex 登录。后台会消耗当前账号的模型额度。

## 怎么用

正常使用 Codex 即可。默认累计 50 次工具调用后，在回合结束时启动后台学习；会话结束时也会处理未学习的尾部。纯聊天不会增加工具调用计数。没有可复用经验时，可以不生成技能。

手动学习：在新会话选择插件的 `learn` 技能，或输入 `$learn` 并说明要提炼本次会话的经验。也可以把已脱敏的片段保存为文本后运行：

```sh
PYTHONPATH="$PWD/src" python3 -m autoharness.codex.learn --project /path/to/project --input /path/to/episode.txt
```

检查返回的 `verdicts`；只有 `ok: true` 才表示通过并落盘。输入文件用完即可删除。

| 内容 | 默认位置 |
| --- | --- |
| 当前项目的技能 | `<project>/.agents/skills/ah-*/SKILL.md` |
| 跨项目的技能 | `~/.agents/skills/ah-*/SKILL.md` |
| 运行记录、队列、归档 | `$CODEX_HOME/autoharness/`，通常为 `~/.codex/autoharness/` |
| 学习依据 | 技能目录内 `.ledger.jsonl` 和 `references/evidence-*.md` |

每个项目的状态按路径摘要分开存放。原有手写或其他来源的技能不会被修改。后台只返回结构化建议，Python 校验器是技能库的写入者。

## Codex 适配

- 原生插件清单、生命周期钩子、`learn` 技能。
- 使用 `codex exec --output-schema`，ChatGPT 登录可用；无需 Claude。
- 后台采用只读沙箱、300 秒超时、临时目录、无持久会话，并关闭用户配置及钩子，避免递归学习。
- 默认跟随用户 Codex 配置中的模型；可用 `AUTOHARNESS_CODEX_MODEL` 指定。自定义第三方 provider 配置目前不会自动复制到后台，当前验证范围是 OpenAI/ChatGPT 登录。
- 原始会话按字节水位截取并脱敏；Codex 旧消息摘要只保留用户/助手文本，不把开发者指令或工具输出当摘要。
- 后续会话通过原生技能发现和启动时索引召回。
- 显式 `read_file`、简单 `cat` 读取记为 `view`，不伪称 `use`。Codex 没有统一的技能执行信号，默认暂停“零使用毕业淘汰”；容量限制和主动合并仍保留。复杂 shell/组合工具中的读取可能不计数。
- 当前采用脱敏片段载体 `bundle`，没有宣称支持继承父会话缓存的 fork 载体。

## 可选设置

在启动 Codex 前设置环境变量。上游其余 `AUTOHARNESS_*` 设置仍适用。

| 变量 | 默认 | 用途 |
| --- | --- | --- |
| `AUTOHARNESS_REFLECT_EVERY_N` | `50` | 工具调用达到多少次后学习 |
| `AUTOHARNESS_CODEX_MODEL` | 用户配置模型 | 后台模型 |
| `AUTOHARNESS_CODEX_TIMEOUT_S` | `300` | 单次后台最长秒数 |
| `AUTOHARNESS_SKILL_PREFIX` | `ah-` | 新建技能的名称前缀 |
| `AUTOHARNESS_DISABLE_GLOBAL` | `0` | 设为 `1` 时只写项目技能 |
| `AUTOHARNESS_GLOBAL_ROOT` | `~/.agents` | 全局技能根目录 |
| `AUTOHARNESS_STATE_HOME` | `$CODEX_HOME/autoharness` | 状态目录 |
| `AUTOHARNESS_GRADUATION_SUSPENDED` | `1` | 暂停基于零使用的毕业淘汰 |

## 更新与卸载

```sh
git pull --ff-only
codex plugin add autoharness-codex@autoharness-codex
```

版本号变化后会安装新缓存。检查 `/hooks` 是否需要重新信任，再打开新会话。

```sh
codex plugin remove autoharness-codex@autoharness-codex
codex plugin marketplace remove autoharness-codex
```

卸载停止后续学习，保留已学技能和证据，方便恢复。

## 开发验证

```sh
uv run --with pytest pytest -q -m 'not live'
uv run --with ruff ruff check src/autoharness/codex tests/test_codex.py
```

真实验证记录见 [docs/codex-verification.md](docs/codex-verification.md)。单元测试与真实模型验收分开记录。上游 `live` 测试需要 Claude，不属于 Codex 验收。
