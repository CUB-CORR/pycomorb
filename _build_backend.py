"""Custom build backend that handles data file nesting and git tracking."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import setuptools.build_meta as build_meta


def _prepare_common_nested() -> None:
    """Copy only git-tracked files from common/ into pycomorb/common/ for the build."""
    repo_root = Path(__file__).parent
    source = repo_root / "common"
    target = repo_root / "pycomorb" / "common"

    if not source.exists():
        return

    if target.exists():
        shutil.rmtree(target)

    target.mkdir(parents=True, exist_ok=True)

    try:
        # Get list of git-tracked files in the common/ directory
        result = subprocess.run(
            ["git", "ls-files", "common/"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        tracked_files = result.stdout.splitlines()

        for file_path_str in tracked_files:
            file_path = repo_root / file_path_str
            if not file_path.is_file():
                continue

            # Calculate the path relative to the 'common' directory
            relative_path = file_path.relative_to(source)
            dest_path = target / relative_path

            # Create parent directories in the target if they don't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(file_path, dest_path)

        print(
            "✓ Prepared git-tracked data files: common/ → pycomorb/common/",
            file=sys.stderr,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        # Fallback to simple copy if git is not available or fails
        print(
            f"Warning: Git check failed ({e}), falling back to full copy.",
            file=sys.stderr,
        )
        shutil.rmtree(target)
        shutil.copytree(source, target)


def _cleanup_common_nested() -> None:
    """Remove the nested pycomorb/common/ after build."""
    repo_root = Path(__file__).parent
    target = repo_root / "pycomorb" / "common"
    if target.exists():
        shutil.rmtree(target)
        print("✓ Cleaned up pycomorb/common/", file=sys.stderr)


# Prepare before building sdist
def build_sdist(
    sdist_directory: str, config_settings: Dict[str, Any] | None = None
) -> str:
    """Build source distribution with prepared data files."""
    _prepare_common_nested()
    try:
        return build_meta.build_sdist(sdist_directory, config_settings)
    finally:
        _cleanup_common_nested()


# Prepare before building wheel
def build_wheel(
    wheel_directory: str,
    config_settings: Dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build wheel with prepared data files."""
    _prepare_common_nested()
    try:
        return build_meta.build_wheel(wheel_directory, config_settings, metadata_directory) # fmt: skip
    finally:
        _cleanup_common_nested()


# Other required functions from the backend
def get_requires_for_build_sdist(
    config_settings: Dict[str, Any] | None = None,
) -> List[str]:
    _prepare_common_nested()
    try:
        return build_meta.get_requires_for_build_sdist(config_settings)
    finally:
        _cleanup_common_nested()


def get_requires_for_build_wheel(
    config_settings: Dict[str, Any] | None = None,
) -> List[str]:
    _prepare_common_nested()
    try:
        return build_meta.get_requires_for_build_wheel(config_settings)
    finally:
        _cleanup_common_nested()


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: Dict[str, Any] | None = None,
) -> str:
    """Prepare wheel metadata."""
    _prepare_common_nested()
    try:
        return build_meta.prepare_metadata_for_build_wheel(metadata_directory, config_settings) # fmt: skip
    finally:
        _cleanup_common_nested()


def build_editable(
    wheel_directory: str,
    config_settings: Dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build editable install."""
    _prepare_common_nested()
    try:
        return build_meta.build_editable(wheel_directory, config_settings, metadata_directory) # fmt: skip
    finally:
        _cleanup_common_nested()


def get_requires_for_build_editable(
    config_settings: Dict[str, Any] | None = None,
) -> List[str]:
    _prepare_common_nested()
    try:
        return build_meta.get_requires_for_build_editable(config_settings)
    finally:
        _cleanup_common_nested()
