"""Translate Codex hook events to the shared deterministic pipeline."""
import json
import os
import shlex
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
    # Views are evidence of reading, not proof that the model followed a skill.
    if event.get('hook_event_name') == 'PostToolUse':
        args = event.get('tool_input') or {}
        tool = event.get('tool_name', '').split('.')[-1]
        response = event.get('tool_response') or {}
        failed = isinstance(response, dict) and response.get('exit_code', 0) not in (0, None)
        paths = []
        if not failed and isinstance(args, dict):
            if tool == 'read_file' and isinstance(args.get('path'), str):
                paths = [args['path']]
            elif tool in ('exec_command', 'Bash', 'shell_command'):
                command = args.get('cmd') or args.get('command') or ''
                try:
                    words = shlex.split(command)
                except (ValueError, TypeError):
                    words = []
                if words and words[0] == 'cat' and not any(c in command for c in ';|&><`$'):
                    paths = [word for word in words[1:] if not word.startswith('-')]
            for path in paths:
                file_path = str((Path(args.get('workdir') or cwd) / path).resolve())
                on_skill_call.on_skill_read({'tool_input': {'file_path': file_path}}, roots=roots)
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
