---
name: learn
description: Use when asked to learn reusable lessons from this Codex chat.
---

Review this conversation for a concrete, reusable lesson. If none exists, say so.
Use the plugin's Python helper to run a bounded reflection from a UTF-8 text file containing only the relevant user messages, observed actions and results. Remove secrets and unrelated information first.
Resolve the plugin root as three parents above this SKILL.md directory. Run:

```sh
PYTHONPATH="<plugin-root>/src" python3 -m autoharness.codex.learn --project "<current-project>" --input "<episode-file>"
```

Read the returned promoter verdict before claiming a skill was saved. Delete the temporary episode file after completion. The helper uses the current Codex login and the same validation pipeline as automatic background learning.
