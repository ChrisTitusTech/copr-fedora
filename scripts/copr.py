#!/usr/bin/env python3
"""Validate package recipes and publish them to Fedora COPR."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / ".copr" / "project.toml"
PACKAGES_DIR = ROOT / "packages"
SRPM_MAKEFILE = ROOT / ".copr" / "Makefile"
PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._-]*$")
ZERO_SHA_RE = re.compile(r"^0+$")
MANAGED_PATHS = (
    ".copr/",
    "scripts/",
    ".github/workflows/copr.yml",
)


class CoprAutomationError(RuntimeError):
    """Raised for an expected validation or publishing failure."""


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    chroots: tuple[str, ...]
    description: str
    instructions: str
    homepage: str
    clone_url: str
    branch: str


@dataclass(frozen=True)
class PackageDefinition:
    name: str
    directory: Path
    spec: Path


def _required_string(table: dict[str, Any], key: str, section: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CoprAutomationError(f"{section}.{key} must be a non-empty string")
    return value.strip()


def load_project_config(path: Path = PROJECT_FILE) -> ProjectConfig:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CoprAutomationError(f"cannot read {path}: {exc}") from exc

    project = data.get("project")
    repository = data.get("repository")
    if not isinstance(project, dict) or not isinstance(repository, dict):
        raise CoprAutomationError("project.toml requires [project] and [repository] tables")

    raw_chroots = project.get("chroots")
    if (
        not isinstance(raw_chroots, list)
        or not raw_chroots
        or any(not isinstance(item, str) or not item.strip() for item in raw_chroots)
    ):
        raise CoprAutomationError("project.chroots must be a non-empty string array")

    return ProjectConfig(
        name=_required_string(project, "name", "project"),
        chroots=tuple(dict.fromkeys(item.strip() for item in raw_chroots)),
        description=_required_string(project, "description", "project"),
        instructions=_required_string(project, "instructions", "project"),
        homepage=_required_string(project, "homepage", "project"),
        clone_url=_required_string(repository, "clone_url", "repository"),
        branch=_required_string(repository, "branch", "repository"),
    )


def validate_package_name(name: str) -> str:
    if not PACKAGE_NAME_RE.fullmatch(name):
        raise CoprAutomationError(f"invalid package name: {name!r}")
    return name


def discover_packages(
    names: Iterable[str] | None = None,
    packages_dir: Path = PACKAGES_DIR,
) -> list[PackageDefinition]:
    if names is None:
        selected = sorted(path.name for path in packages_dir.iterdir() if path.is_dir())
    else:
        selected = sorted(dict.fromkeys(validate_package_name(name) for name in names))

    packages: list[PackageDefinition] = []
    for name in selected:
        validate_package_name(name)
        directory = packages_dir / name
        if not directory.is_dir():
            raise CoprAutomationError(f"package directory does not exist: {directory}")

        expected_spec = directory / f"{name}.spec"
        specs = sorted(directory.glob("*.spec"))
        if specs != [expected_spec]:
            found = ", ".join(path.name for path in specs) or "none"
            raise CoprAutomationError(
                f"{directory} must contain exactly {name}.spec; found: {found}"
            )
        packages.append(PackageDefinition(name, directory, expected_spec))
    return packages


def rpm_name(package: PackageDefinition) -> str:
    command = [
        "rpmspec",
        "-q",
        "--srpm",
        "--qf",
        "%{NAME}\\n",
        str(package.spec),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise CoprAutomationError("rpmspec is required for validation") from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip() or "rpmspec failed"
        raise CoprAutomationError(f"invalid spec {package.spec}: {details}") from exc

    names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if names != [package.name]:
        actual = ", ".join(names) or "no name"
        raise CoprAutomationError(
            f"RPM Name in {package.spec} must be {package.name!r}; found {actual!r}"
        )
    return names[0]


def validate_sources(package: PackageDefinition) -> None:
    try:
        result = subprocess.run(
            ["rpmspec", "-P", str(package.spec)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CoprAutomationError("rpmspec is required for validation") from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip() or "rpmspec failed"
        raise CoprAutomationError(f"cannot expand {package.spec}: {details}") from exc

    entry_re = re.compile(r"^(?:Source|Patch)\d*:\s*(\S+)", re.IGNORECASE)
    package_root = package.directory.resolve()
    for line in result.stdout.splitlines():
        match = entry_re.match(line.strip())
        if not match:
            continue
        value = match.group(1)
        parsed = urlparse(value)
        if parsed.scheme:
            if parsed.scheme.lower() != "https":
                raise CoprAutomationError(
                    f"{package.spec} uses non-HTTPS source or patch: {value}"
                )
            continue
        local_path = (package.directory / value).resolve()
        if not local_path.is_relative_to(package_root) or not local_path.is_file():
            raise CoprAutomationError(
                f"local source or patch is missing from {package.directory}: {value}"
            )


def run_rpmlint(package: PackageDefinition) -> None:
    try:
        subprocess.run(["rpmlint", str(package.spec)], check=True)
    except FileNotFoundError as exc:
        raise CoprAutomationError("rpmlint is required for validation") from exc
    except subprocess.CalledProcessError as exc:
        raise CoprAutomationError(
            f"rpmlint failed for {package.name} with exit code {exc.returncode}"
        ) from exc


def build_srpm(package: PackageDefinition, makefile: Path = SRPM_MAKEFILE) -> Path:
    with tempfile.TemporaryDirectory(prefix=f"copr-{package.name}-") as temp_dir:
        command = [
            "make",
            "-f",
            str(makefile),
            "srpm",
            f"outdir={temp_dir}",
            f"spec={package.spec}",
        ]
        try:
            subprocess.run(command, cwd=package.directory, check=True)
        except FileNotFoundError as exc:
            raise CoprAutomationError("make is required for SRPM validation") from exc
        except subprocess.CalledProcessError as exc:
            raise CoprAutomationError(
                f"SRPM validation failed for {package.name} with exit code {exc.returncode}"
            ) from exc

        srpms = list(Path(temp_dir).glob("*.src.rpm"))
        if len(srpms) != 1:
            raise CoprAutomationError(
                f"expected one SRPM for {package.name}, found {len(srpms)}"
            )
        return Path(srpms[0].name)


def validate_packages(packages: Sequence[PackageDefinition], build: bool = True) -> None:
    for package in packages:
        rpm_name(package)
        validate_sources(package)
        if build:
            run_rpmlint(package)
            srpm = build_srpm(package)
            print(f"validated {package.name}: {srpm}")
        else:
            print(f"validated layout: {package.name}")
    if not packages:
        print("no package definitions found; project configuration is valid")


def changed_package_names(base: str, head: str = "HEAD") -> list[str] | None:
    """Return changed package names, or None when every package must publish."""
    if not base or ZERO_SHA_RE.fullmatch(base):
        return None

    command = ["git", "diff", "--name-status", "--find-renames", base, head, "--"]
    try:
        result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise CoprAutomationError(f"cannot calculate changed packages for {base}..{head}") from exc

    changed: set[str] = set()
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        for relative in fields[1:]:
            if any(relative == prefix or relative.startswith(prefix) for prefix in MANAGED_PATHS):
                return None
            parts = Path(relative).parts
            if len(parts) >= 3 and parts[0] == "packages":
                name = validate_package_name(parts[1])
                if (PACKAGES_DIR / name).is_dir():
                    changed.add(name)
                else:
                    print(
                        f"warning: {name} was removed locally; remote COPR package is retained",
                        file=sys.stderr,
                    )
    return sorted(changed)


def _project_chroots(project: Any) -> set[str]:
    chroot_repos = getattr(project, "chroot_repos", None)
    if isinstance(chroot_repos, dict):
        return set(chroot_repos)
    chroots = getattr(project, "chroots", None)
    return set(chroots or ())


def ensure_project(client: Any, owner: str, config: ProjectConfig) -> Any:
    client.project_proxy.add(
        ownername=owner,
        projectname=config.name,
        chroots=list(config.chroots),
        description=config.description,
        instructions=config.instructions.replace("<owner>", owner),
        homepage=config.homepage,
        unlisted_on_hp=False,
        enable_net=False,
        devel_mode=False,
        auto_prune=True,
        follow_fedora_branching=False,
        exist_ok=True,
    )
    project = client.project_proxy.get(owner, config.name)
    chroots = sorted(_project_chroots(project) | set(config.chroots))
    client.project_proxy.edit(
        ownername=owner,
        projectname=config.name,
        chroots=chroots,
        description=config.description,
        instructions=config.instructions.replace("<owner>", owner),
        homepage=config.homepage,
        unlisted_on_hp=False,
        enable_net=False,
        devel_mode=False,
        auto_prune=True,
        follow_fedora_branching=False,
    )
    print(f"ensured public COPR project: {owner}/{config.name}")
    return project


def package_source(config: ProjectConfig, package: PackageDefinition) -> dict[str, Any]:
    return {
        "clone_url": config.clone_url,
        "committish": config.branch,
        "subdirectory": str(package.directory.relative_to(ROOT)),
        "spec": package.spec.name,
        "scm_type": "git",
        "source_build_method": "make_srpm",
        "webhook_rebuild": False,
    }


def sync_package(
    client: Any,
    no_result_error: type[BaseException],
    owner: str,
    config: ProjectConfig,
    package: PackageDefinition,
) -> None:
    source = package_source(config, package)
    try:
        client.package_proxy.get(owner, config.name, package.name)
    except no_result_error:
        client.package_proxy.add(owner, config.name, package.name, "scm", source)
        action = "added"
    else:
        client.package_proxy.edit(owner, config.name, package.name, "scm", source)
        action = "updated"
    print(f"{action} COPR package recipe: {package.name}")


def wait_for_builds(
    builds: Sequence[Any],
    wait_func: Callable[..., Sequence[Any]],
    copr_url: str,
) -> list[Any]:
    if not builds:
        print("no package builds requested")
        return []

    def progress(items: Sequence[Any]) -> None:
        states = ", ".join(f"{item.id}={item.state}" for item in items)
        print(f"COPR build status: {states}", flush=True)

    results = list(wait_func(list(builds), interval=30, callback=progress, timeout=21000))
    base_url = copr_url.rstrip("/")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    summary_lines = ["## COPR builds", ""]
    for build in results:
        url = f"{base_url}/coprs/build/{build.id}"
        print(f"build {build.id}: {build.state} ({url})")
        summary_lines.append(f"- [{build.id}]({url}): `{build.state}`")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("\n".join(summary_lines) + "\n")

    failures = [build for build in results if build.state not in {"succeeded", "skipped"}]
    if failures:
        states = ", ".join(f"{build.id}={build.state}" for build in failures)
        raise CoprAutomationError(f"COPR builds did not succeed: {states}")
    return results


def load_copr_client(config_path: str | None) -> tuple[Any, type[BaseException], Callable[..., Any]]:
    try:
        from copr.v3 import Client, CoprNoResultException, wait
    except ImportError as exc:
        raise CoprAutomationError("python3-copr is required for publishing") from exc
    return Client.create_from_config_file(config_path), CoprNoResultException, wait


def publish(packages: Sequence[PackageDefinition], config_path: str | None) -> None:
    config = load_project_config()
    owner = os.environ.get("COPR_OWNER", "").strip()
    if not owner:
        raise CoprAutomationError("COPR_OWNER is required for publishing")

    client, no_result_error, wait_func = load_copr_client(config_path)
    authenticated = str(client.config.get("username") or "").strip()
    if authenticated != owner:
        raise CoprAutomationError(
            f"COPR_CONFIG username {authenticated!r} does not match COPR_OWNER {owner!r}"
        )

    ensure_project(client, owner, config)
    builds: list[Any] = []
    for package in packages:
        sync_package(client, no_result_error, owner, config, package)
        build = client.package_proxy.build(owner, config.name, package.name)
        # PackageProxy.build delegates to BuildProxy but binds the returned
        # object back to PackageProxy. The wait helper needs BuildProxy.get.
        build.__proxy__ = client.build_proxy
        builds.append(build)
    wait_for_builds(builds, wait_func, client.config["copr_url"])


def selection_from_args(args: argparse.Namespace) -> list[str] | None:
    if args.package:
        return [validate_package_name(args.package)]
    if getattr(args, "changed_from", None) is not None:
        return changed_package_names(args.changed_from, args.head)
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate package specs and build SRPMs")
    validate_selection = validate.add_mutually_exclusive_group(required=True)
    validate_selection.add_argument("--all", action="store_true", help="validate every package")
    validate_selection.add_argument("--package", help="validate one package")

    publish_command = commands.add_parser("publish", help="sync and build COPR packages")
    publish_selection = publish_command.add_mutually_exclusive_group(required=True)
    publish_selection.add_argument("--all", action="store_true", help="publish every package")
    publish_selection.add_argument("--package", help="publish one package")
    publish_selection.add_argument("--changed-from", metavar="GIT_SHA", help="publish changed packages")
    publish_command.add_argument("--head", default="HEAD", help="end of the Git change range")
    publish_command.add_argument(
        "--config",
        default=os.environ.get("COPR_CONFIG_PATH"),
        help="path to copr-cli configuration (default: COPR_CONFIG_PATH or ~/.config/copr)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        load_project_config()
        selected = selection_from_args(args)
        packages = discover_packages(selected)
        if args.command == "validate":
            validate_packages(packages)
        else:
            validate_packages(packages, build=False)
            publish(packages, args.config)
        return 0
    except CoprAutomationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
