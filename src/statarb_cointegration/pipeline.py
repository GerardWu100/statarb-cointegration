"""Execute notebook-derived step scripts in original notebook order."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ProjectConfig, build_execution_context


def run_pipeline(context_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run each generated step script with a shared notebook-style context.

    Steps execute in lexicographic filename order so numeric prefixes preserve
    notebook section order. Each script mutates the same ``context`` dict.
    """
    config = ProjectConfig()
    context = build_execution_context(config=config, context_overrides=context_overrides)

    for step_path in sorted(config.steps_dir.glob('*.py')):
        context['__file__'] = str(step_path)
        # exec keeps notebook semantics: later steps see names defined earlier.
        exec(compile(step_path.read_text(), str(step_path), 'exec'), context)

    return context
