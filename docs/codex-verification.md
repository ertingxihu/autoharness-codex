# Codex 本地验收记录

日期：2026-11-11（America/Los_Angeles）。最终安装版本：0.6.2。代码版本：`0e13a7d`。

## 环境与安装

- macOS，Python 3.13.2，Codex CLI 0.167.0，ChatGPT 登录。
- `codex plugin marketplace add` 注册本地源码，`codex plugin add` 安装缓存。
- 插件 ID：`autoharness-codex@autoharness-codex`。
- 最终 5 个钩子通过 Codex 原生信任界面启用。测试使用持久化的精确 hash，没有使用跳过钩子信任参数。
- 升级缓存版本后旧信任失效，重新信任最终版本后才执行最终测试。

## 先失败，再实现

11 项新增 Codex 回归先观察到失败再实现。覆盖路由、目录、后台隔离、递归防护、技能落盘、手写技能保护、无效输出、插件清单、手动入口、Codex 摘要、读取计数。

最终全量结果：`983 passed, 1 deselected`。排除的是需要 Claude 的上游 live 测试。新增和修改的 Python 文件通过 Ruff，`git diff --check` 通过。

## 真实闭环

测试在独立临时目录运行，全局技能和运行状态都重定向到该目录。为加快验证，工具调用阈值设为 1，正式默认仍为 50。

1. 启动真实 Codex 会话，要求通过 shell 读取 fixture.json，并给出“JSON 更新先写同目录临时文件，再原子替换”的项目规则。
2. 真实钩子触发后台 Codex。promoter 返回 `create ah-atomic-json-config: ok=true`，SKILL.md、sidecar、ledger 和证据文件落盘。
3. 新会话只提出 JSON 更新需求。模型发现并通过 `cat` 读取已有技能，正确复述原子替换规则。
4. 在最终 0.6.2 安装缓存上再运行真实会话，纠正规则为替换前先 `flush`、`fsync`。后台返回 `patch ah-atomic-json-config: ok=true`，仍只有 1 个技能，没有重复创建。
5. 最终 sidecar：`view=1`、`patch=1`、`use=0`。读取观察与实际遵循没有混为一谈。

精简的真实输出、最终技能和运行账户保存在 [codex-evidence.json](codex-evidence.json)。一次性测试目录在验收后删除，生产技能库没有混入测试技能。

## 范围与限制

已验证的是本机真实 Codex CLI 插件。桌面端的现有会话没有重载；需要新会话或重启应用以加载新插件。

没有把 CLI 的成功写成桌面交互验收，也没有验证 Windows、第三方模型 provider 或父会话缓存 fork。`use` 缺少统一可靠信号，所以默认暂停零使用毕业淘汰；简单显式读取计入 `view`。

钩子配置过程中本机共享 Codex 后台曾被重启；已恢复 `features.apps=true`，后续钩子配置使用 `--no-daemon` 独立进程。

## 参考

- [Codex 非交互执行](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex 钩子与信任规则](https://learn.chatgpt.com/docs/hooks)
- [上游 AutoHarness](https://github.com/tigerless-labs/autoharness)
