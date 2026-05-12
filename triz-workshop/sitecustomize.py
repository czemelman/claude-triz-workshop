"""Subprocess-coverage shim for triz-workshop.

Python imports `sitecustomize` automatically at interpreter startup if it is
present on `sys.path`. The pytest conftest puts `triz-workshop/` on the
PYTHONPATH for child processes, so when next_action.py is launched via
subprocess.run([sys.executable, ...]) and `COVERAGE_PROCESS_START` is set,
this module fires `coverage.process_startup()` which initializes coverage
in the child using the .coveragerc referenced by that env var.

This is the standard approach documented in coverage.py for measuring
subprocess code paths (see coverage.py docs: "Measuring sub-processes").

If coverage is not installed, or COVERAGE_PROCESS_START is not set, the
import of coverage.process_startup is a no-op (returns immediately), so
this file is safe to keep on the path in non-coverage runs.
"""

from __future__ import annotations

try:
    import coverage  # type: ignore[import-untyped]
except ImportError:
    # coverage.py not installed in this environment; nothing to do.
    pass
else:
    # process_startup() itself short-circuits when COVERAGE_PROCESS_START
    # is unset, so this is safe to call unconditionally.
    coverage.process_startup()
