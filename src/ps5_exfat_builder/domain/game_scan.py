"""Game metadata scanning and filename helpers.

This module is intentionally UI-free so build, conversion, AMPR, and PKG
backends can all share the same metadata behavior.
"""

from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path


def parse_sfo(path: str | os.PathLike[str]) -> dict[str, object]:
    try:
        data = Path(path).read_bytes()
        if len(data) < 20:
            return {}
        magic, _version, key_table_offset, data_table_offset, num_entries = (
            struct.unpack_from("<IIIII", data, 0)
        )
        if magic != 0x46535000:
            return {}
        results: dict[str, object] = {}
        for i in range(num_entries):
            entry_offset = 20 + i * 16
            if entry_offset + 16 > len(data):
                break
            key_off, data_fmt, data_len, _data_max_len, data_off = (
                struct.unpack_from("<HHIII", data, entry_offset)
            )
            key_start = key_table_offset + key_off
            key_end = data.index(b"\x00", key_start)
            key = data[key_start:key_end].decode("utf-8", errors="replace")
            val_start = data_table_offset + data_off
            if data_fmt == 0x0204:
                val = (
                    data[val_start : val_start + data_len]
                    .rstrip(b"\x00")
                    .decode("utf-8", errors="replace")
                )
            elif data_fmt == 0x0404:
                val = struct.unpack_from("<I", data, val_start)[0]
            else:
                val = data[val_start : val_start + data_len]
            results[key] = val
        return results
    except Exception:
        return {}


def find_meta_file(folder: str | os.PathLike[str], names: list[str]) -> str | None:
    """Search for any of the given filenames within folder up to 5 levels deep."""
    folder_path = Path(folder)
    for sub in ("", "sce_sys"):
        for name in names:
            path = folder_path / sub / name if sub else folder_path / name
            if path.is_file():
                return str(path)

    try:
        for root, dirs, files in os.walk(folder_path):
            root_path = Path(root)
            rel = os.path.relpath(root_path, folder_path)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth > 5:
                dirs[:] = []
                continue
            lower_files = [file.lower() for file in files]
            for name in names:
                lowered = name.lower()
                if lowered in lower_files:
                    idx = lower_files.index(lowered)
                    return str(root_path / files[idx])
    except Exception:
        pass
    return None


def find_sfo(folder: str | os.PathLike[str]) -> str | None:
    return find_meta_file(folder, ["param.sfo"])


def parse_param_json(path: str | os.PathLike[str]) -> tuple[str, str, str]:
    """Parse param.json used by some PS5 extraction tools instead of param.sfo."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            data = json.load(file)
        title_id = data.get("titleId", "")
        version = data.get("version") or data.get("masterVersion") or ""
        title = ""
        localized = data.get("localizedParameters", {})
        if localized:
            default_lang = localized.get("defaultLanguage", "en-US")
            for lang in (default_lang, "en-US", "en-GB"):
                value = localized.get(lang, {})
                if isinstance(value, dict):
                    candidate = value.get("titleName", "")
                    if candidate:
                        title = candidate
                        break
            if not title:
                for value in localized.values():
                    if isinstance(value, dict) and value.get("titleName"):
                        title = value["titleName"]
                        break
        if not title:
            title = data.get("titleName", "") or data.get("name", "")
        return title.strip(), str(title_id).strip(), str(version).strip()
    except Exception:
        return "", "", ""


def parse_nptitle_dat(path: str | os.PathLike[str]) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            return file.readline().strip()
    except Exception:
        return ""


def sanitize_filename(name: object) -> str:
    if not name:
        return ""
    text = str(name)
    normalize = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b4": "'",
        "\u0060": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u2022": " ",
        "\u00b7": " ",
        "\u2027": " ",
        "\u00ae": "",
        "\u00a9": "",
        "\u2122": "",
        "\u2120": "",
    }
    for src, dst in normalize.items():
        if src in text:
            text = text.replace(src, dst)

    text = "".join(
        ch
        for ch in text
        if ch == "\t" or (0x20 <= ord(ch) < 0x7F) or ord(ch) > 0x9F
    )
    text = re.sub(r'[\\/:*?"<>|&^%!`$]', "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" .")
    text = text[:80]
    return text or "game"


def normalize_version(version: object) -> str:
    if not isinstance(version, str):
        return ""
    version = version.strip()
    if not version:
        return ""
    parts = version.split(".")
    if len(parts) == 2:
        parts.append("000")
    if len(parts) >= 3:
        parts[0] = parts[0].zfill(2)
        parts[1] = parts[1].zfill(3)
        parts[2] = parts[2].zfill(3)
        return ".".join(parts[:3])
    return version


def get_game_info(folder: str | os.PathLike[str]) -> tuple[str | None, str | None, str | None]:
    folder = os.path.normpath(os.fspath(folder))
    title, title_id, version = "", "", ""

    sfo_path = find_sfo(folder)
    if sfo_path:
        info = parse_sfo(sfo_path)
        if info:
            title = str(info.get("TITLE") or info.get("TITLE_00") or "")
            raw_title_id = info.get("TITLE_ID", "")
            title_id = "" if isinstance(raw_title_id, int) else str(raw_title_id)
            version = str(info.get("VERSION") or info.get("APP_VER") or "")
    sfo_version = version

    pfs_path = find_meta_file(folder, ["pfs-version.dat"])
    if pfs_path:
        try:
            with open(pfs_path, "r", encoding="utf-8", errors="replace") as file:
                pfs_ver = file.read().strip().split("\n")[0].strip()
            if pfs_ver and re.match(r"[\d.]+", pfs_ver):
                version = pfs_ver
        except Exception:
            pass

    if not title and not title_id:
        json_path = find_meta_file(folder, ["param.json"])
        if json_path:
            parsed_title, parsed_id, parsed_version = parse_param_json(json_path)
            title = title or parsed_title
            title_id = title_id or parsed_id
            if not sfo_version and not version:
                version = parsed_version

    if not title:
        npt_path = find_meta_file(folder, ["nptitle.dat"])
        if npt_path:
            title = parse_nptitle_dat(npt_path)

    version = normalize_version(version)
    return (
        sanitize_filename(title) if title else None,
        title_id.strip() if title_id else None,
        version if version else None,
    )


def build_exfat_name(
    title: str | None,
    title_id: str | None,
    version: str | None,
) -> str:
    parts = []
    if title_id:
        parts.append(title_id)
    if title and title != title_id:
        parts.append(title)
    if not parts:
        return "game.exfat"
    result = " ".join(parts)
    if version:
        result = f"{result} ({version})"
    return sanitize_filename(result) + ".exfat"
