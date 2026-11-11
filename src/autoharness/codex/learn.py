"""Explicit learning command: same validation and store as automatic hooks."""
import argparse
import json
import os
import uuid
from pathlib import Path

from autoharness.codex import configure


def learn(project, episode):
    configure()
    from autoharness import config
    from autoharness.hook import spawn
    from autoharness.lib import layer, redact
    project = Path(project).resolve(strict=True)
    roots = {layer.PROJECT: layer._main_worktree_root(project) / os.environ['AUTOHARNESS_PROJECT_DIR'],
             layer.GLOBAL: layer.default_root(layer.GLOBAL)}
    text = Path(episode).read_text(encoding='utf-8')
    if len(text.encode()) > config.CAPTURE_MAX_WINDOW_BYTES:
        raise ValueError('episode exceeds capture byte budget')
    run_id = 'codex-learn-' + uuid.uuid4().hex
    verdicts = spawn.run(redact.redact(text), run_id, roots=roots)
    account = layer.state_dir(layer.PROJECT, roots[layer.PROJECT]) / 'runs' / f'{run_id}.json'
    record = json.loads(account.read_text(encoding='utf-8')) if account.exists() else {}
    if record.get('spawn_error'):
        raise RuntimeError(record['spawn_error'])
    return {'run_id': run_id, 'verdicts': verdicts, 'account': str(account)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(learn(args.project, args.input), ensure_ascii=False, default=str, indent=2))


if __name__ == '__main__':
    main()
