"""Translate Codex hook events to the shared deterministic pipeline."""
import json
import os
import sys
from pathlib import Path

from autoharness.codex import configure


def handle(event):
    if os.environ.get('AUTOHARNESS_CHILD_SESSION') or not isinstance(event, dict):
        return {'ignored': True}
    configure()
    from autoharness.hook import dispatch, on_skill_call
    from autoharness.lib import layer
    cwd = event.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_dir():
        return {'ignored': True, 'reason': 'missing project cwd'}
    # Do not trust the hook process cwd: it may be a nested shell directory.
    roots = {layer.PROJECT: layer._main_worktree_root(cwd) / os.environ['AUTOHARNESS_PROJECT_DIR'],
             layer.GLOBAL: layer.default_root(layer.GLOBAL)}
    result = dispatch.dispatch(event, roots=roots)
    if event.get('hook_event_name') == 'SessionStart':
        context = (result.get('result') or {}).get('context')
        if context:
            paths = '\n'.join(f'{lyr}: {layer.skills_dir(lyr, root)}/<name>/SKILL.md' for lyr, root in roots.items())
            result['result']['context'] += '\nLoad matching skills by reading their SKILL.md:\n' + paths
    # Track only explicit file read tools. Shell commands cannot prove a skill was followed.
    if event.get('hook_event_name') == 'PostToolUse' and event.get('tool_name', '').split('.')[-1] == 'read_file':
        args = event.get('tool_input') or {}
        if isinstance(args, dict) and isinstance(args.get('path'), str):
            on_skill_call.on_skill_read({'tool_input': {'file_path': args['path']}}, roots=roots)
    return result


def main():
    try:
        event = json.load(sys.stdin)
        result = handle(event)
        from autoharness.hook.dispatch import _emit
        _emit(result)
    except Exception as exc:
        print(f'autoharness-codex hook: {type(exc).__name__}: {exc}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
