"""
Backend preflight checks.

Purpose:
- Fail fast when Python runtime is incompatible.
- Validate key dependency imports for backend startup.
- Check environment file and basic URL configuration.
"""

from __future__ import annotations

import importlib.util
import os
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List
from urllib.parse import urlparse

MIN_VERSION = (3, 11)
MAX_VERSION_EXCLUSIVE = (3, 14)

REQUIRED_MODULES = [
    "fastapi",
    "pydantic",
    "pydantic_settings",
    "sqlalchemy",
    "alembic",
    "redis",
    "jose",
    "passlib",
    "sentry_sdk",
]

DOCKER_INTERNAL_HOSTS = {"db", "redis", "rabbitmq"}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _check_python_version() -> CheckResult:
    version = sys.version_info[:3]
    if version < MIN_VERSION or version >= MAX_VERSION_EXCLUSIVE:
        return CheckResult(
            "python_version",
            False,
            (
                "Unsupported Python version "
                f"{version[0]}.{version[1]}.{version[2]}. "
                "Use Python >= 3.11 and < 3.14 for this backend."
            ),
        )

    return CheckResult(
        "python_version",
        True,
        f"Python {version[0]}.{version[1]}.{version[2]} is supported.",
    )


def _check_required_modules() -> List[CheckResult]:
    results: List[CheckResult] = []
    for module in REQUIRED_MODULES:
        found = importlib.util.find_spec(module) is not None
        results.append(
            CheckResult(
                f"module:{module}",
                found,
                "installed" if found else "missing",
            )
        )
    return results


def _check_env_file(repo_root: Path) -> CheckResult:
    env_file = repo_root / "backend" / ".env"
    if env_file.exists():
        return CheckResult("env_file", True, f"found at {env_file}")
    return CheckResult("env_file", False, f"missing file: {env_file}")


def _load_env_file_if_present(repo_root: Path) -> None:
    env_file = repo_root / "backend" / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _extract_host(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.hostname or ""
    except Exception:
        return ""


def _check_hostname_resolves(name: str, host: str) -> CheckResult:
    if not host:
        return CheckResult(name, False, "host is empty or URL is invalid")

    try:
        socket.getaddrinfo(host, None)
        return CheckResult(name, True, f"resolved host: {host}")
    except Exception:
        if host in DOCKER_INTERNAL_HOSTS:
            return CheckResult(
                name,
                True,
                (
                    f"host '{host}' not resolvable from current shell. "
                    "This is expected for docker-internal hostnames."
                ),
            )
        return CheckResult(name, False, f"cannot resolve host: {host}")


def _check_urls() -> List[CheckResult]:
    db_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "")

    results: List[CheckResult] = []
    if db_url:
        results.append(_check_hostname_resolves("database_host", _extract_host(db_url)))
    else:
        results.append(CheckResult("database_host", False, "DATABASE_URL not set"))

    if redis_url:
        results.append(_check_hostname_resolves("redis_host", _extract_host(redis_url)))
    else:
        results.append(CheckResult("redis_host", False, "REDIS_URL not set"))

    return results


def main() -> int:
    # scripts directory is backend/scripts, so repo root is two levels up.
    repo_root = Path(__file__).resolve().parents[2]
    _load_env_file_if_present(repo_root)

    results: List[CheckResult] = []
    results.append(_check_python_version())
    results.extend(_check_required_modules())
    results.append(_check_env_file(repo_root))
    results.extend(_check_urls())

    failures = [r for r in results if not r.ok]

    print("Backend preflight report")
    print("=" * 24)
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"[{status}] {r.name}: {r.detail}")

    if failures:
        print("\nPreflight failed. Fix FAIL items before starting backend.")
        return 1

    print("\nPreflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
