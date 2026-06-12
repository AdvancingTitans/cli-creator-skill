from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SKILL_NAME = "cli-creator"


def default_target() -> Path:
    return Path.home() / ".codex" / "skills"


def skill_source() -> Path:
    return Path(__file__).resolve().parent / "skills" / SKILL_NAME


def install(target: Path, force: bool = False) -> Path:
    src = skill_source()
    if not src.exists():
        raise FileNotFoundError(f"Skill files were not found in the package: {src}")

    dest = target.expanduser().resolve() / SKILL_NAME
    if dest.exists():
        if not force:
            raise FileExistsError(
                f"{dest} already exists. Re-run with --force to overwrite it."
            )
        shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli-creator-skill",
        description="Install the cli-creator agent skill.",
    )
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install", help="Install the skill locally.")
    install_parser.add_argument(
        "--target",
        type=Path,
        default=default_target(),
        help="Directory that contains skill folders. Default: ~/.codex/skills",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing cli-creator skill directory.",
    )

    args = parser.parse_args(argv)
    if args.command in (None, "install"):
        try:
            dest = install(args.target, force=args.force)
        except Exception as exc:
            print(f"Install failed: {exc}", file=sys.stderr)
            return 1
        print(f"Installed {SKILL_NAME} to {dest}")
        return 0

    parser.print_help()
    return 0
