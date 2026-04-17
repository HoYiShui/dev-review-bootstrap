#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_repo_hook(start: Path) -> tuple[Path, Path] | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        hook = candidate / ".codex" / "workflow" / "hooks" / "post_stop.sh"
        if hook.is_file():
            return candidate, hook
    return None


def main() -> int:
    if os.environ.get("DEV_REVIEW_HOOK_ACTIVE") == "1":
        return 0

    found = find_repo_hook(Path.cwd())
    if found is None:
        return 0

    repo_root, hook = found
    result = subprocess.run(
        ["bash", str(hook)],
        cwd=repo_root,
        env=os.environ.copy(),
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
