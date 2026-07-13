from __future__ import annotations

import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "copr_automation", ROOT / "scripts" / "copr_automation.py"
)
assert SPEC and SPEC.loader
copr = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = copr
SPEC.loader.exec_module(copr)


class NoResultError(Exception):
    pass


class CoprAutomationTests(unittest.TestCase):
    def test_project_configuration(self) -> None:
        config = copr.load_project_config()
        self.assertEqual(config.name, "copr-fedora")
        self.assertEqual(
            config.chroots,
            ("fedora-43-x86_64", "fedora-44-x86_64"),
        )
        self.assertEqual(config.branch, "main")

    def test_empty_package_directory_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(copr.discover_packages(packages_dir=Path(directory)), [])

    def test_package_layout_requires_matching_spec(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            packages = Path(directory)
            (packages / "wrong").mkdir()
            (packages / "wrong" / "other.spec").touch()
            with self.assertRaisesRegex(copr.CoprAutomationError, "wrong.spec"):
                copr.discover_packages(["wrong"], packages)

    def test_invalid_package_name_is_rejected(self) -> None:
        with self.assertRaises(copr.CoprAutomationError):
            copr.validate_package_name("../escape")

    def test_non_https_source_is_rejected(self) -> None:
        package = copr.PackageDefinition(
            "hello",
            ROOT / "tests" / "fixtures" / "hello",
            ROOT / "tests" / "fixtures" / "hello" / "hello.spec",
        )
        expanded = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Source0: http://example.invalid/hello.tar.gz\n",
            stderr="",
        )
        with mock.patch.object(copr.subprocess, "run", return_value=expanded):
            with self.assertRaisesRegex(copr.CoprAutomationError, "non-HTTPS"):
                copr.validate_sources(package)

    def test_missing_local_source_is_rejected(self) -> None:
        package = copr.PackageDefinition(
            "hello",
            ROOT / "tests" / "fixtures" / "hello",
            ROOT / "tests" / "fixtures" / "hello" / "hello.spec",
        )
        expanded = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Source0: missing.tar.gz\n",
            stderr="",
        )
        with mock.patch.object(copr.subprocess, "run", return_value=expanded):
            with self.assertRaisesRegex(copr.CoprAutomationError, "missing"):
                copr.validate_sources(package)

    def test_ensure_project_preserves_extra_chroots(self) -> None:
        client = SimpleNamespace(
            project_proxy=mock.Mock(),
        )
        client.project_proxy.get.return_value = SimpleNamespace(
            chroot_repos={"fedora-rawhide-x86_64": "https://example.invalid"}
        )
        config = copr.load_project_config()

        copr.ensure_project(client, "owner", config)

        client.project_proxy.add.assert_called_once()
        edit = client.project_proxy.edit.call_args.kwargs
        self.assertEqual(
            edit["chroots"],
            ["fedora-43-x86_64", "fedora-44-x86_64", "fedora-rawhide-x86_64"],
        )
        self.assertFalse(edit["unlisted_on_hp"])
        self.assertFalse(edit["devel_mode"])

    def test_sync_package_adds_missing_recipe(self) -> None:
        client = SimpleNamespace(package_proxy=mock.Mock())
        client.package_proxy.get.side_effect = NoResultError()
        package = copr.PackageDefinition(
            "hello",
            ROOT / "packages" / "hello",
            ROOT / "packages" / "hello" / "hello.spec",
        )

        copr.sync_package(
            client,
            NoResultError,
            "owner",
            copr.load_project_config(),
            package,
        )

        client.package_proxy.add.assert_called_once()
        source = client.package_proxy.add.call_args.args[-1]
        self.assertEqual(source["subdirectory"], "packages/hello")
        self.assertEqual(source["source_build_method"], "make_srpm")
        self.assertFalse(source["webhook_rebuild"])

    def test_sync_package_updates_existing_recipe(self) -> None:
        client = SimpleNamespace(package_proxy=mock.Mock())
        package = copr.PackageDefinition(
            "hello",
            ROOT / "packages" / "hello",
            ROOT / "packages" / "hello" / "hello.spec",
        )

        copr.sync_package(
            client,
            NoResultError,
            "owner",
            copr.load_project_config(),
            package,
        )

        client.package_proxy.edit.assert_called_once()
        client.package_proxy.add.assert_not_called()

    def test_failed_build_is_an_error(self) -> None:
        build = SimpleNamespace(id=42, state="pending")
        failed = SimpleNamespace(id=42, state="failed")
        with self.assertRaisesRegex(copr.CoprAutomationError, "42=failed"):
            copr.wait_for_builds([build], lambda *_args, **_kwargs: [failed], "https://copr.example")

    def test_removed_package_is_retained(self) -> None:
        diff = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="D\tpackages/removed/removed.spec\n",
            stderr="",
        )
        errors = io.StringIO()
        with mock.patch.object(copr.subprocess, "run", return_value=diff), redirect_stderr(errors):
            changed = copr.changed_package_names("a" * 40, "b" * 40)
        self.assertEqual(changed, [])
        self.assertIn("remote COPR package is retained", errors.getvalue())

    def test_shared_change_rebuilds_all_packages(self) -> None:
        diff = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="M\t.copr/Makefile\n",
            stderr="",
        )
        with mock.patch.object(copr.subprocess, "run", return_value=diff):
            self.assertIsNone(copr.changed_package_names("a" * 40, "b" * 40))

    def test_unavailable_git_range_rebuilds_all_packages(self) -> None:
        failure = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "diff"],
            stderr="fatal: not a git repository",
        )
        errors = io.StringIO()
        with mock.patch.object(copr.subprocess, "run", side_effect=failure), redirect_stderr(errors):
            self.assertIsNone(copr.changed_package_names("a" * 40, "b" * 40))
        self.assertIn("publishing all packages", errors.getvalue())

    def test_publish_binds_build_proxy_before_waiting(self) -> None:
        build = SimpleNamespace(id=7, state="pending")
        completed = SimpleNamespace(id=7, state="succeeded")
        client = SimpleNamespace(
            config={"username": "owner", "copr_url": "https://copr.example"},
            project_proxy=mock.Mock(),
            package_proxy=mock.Mock(),
            build_proxy=mock.Mock(),
        )
        client.project_proxy.get.return_value = SimpleNamespace(chroot_repos={})
        client.package_proxy.build.return_value = build
        package = copr.PackageDefinition(
            "hello",
            ROOT / "packages" / "hello",
            ROOT / "packages" / "hello" / "hello.spec",
        )

        def wait_func(builds, **_kwargs):
            self.assertIs(builds[0].__proxy__, client.build_proxy)
            return [completed]

        with (
            mock.patch.dict(os.environ, {"COPR_OWNER": "owner"}, clear=False),
            mock.patch.object(
                copr,
                "load_copr_client",
                return_value=(client, NoResultError, wait_func),
            ),
        ):
            copr.publish([package], "/tmp/copr-config")

        client.package_proxy.edit.assert_called_once()
        client.package_proxy.build.assert_called_once_with("owner", "copr-fedora", "hello")

    def test_publish_rejects_owner_mismatch_before_mutation(self) -> None:
        client = SimpleNamespace(
            config={"username": "different", "copr_url": "https://copr.example"},
            project_proxy=mock.Mock(),
            package_proxy=mock.Mock(),
        )
        with (
            mock.patch.dict(os.environ, {"COPR_OWNER": "owner"}, clear=False),
            mock.patch.object(
                copr,
                "load_copr_client",
                return_value=(client, NoResultError, mock.Mock()),
            ),
        ):
            with self.assertRaisesRegex(copr.CoprAutomationError, "does not match"):
                copr.publish([], "/tmp/copr-config")
        client.project_proxy.add.assert_not_called()

    @unittest.skipUnless(
        shutil.which("rpmbuild") and shutil.which("spectool") and shutil.which("make"),
        "RPM build tools are required",
    )
    def test_shared_makefile_builds_fixture_srpm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package_dir = Path(directory) / "hello"
            source_dir = Path(directory) / "hello-1.0"
            output_dir = Path(directory) / "output"
            package_dir.mkdir()
            source_dir.mkdir()
            output_dir.mkdir()
            shutil.copy(ROOT / "tests" / "fixtures" / "hello" / "hello.spec", package_dir)
            (source_dir / "README").write_text("hello\n", encoding="utf-8")
            with tarfile.open(package_dir / "hello-1.0.tar.gz", "w:gz") as archive:
                archive.add(source_dir, arcname="hello-1.0")

            subprocess.run(
                [
                    "make",
                    "-f",
                    str(ROOT / ".copr" / "Makefile"),
                    "srpm",
                    f"outdir={output_dir}",
                    "spec=hello.spec",
                ],
                cwd=package_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(len(list(output_dir.glob("hello-*.src.rpm"))), 1)


if __name__ == "__main__":
    unittest.main()
