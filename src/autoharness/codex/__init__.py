"""Codex host defaults; import before the shared configuration module."""
import os
from pathlib import Path


def configure():
    os.environ['AUTOHARNESS_HOST'] = 'codex'
    defaults = {
        'AUTOHARNESS_GLOBAL_ROOT': str(Path.home() / '.agents'),
        'AUTOHARNESS_PROJECT_DIR': '.agents',
        'AUTOHARNESS_STATE_HOME': str(Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex') / 'autoharness'),
        'AUTOHARNESS_SKILL_PREFIX': 'ah-',
        # Codex shell reads are observations, not proof of adherence.
        'AUTOHARNESS_GRADUATION_SUSPENDED': '1',
        'AUTOHARNESS_CARRIER': 'bundle',
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)
