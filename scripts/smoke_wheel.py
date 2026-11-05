"""Inspect wheel and sdist, and import the wheel in a clean isolated venv."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("pyauthkit-*.whl"))
    archives = list((root / "dist").glob("pyauthkit-*.tar.gz"))
    if len(wheels) != 1 or len(archives) != 1:
        raise RuntimeError("expected exactly one wheel and one sdist")
    for artifact in (*wheels, *archives):
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        print(f"ARTIFACT {artifact.name} sha256:{digest}")
    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
        if not any(n == "pyauthkit/__init__.py" for n in names):
            raise RuntimeError("wheel has no package init")
        if any(n.startswith(("tests/", "docs/", "scripts/")) or "/fixtures/" in n for n in names):
            raise RuntimeError("test, fixture or source-document content leaked into wheel")
        if any(
            n.startswith("pyauthkit/")
            and ("fake" in Path(n).stem or Path(n).stem.startswith("test_"))
            for n in names
        ):
            raise RuntimeError("test-only fake or test module leaked into runtime wheel")
        for required in ("pyauthkit/application/engine.py", "pyauthkit/ports/authenticator.py"):
            if required not in names:
                raise RuntimeError(f"M2 runtime contract missing from wheel: {required}")
    with tarfile.open(archives[0], "r:gz") as tf:
        names = tf.getnames()
        if not any(name.endswith("/pyproject.toml") for name in names):
            raise RuntimeError("sdist missing pyproject.toml")
        if not any(name.endswith("/src/pyauthkit/__init__.py") for name in names):
            raise RuntimeError("sdist missing src package")
    with tempfile.TemporaryDirectory(prefix="pyauthkit-smoke-") as temp:
        temp_path = Path(temp)
        env_dir = temp_path / "venv"
        venv.EnvBuilder(with_pip=True).create(env_dir)
        binary = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [str(binary), "-m", "pip", "install", "--no-deps", str(wheels[0].resolve())],
            cwd=temp_path,
            check=True,
        )
        script = (
            "import pyauthkit, importlib.metadata, pathlib; "
            "from pyauthkit.domain.scope import TrustedScopeRef; "
            "from pyauthkit.application.engine import AuthenticationEngine; "
            "from pyauthkit.composition.registry import AuthenticatorRegistryBuilder; "
            "assert pyauthkit.__version__ == importlib.metadata.version('pyauthkit'); "
            "assert TrustedScopeRef('tenant-a').value == 'tenant-a'; "
            "path = pathlib.Path(pyauthkit.__file__).resolve(); "
            "assert 'site-packages' in str(path), path; "
            "print('ISOLATED WHEEL IMPORT PASS', path)"
        )
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        subprocess.run([str(binary), "-c", script], cwd=temp_path, env=env, check=True)
        # Execute a real PR-07 verifier in the isolated wheel environment on every OS.
        # No optional FastAPI/PostgreSQL/Redis package is installed in that venv.
        subprocess.run(
            [str(binary), str(root / "scripts" / "smoke_m4_wheel.py")],
            cwd=temp_path,
            env=env,
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
