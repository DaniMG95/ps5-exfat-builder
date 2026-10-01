"""OSFMount command construction.

Keep direct OSFMount invocation behind this boundary so exFAT, PKG, AMPR,
and editor flows can share the same mounting behavior.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

OSFMOUNT_BINARY_NAMES = (
    "osfmount.com",
    "OSFMount.com",
    "OSFMount.exe",
    "osfmount.exe",
)


@dataclass(frozen=True, slots=True)
class OsfMountImageCommand:
    executable: Path
    image: Path
    mount_point: str
    read_only: bool = True

    def argv(self) -> list[str]:
        options = "ro,rem" if self.read_only else "rw,rem"
        return [
            str(self.executable),
            "-a",
            "-t",
            "file",
            "-f",
            str(self.image),
            "-m",
            self.mount_point,
            "-o",
            options,
        ]


@dataclass(frozen=True, slots=True)
class OsfDismountCommand:
    executable: Path
    mount_point: str

    def argv(self) -> list[str]:
        return [str(self.executable), "-d", "-m", self.mount_point]


def valid_osfmount_file(path: str | os.PathLike[str] | None) -> str | None:
    try:
        if path and Path(path).is_file():
            return str(path)
    except Exception:
        pass
    return None


def prefer_cli_wrapper(path: str | os.PathLike[str] | None) -> str | None:
    """Prefer osfmount.com beside OSFMount.exe when available."""
    valid = valid_osfmount_file(path)
    if not valid:
        return None
    candidate = Path(valid)
    if candidate.suffix.lower() == ".exe":
        sibling = candidate.with_name("osfmount.com")
        if sibling.is_file():
            return str(sibling)
    return str(candidate)


def find_in_directory(directory: str | os.PathLike[str] | None) -> str | None:
    if not directory:
        return None
    try:
        directory_path = Path(directory)
        for name in OSFMOUNT_BINARY_NAMES:
            candidate = valid_osfmount_file(directory_path / name)
            if candidate:
                return candidate
    except Exception:
        pass
    return None


def common_install_dirs() -> list[str]:
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get(
        "ProgramFiles(x86)",
        r"C:\Program Files (x86)",
    )
    program_w6432 = os.environ.get("ProgramW6432", program_files)
    candidates: list[str] = []
    for base in (program_files, program_files_x86, program_w6432):
        for sub in ("OSFMount", os.path.join("PassMark", "OSFMount")):
            candidates.append(os.path.join(base, sub))

    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        normalized = os.path.normcase(candidate)
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(candidate)
    return ordered


def find_osfmount(custom_path: str | None = None) -> str | None:
    """Locate OSFMount, preferring the CLI wrapper when possible."""
    custom = (custom_path or "").strip()
    if custom:
        direct = prefer_cli_wrapper(custom)
        if direct:
            return direct
        try:
            custom_path_obj = Path(custom)
            if custom_path_obj.is_dir():
                found = find_in_directory(custom_path_obj)
            else:
                found = find_in_directory(custom_path_obj.parent)
            if found:
                return found
        except Exception:
            pass

    registry_hit = find_osfmount_from_registry()
    if registry_hit:
        return registry_hit

    for directory in common_install_dirs():
        found = find_in_directory(directory)
        if found:
            return found

    for name in OSFMOUNT_BINARY_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def find_osfmount_from_registry() -> str | None:
    try:
        import winreg
    except ImportError:
        return None

    keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PassMark\OSFMount"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\PassMark\OSFMount"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\PassMark\OSFMount"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\OSFMount_is1",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion"
            r"\Uninstall\OSFMount_is1",
        ),
    ]
    for hive, subkey in keys:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                for value_name in ("InstallLocation", "Path", "InstallDir"):
                    try:
                        value, _value_type = winreg.QueryValueEx(key, value_name)
                        found = find_in_directory(value)
                        if found:
                            return found
                    except FileNotFoundError:
                        continue
        except (FileNotFoundError, OSError):
            continue
    return None


def first_free_drive_letter(used_mask: int, start: str = "G", end: str = "Z") -> str | None:
    for code in range(ord(start.upper()), ord(end.upper()) + 1):
        if not (used_mask & (1 << (code - ord("A")))):
            return chr(code) + ":"
    return None
