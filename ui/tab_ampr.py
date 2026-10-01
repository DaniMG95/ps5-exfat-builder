"""AMPR conversion tab."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from tkinter_theme import COLORS, FONTS
from ui.shared.cards import Card
from ui.shared.page_head import field_block, info_banner, make_themed_button, page_head
from ui.shared.scroll import attach_scroll
from ps5_exfat_builder.domain import FormatId, TransformRequest
from ps5_exfat_builder.formats import default_registry
from ps5_exfat_builder.formats.ampr import AMPR_PEER_FORMATS
from ps5_exfat_builder.integrations.ampr import discover_profiles, find_tool
from ps5_exfat_builder.services.progress import ProgressEvent


_FORMAT_CHOICES = ("ampr", *AMPR_PEER_FORMATS)
_TARGET_EXTENSIONS = {
    "ampr": ".ampr",
    "exfat": ".exfat",
    "ffpkg": ".ffpkg",
    "ffpfs": ".ffpfs",
    "ffpfsc": ".ffpfsc",
    "pkg": ".pkg",
}


def _coerce_format(value: str) -> FormatId:
    return value  # type: ignore[return-value]


def build_ampr_tab(parent, app) -> None:
    parent.configure(bg=COLORS["bg_1"])

    registry = default_registry(include_experimental=True)
    cpu_count = os.cpu_count() or 1
    state = {"busy": False}

    source_var = tk.StringVar()
    target_var = tk.StringVar()
    tool_var = tk.StringVar()
    profile_var = tk.StringVar()
    source_format_var = tk.StringVar(value="folder")
    target_format_var = tk.StringVar(value="ampr")
    command_style_var = tk.StringVar(value="route-flags")
    default_args_var = tk.StringVar()
    extra_args_var = tk.StringVar()
    timeout_var = tk.StringVar(value="")
    workers_var = tk.StringVar(value=str(cpu_count))
    high_perf_var = tk.BooleanVar(value=True)
    status_var = tk.StringVar(value="Ready.")

    canvas = tk.Canvas(parent, bg=COLORS["bg_1"], bd=0, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)
    inner = tk.Frame(canvas, bg=COLORS["bg_1"])
    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))
    attach_scroll(canvas)

    head = page_head(
        inner,
        "A",
        "AMPR Studio",
        "Pack and unpack AMPR routes with profiles, backend styles and CPU-focused execution.",
    )
    head.pack(fill="x", padx=24, pady=(14, 12))

    info_banner(
        inner,
        "High performance sets thread-count environment variables, high process priority and CPU affinity for the external AMPR backend.",
    ).pack(fill="x", padx=24, pady=(0, 14))

    route_card = Card(
        inner,
        title="Conversion route",
        subtitle="Choose any supported AMPR pack or unpack transformation.",
        icon=">",
        with_actions=False,
    )
    route_card.pack(fill="x", padx=24, pady=(0, 14))

    route_row = tk.Frame(route_card.body, bg=COLORS["bg_2"])
    route_row.pack(fill="x")
    for idx in range(5):
        route_row.grid_columnconfigure(idx, weight=1 if idx in (0, 2) else 0)

    tk.Label(route_row, text="Source format", font=FONTS["label"], bg=COLORS["bg_2"], fg=COLORS["fg_3"]).grid(row=0, column=0, sticky="w")
    tk.Label(route_row, text="Target format", font=FONTS["label"], bg=COLORS["bg_2"], fg=COLORS["fg_3"]).grid(row=0, column=2, sticky="w", padx=(16, 0))
    src_combo = ttk.Combobox(route_row, textvariable=source_format_var, values=_FORMAT_CHOICES, state="readonly")
    src_combo.grid(row=1, column=0, sticky="ew", pady=(6, 0))
    tk.Label(route_row, text="->", font=(FONTS["h2"][0], 14, "bold"), bg=COLORS["bg_2"], fg=COLORS["accent"]).grid(row=1, column=1, padx=14)
    dst_combo = ttk.Combobox(route_row, textvariable=target_format_var, values=_FORMAT_CHOICES, state="readonly")
    dst_combo.grid(row=1, column=2, sticky="ew", padx=(16, 0), pady=(6, 0))

    route_status = tk.Label(route_row, text="", font=FONTS["mono_sm"], bg=COLORS["bg_2"], fg=COLORS["fg_4"])
    route_status.grid(row=1, column=3, sticky="e", padx=(16, 0))

    matrix = tk.Frame(route_card.body, bg=COLORS["bg_2"])
    matrix.pack(fill="x", pady=(18, 0))
    tk.Label(
        matrix,
        text="Implemented AMPR transformations",
        font=(FONTS["mono_sm"][0], 9, "bold"),
        bg=COLORS["bg_2"],
        fg=COLORS["fg_1"],
        anchor="w",
    ).pack(fill="x")
    matrix_grid = tk.Frame(matrix, bg=COLORS["bg_2"])
    matrix_grid.pack(fill="x", pady=(8, 0))
    matrix_grid.grid_columnconfigure(0, weight=1)
    matrix_grid.grid_columnconfigure(1, weight=1)

    def _route_line(parent, text: str) -> None:
        tk.Label(
            parent,
            text="  " + text + "  ",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_3"],
            fg=COLORS["teal_hi"],
            anchor="w",
            padx=8,
            pady=4,
            highlightbackground=COLORS["border_2"],
            highlightthickness=1,
        ).pack(fill="x", pady=(0, 4))

    pack_col = tk.Frame(matrix_grid, bg=COLORS["bg_2"])
    unpack_col = tk.Frame(matrix_grid, bg=COLORS["bg_2"])
    pack_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    unpack_col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    tk.Label(pack_col, text="Pack to AMPR", font=FONTS["label"], bg=COLORS["bg_2"], fg=COLORS["fg_3"], anchor="w").pack(fill="x", pady=(0, 6))
    tk.Label(unpack_col, text="Unpack from AMPR", font=FONTS["label"], bg=COLORS["bg_2"], fg=COLORS["fg_3"], anchor="w").pack(fill="x", pady=(0, 6))
    for fmt in AMPR_PEER_FORMATS:
        _route_line(pack_col, f"{fmt} -> ampr")
        _route_line(unpack_col, f"ampr -> {fmt}")

    files_card = Card(
        inner,
        title="Inputs and output",
        subtitle="Select the backend launcher, optional TOML profile, source and destination.",
        icon="...",
    )
    files_card.pack(fill="x", padx=24, pady=(0, 14))

    def _browse_source() -> None:
        if source_format_var.get() == "folder":
            path = filedialog.askdirectory(title="Select source folder")
        else:
            path = filedialog.askopenfilename(title="Select source file", filetypes=[("All files", "*.*")])
        if path:
            source_var.set(path)

    def _browse_target() -> None:
        ext = _TARGET_EXTENSIONS.get(target_format_var.get(), "")
        path = filedialog.asksaveasfilename(
            title="Select output",
            defaultextension=ext,
            filetypes=[(target_format_var.get().upper(), "*" + ext), ("All files", "*.*")] if ext else [("All files", "*.*")],
        )
        if path:
            target_var.set(path)

    def _browse_tool() -> None:
        path = filedialog.askopenfilename(title="Select AMPR tool", filetypes=[("Executables and scripts", "*.exe *.bat *.cmd *.py"), ("All files", "*.*")])
        if path:
            tool_var.set(path)

    def _browse_profile() -> None:
        path = filedialog.askopenfilename(title="Select AMPR profile", filetypes=[("TOML profiles", "*.toml"), ("All files", "*.*")])
        if path:
            profile_var.set(path)

    field_block(files_card.body, "Source", source_var, on_browse=_browse_source, hint="folder or image depending on route")
    field_block(files_card.body, "Output", target_var, on_browse=_browse_target, hint="destination artifact")
    field_block(files_card.body, "AMPR tool", tool_var, on_browse=_browse_tool, hint="Lazy_AMPR/ampr_emu launcher")
    field_block(files_card.body, "Profile", profile_var, on_browse=_browse_profile, hint="optional TOML profile")

    backend_card = Card(
        inner,
        title="Backend and hardware performance",
        subtitle=(
            "Tune command syntax, worker count, high process priority and "
            "all-CPU affinity for heavy AMPR conversions."
        ),
        icon="*",
        with_actions=True,
    )
    backend_card.pack(fill="x", padx=24, pady=(0, 18))

    controls = tk.Frame(backend_card.body, bg=COLORS["bg_2"])
    controls.pack(fill="x")
    for idx in range(4):
        controls.grid_columnconfigure(idx, weight=1)

    def _label(text: str, row: int, col: int) -> None:
        tk.Label(controls, text=text, font=FONTS["label"], bg=COLORS["bg_2"], fg=COLORS["fg_3"]).grid(row=row, column=col, sticky="w", padx=(0 if col == 0 else 12, 0))

    _label("Command style", 0, 0)
    ttk.Combobox(controls, textvariable=command_style_var, values=("generic", "route-flags", "positional"), state="readonly").grid(row=1, column=0, sticky="ew", pady=(6, 12))
    _label("CPU workers", 0, 1)
    tk.Entry(controls, textvariable=workers_var, font=FONTS["mono_sm"], bg=COLORS["field_bg"], fg=COLORS["field_fg"], relief="flat", bd=7).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(6, 12))
    _label("Timeout seconds", 0, 2)
    tk.Entry(controls, textvariable=timeout_var, font=FONTS["mono_sm"], bg=COLORS["field_bg"], fg=COLORS["field_fg"], relief="flat", bd=7).grid(row=1, column=2, sticky="ew", padx=(12, 0), pady=(6, 12))
    tk.Checkbutton(
        controls,
        text=f"Use all CPU / high priority ({cpu_count} threads detected)",
        variable=high_perf_var,
        bg=COLORS["bg_2"],
        fg=COLORS["fg_1"],
        selectcolor=COLORS["bg_4"],
        activebackground=COLORS["bg_2"],
        activeforeground=COLORS["accent"],
        font=FONTS["body"],
    ).grid(row=1, column=3, sticky="w", padx=(12, 0), pady=(6, 12))

    field_block(backend_card.body, "Default args", default_args_var, hint="space-separated arguments before generated route args")
    field_block(backend_card.body, "Extra args", extra_args_var, hint="space-separated arguments appended at the end")

    status_label = tk.Label(backend_card.actions, textvariable=status_var, font=FONTS["mono_sm"], bg=COLORS["bg_3"], fg=COLORS["fg_4"], anchor="w")
    status_label.pack(side="left", fill="x", expand=True)

    progress = ttk.Progressbar(backend_card.actions, mode="indeterminate", length=180)
    progress.pack(side="right", padx=(8, 0))

    def _log(line: str) -> None:
        if hasattr(app, "_log"):
            parent.after(0, lambda: app._log("[AMPR] " + line.rstrip() + "\n"))

    def _split_args(value: str) -> list[str]:
        return [part for part in value.split() if part]

    def _set_busy(busy: bool, text: str) -> None:
        state["busy"] = busy
        status_var.set(text)
        run_button.configure(state="disabled" if busy else "normal")
        dry_button.configure(state="disabled" if busy else "normal")
        if busy:
            progress.start(10)
        else:
            progress.stop()

    def _route_ok() -> bool:
        source_format = _coerce_format(source_format_var.get())
        target_format = _coerce_format(target_format_var.get())
        ok = registry.can_convert(source_format, target_format)
        route_status.configure(
            text="route ready" if ok else "unsupported route",
            fg=COLORS["success_hi"] if ok else COLORS["danger_hi"],
        )
        return ok

    def _autofill_target(*_args) -> None:
        if not source_var.get().strip() or target_var.get().strip():
            _route_ok()
            return
        src = Path(source_var.get().strip())
        ext = _TARGET_EXTENSIONS.get(target_format_var.get(), "")
        base = src.stem if src.suffix else src.name
        target_var.set(str(src.with_name(base + ext)) if ext else str(src.with_name(base + ".out")))
        _route_ok()

    def _discover_default_tool() -> None:
        if not tool_var.get().strip() and source_var.get().strip():
            candidate_root = Path(source_var.get().strip())
            if candidate_root.is_file():
                candidate_root = candidate_root.parent
            tool = find_tool(candidate_root)
            if tool:
                tool_var.set(str(tool))

    def _discover_default_profile() -> None:
        if profile_var.get().strip() or not tool_var.get().strip():
            return
        tool = Path(tool_var.get().strip())
        root = tool.parent if tool.is_file() else tool
        try:
            profiles = discover_profiles(root)
        except Exception:
            profiles = ()
        if profiles:
            profile_var.set(str(profiles[0].path))

    for var in (source_format_var, target_format_var):
        var.trace_add("write", _autofill_target)
    source_var.trace_add("write", lambda *_a: (_autofill_target(), _discover_default_tool(), _discover_default_profile()))
    tool_var.trace_add("write", lambda *_a: _discover_default_profile())
    _route_ok()

    def _build_request(*, dry_run: bool) -> TransformRequest:
        if not _route_ok():
            raise ValueError(f"Unsupported route: {source_format_var.get()}->{target_format_var.get()}")
        source = source_var.get().strip()
        target = target_var.get().strip()
        tool = tool_var.get().strip()
        if not source:
            raise ValueError("Source is required.")
        if not target:
            raise ValueError("Output is required.")
        if not tool:
            raise ValueError("AMPR tool is required.")
        return TransformRequest(
            source=Path(source),
            target=Path(target),
            source_format=_coerce_format(source_format_var.get()),
            target_format=_coerce_format(target_format_var.get()),
            options={
                "tool_path": tool,
                "profile_path": profile_var.get().strip() or None,
                "command_style": command_style_var.get(),
                "performance_preset": "max" if high_perf_var.get() else "normal",
                "worker_count": workers_var.get().strip() or None,
                "timeout": timeout_var.get().strip() or None,
                "default_args": _split_args(default_args_var.get()),
                "extra_args": _split_args(extra_args_var.get()),
                "dry_run": dry_run,
            },
        )

    def _run(dry_run: bool) -> None:
        if state["busy"]:
            return
        try:
            request = _build_request(dry_run=dry_run)
        except Exception as exc:
            messagebox.showerror("AMPR", str(exc))
            return

        converter = registry.get_converter(request.source_format, request.target_format)
        _set_busy(True, "Preparing AMPR command..." if dry_run else "Running AMPR conversion...")

        def _progress(event: ProgressEvent) -> None:
            parent.after(0, lambda: status_var.set(event.message))

        def _worker() -> None:
            result = converter.convert(request, _progress)
            def _finish() -> None:
                _set_busy(False, "Done." if result.ok else "Failed.")
                if result.details.get("args"):
                    _log(" ".join(str(part) for part in result.details["args"]))
                if result.details.get("output"):
                    _log(str(result.details["output"]))
                if result.ok:
                    title = "AMPR dry run" if dry_run else "AMPR complete"
                    messagebox.showinfo(title, result.message)
                else:
                    messagebox.showerror("AMPR failed", result.message)
            parent.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    run_button = make_themed_button(
        backend_card.actions,
        "Run conversion",
        command=lambda: _run(False),
        kind="success",
        icon=">",
    )
    run_button.pack(side="right", padx=(8, 0))
    dry_button = make_themed_button(
        backend_card.actions,
        "Dry run",
        command=lambda: _run(True),
        kind="ghost",
    )
    dry_button.pack(side="right", padx=(8, 0))
