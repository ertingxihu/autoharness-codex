import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from autoharness.hook import spawn


def test_codex_command_uses_worker(monkeypatch):
    monkeypatch.setenv('AUTOHARNESS_HOST', 'codex')
    command = spawn.build_command(agent='autoharness:reflector', claude_bin='claude')
    assert command[:3] == [sys.executable, '-m', 'autoharness.codex.worker']
    assert 'reflector' in command


def test_codex_defaults_use_agents_and_external_state(tmp_path, monkeypatch):
    from autoharness.codex import configure
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / '.codex'))
    for key in ('AUTOHARNESS_GLOBAL_ROOT', 'AUTOHARNESS_STATE_HOME', 'AUTOHARNESS_SKILL_PREFIX'):
        monkeypatch.delenv(key, raising=False)
    configure()
    assert os.environ['AUTOHARNESS_GLOBAL_ROOT'] == str(tmp_path / '.agents')
    assert os.environ['AUTOHARNESS_PROJECT_DIR'] == '.agents'
    assert os.environ['AUTOHARNESS_STATE_HOME'] == str(tmp_path / '.codex/autoharness')
    assert os.environ['AUTOHARNESS_SKILL_PREFIX'] == 'ah-'


def test_hook_uses_payload_cwd_not_shell_cwd(tmp_path, monkeypatch):
    from autoharness.codex.hook import handle
    from autoharness.lib import counters
    monkeypatch.setenv('AUTOHARNESS_GLOBAL_ROOT', str(tmp_path / 'global'))
    monkeypatch.setenv('AUTOHARNESS_STATE_HOME', str(tmp_path / 'state'))
    project = tmp_path / 'project'
    project.mkdir()
    handle({'hook_event_name': 'PreToolUse', 'session_id': 's1', 'cwd': str(project),
            'tool_name': 'exec_command', 'tool_input': {'cmd': 'pwd'}})
    assert counters.session_count('s1', project / '.agents') == 1


def test_child_hook_does_not_count(tmp_path, monkeypatch):
    from autoharness.codex.hook import handle
    monkeypatch.setenv('AUTOHARNESS_CHILD_SESSION', '1')
    assert handle({'hook_event_name': 'Stop', 'cwd': str(tmp_path)})['ignored']


def test_stage_output_lands_and_preserves_handwritten(tmp_path):
    from autoharness.codex.worker import stage_output
    from autoharness.hook import promoter
    roots = {'project': tmp_path / 'p', 'global': tmp_path / 'g'}
    body = '---\nname: ah-json\ndescription: Use when writing JSON files.\ncategory: testing\n---\nWrite JSON atomically with a same-directory temporary file.\n'
    output = {'intents': [dict(action='create', name='ah-json', body=body,
                              reason='Avoid truncated writes.', evidence='Write JSON atomically.', level='project')]}
    stage_output(output, 'codex-test', roots['project'])
    result = promoter.drain('codex-test', roots=roots)
    assert (roots['project'] / 'skills/ah-json/SKILL.md').read_text().startswith('---')
    assert result
    manual = roots['project'] / 'skills/manual/SKILL.md'
    manual.parent.mkdir(parents=True)
    manual.write_text(body)
    stage_output({'intents': [dict(action='delete', name='manual', reason='cleanup', evidence='obsolete')]}, 'codex-test-2', roots['project'])
    promoter.drain('codex-test-2', roots=roots)
    assert manual.exists()


def test_stage_output_rejects_invalid_shape(tmp_path):
    from autoharness.codex.worker import stage_output
    with pytest.raises(ValueError):
        stage_output({'intents': [None]}, 'bad-run', tmp_path)


def test_child_command_is_bounded_and_isolated(tmp_path):
    from autoharness.codex.worker import build_command
    command = build_command(tmp_path / 'schema.json', tmp_path / 'answer.json', tmp_path)
    assert '--ignore-user-config' in command
    assert '--ephemeral' in command
    assert command[command.index('--sandbox') + 1] == 'read-only'
    assert '--dangerously-bypass-approvals-and-sandbox' not in command
    assert 'features.hooks=false' in command


def test_plugin_has_codex_entrypoints():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text())
    assert manifest['name'] == 'autoharness-codex'
    hooks = json.loads((root / manifest['hooks']).read_text())['hooks']
    assert {'SessionStart', 'PreToolUse', 'Stop'} <= set(hooks)
    assert (root / manifest['skills'] / 'learn/SKILL.md').exists()


def test_manual_learn_cli_reaches_pipeline(tmp_path, monkeypatch):
    from autoharness.codex.learn import learn
    episode = tmp_path / 'episode.txt'
    episode.write_text('Use atomic JSON writes.')
    seen = {}
    monkeypatch.setattr(spawn, 'run', lambda text, rid, **kw: seen.update(text=text, roots=kw['roots']) or [])
    learn(tmp_path, episode)
    assert seen['text'] == 'Use atomic JSON writes.'
    assert seen['roots']['project'] == tmp_path / '.agents'
