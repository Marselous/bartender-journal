from __future__ import annotations

import subprocess


def main() -> None:
    subprocess.check_call(["alembic", "upgrade", "head"])


if __name__ == "__main__":
    main()

