"""Coverage instrumentation hook for triz-workshop subprocess scripts.

This module is imported at the very top of `scripts/next_action.py` (and any
other script we want measured under `--cov` for subprocess invocations).

Mechanism (per coverage.py docs, "Measuring sub-processes"):

  - When the parent test process sets `COVERAGE_PROCESS_START` in the env to
    point at a coverage config file, child Python processes are expected to
    call `coverage.process_startup()` early enough that the coverage
    instrumentation can patch the trace function before user code runs.
  - The standard mechanism is a `sitecustomize.py` on the path (only loaded
    automatically when it lives in a real `site-packages/`). For our
    layout — where `scripts/` is the source root and tests just put it on
    `PYTHONPATH` — `sitecustomize.py` does NOT auto-load. We instead import
    THIS module from the script entry point as the first executable line,
    which is reliable across direct invocation, `python -m`, and pytest's
    `subprocess.run([sys.executable, ...])`.

Behavior:
  - If `COVERAGE_PROCESS_START` is unset (the common case in production),
    this module does nothing — no import attempted, no side effects.
  - If it IS set but `coverage` isn't installed, the ImportError is
    swallowed; the script continues normally.
  - Otherwise `coverage.process_startup()` is invoked, which reads the
    config file and starts measuring.

Keep this file dependency-free and side-effect-free in the unset case so
that production runs of next_action.py pay zero cost.
"""

from __future__ import annotations

import os as _os
import sys as _sys

if _os.environ.get("COVERAGE_PROCESS_START"):
    try:
        import coverage as _coverage  # type: ignore[import-untyped]
    except ImportError:
        # coverage.py not installed; nothing to do.
        pass
    else:
        try:
            _coverage.process_startup()
        except Exception:
            # Never let coverage bring down the process. Swallow silently
            # so a broken coverage config can't violate next_action.py's
            # strict CLI contract (stderr empty, exit 0).
            pass

# Don't pollute the importing module's namespace with our internals.
del _os, _sys
