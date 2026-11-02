"""Small AST-based architecture fitness check for the PR-02 baseline.

This is a static guard, not a cryptographic or runtime sandbox.
"""

from __future__ import annotations

import argparse
import ast
import tomllib
from pathlib import Path

FORBIDDEN_EXTERNAL = {
    "boto3",
    "django",
    "fastapi",
    "flask",
    "pyiamkit",
    "redis",
    "sqlalchemy",
    "starlette",
}
FORBIDDEN_LAYER_IMPORTS: dict[str, set[str]] = {
    "domain": {"application", "ports", "adapters", "infrastructure"},
    "application": {"adapters", "infrastructure"},
    "ports": {"adapters", "infrastructure"},
}


def imported_modules(source: str, package_name: str) -> set[str]:
    """Return literal import targets including resolvable relative imports."""
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package_name.split(".")
                prefix = parts[: len(parts) - node.level + 1]
                module = ".".join([*prefix, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            if module:
                imports.add(module)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            imports.add(node.args[0].value)
    return imports


def check_tree(src: Path, project: Path) -> list[str]:
    """Return issues found in owned source modules and packaging metadata."""
    errors: list[str] = []
    if not src.is_dir():
        return [f"package directory missing: {src}"]
    for path in sorted(src.rglob("*.py")):
        relative = path.relative_to(src)
        parts = relative.parts
        package_parts = ["pyauthkit", *parts[:-1]]
        package_name = ".".join(package_parts)
        try:
            imports = imported_modules(path.read_text(encoding="utf-8"), package_name)
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"{path}: invalid source: {exc}")
            continue
        layer = parts[0] if len(parts) > 1 else ""
        for module in imports:
            if module.split(".")[0] in FORBIDDEN_EXTERNAL:
                errors.append(f"{path}: forbidden external import {module}")
            segments = module.split(".")
            if (
                len(segments) > 1
                and segments[0] == "pyauthkit"
                and segments[1] in FORBIDDEN_LAYER_IMPORTS.get(layer, set())
            ):
                errors.append(f"{path}: forbidden {layer} -> {module} dependency")
    if project.is_file():
        metadata = tomllib.loads(project.read_text(encoding="utf-8"))
        for value in metadata.get("project", {}).get("dependencies", []):
            normalized = value.lower().replace("_", "-")
            if any(normalized.startswith(name) for name in FORBIDDEN_EXTERNAL):
                errors.append(f"{project}: forbidden required dependency {value}")
    else:
        errors.append(f"project metadata missing: {project}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--src", type=Path, default=root / "src/pyauthkit")
    parser.add_argument("--project", type=Path, default=root / "pyproject.toml")
    args = parser.parse_args()
    errors = check_tree(args.src, args.project)
    for error in errors:
        print("ARCHITECTURE VIOLATION:", error)
    if errors:
        return 1
    print("Architecture static fitness passed (limited to literal imports and metadata).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
