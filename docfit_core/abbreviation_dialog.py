"""준말 등록·관리 창(Tk). 등록표 저장·불러오기는 호출한 쪽이 넘겨 준 함수로 한다."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .abbreviations import DEFAULT_ENTRIES, FORMAT_KINDS, TYPE_LABELS, describe, normalize, upsert


def open_abbreviation_dialog(parent, load, save):
    """load() -> 등록표(dict), save(등록표) 로 저장한다. 창 객체를 돌려준다."""
    entries = normalize(load())
    window = tk.Toplevel(parent)
    window.title("준말 등록·관리")
    window.geometry("640x470")
    window.transient(parent)
    body = ttk.Frame(window, padding=12)
    body.pack(fill="both", expand=True)
    ttk.Label(body, wraplength=600, justify="left", text=(
        "한/글의 상용구처럼 준말을 본말로 바꿉니다. '한 번에 적용'을 실행하면 줄 맨 앞 어절이 준말이고 "
        "바로 뒤에 콜론(:)이 이어지는 줄(예: 제목1: 지구 침공계획(안) 보고)을 본말로 바꿉니다. "
        "서식 표는 콜론 뒤 글을 표 A1 칸에 넣고, 문구는 준말·콜론을 본말로 바꿔 뒷글에 이어 붙입니다.")
              ).pack(anchor="w", pady=(0, 8))

    tree = ttk.Treeview(body, columns=("key", "type", "value"), show="headings", height=8, selectmode="browse")
    for column, title, width in (("key", "준말", 110), ("type", "종류", 90), ("value", "본말", 400)):
        tree.heading(column, text=title)
        tree.column(column, width=width, anchor="w")
    tree.pack(fill="both", expand=True)

    form = ttk.Frame(body)
    form.pack(fill="x", pady=(10, 0))
    key_var, type_var, format_var, text_var = tk.StringVar(), tk.StringVar(value=TYPE_LABELS["format"]), tk.StringVar(), tk.StringVar()
    ttk.Label(form, text="준말").grid(row=0, column=0, sticky="w")
    ttk.Entry(form, textvariable=key_var, width=14).grid(row=0, column=1, sticky="w", padx=(6, 14))
    ttk.Label(form, text="본말 종류").grid(row=0, column=2, sticky="w")
    type_box = ttk.Combobox(form, textvariable=type_var, state="readonly", width=10, values=list(TYPE_LABELS.values()))
    type_box.grid(row=0, column=3, sticky="w", padx=(6, 0))
    ttk.Label(form, text="본말").grid(row=1, column=0, sticky="w", pady=(8, 0))
    format_box = ttk.Combobox(form, textvariable=format_var, state="readonly", width=34, values=list(FORMAT_KINDS.values()))
    text_entry = ttk.Entry(form, textvariable=text_var, width=52)
    format_box.grid(row=1, column=1, columnspan=3, sticky="w", padx=(6, 0), pady=(8, 0))
    status = tk.StringVar()
    ttk.Label(body, textvariable=status, foreground="#a33").pack(anchor="w", pady=(6, 0))

    kind_by_label = {label: kind for kind, label in TYPE_LABELS.items()}
    format_by_label = {label: kind for kind, label in FORMAT_KINDS.items()}

    def refresh():
        tree.delete(*tree.get_children())
        for key in sorted(entries):
            kind_label, detail = describe(entries[key])
            tree.insert("", "end", iid=key, values=(key, kind_label, detail))

    def switch_type(*_):
        if kind_by_label.get(type_var.get()) == "text":
            format_box.grid_remove()
            text_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=(6, 0), pady=(8, 0))
        else:
            text_entry.grid_remove()
            format_box.grid(row=1, column=1, columnspan=3, sticky="w", padx=(6, 0), pady=(8, 0))

    def persist():
        save(dict(entries))
        refresh()

    def add():
        nonlocal entries
        kind = kind_by_label.get(type_var.get(), "format")
        value = text_var.get() if kind == "text" else format_by_label.get(format_var.get(), "")
        updated, error = upsert(entries, key_var.get(), kind, value)
        status.set(error)
        if not error:
            entries = updated
            persist()
            key_var.set("")
            text_var.set("")

    def remove():
        selected = tree.selection()
        if selected and selected[0] in entries:
            entries.pop(selected[0])
            status.set("")
            persist()

    def load_selected(*_):
        selected = tree.selection()
        if not selected or selected[0] not in entries:
            return
        spec = entries[selected[0]]
        key_var.set(selected[0])
        type_var.set(TYPE_LABELS[spec["type"]])
        switch_type()
        if spec["type"] == "format":
            format_var.set(FORMAT_KINDS[spec["value"]])
        else:
            text_var.set(spec["value"])

    def add_defaults():
        entries.update({k: v for k, v in DEFAULT_ENTRIES.items() if k not in entries})
        status.set("")
        persist()

    buttons = ttk.Frame(body)
    buttons.pack(fill="x", pady=(8, 0))
    ttk.Button(buttons, text="추가·수정", command=add).pack(side="left")
    ttk.Button(buttons, text="삭제", command=remove).pack(side="left", padx=(6, 0))
    ttk.Button(buttons, text="기본 준말 넣기 (제목1·제목2·개요)", command=add_defaults).pack(side="left", padx=(6, 0))
    ttk.Button(buttons, text="닫기", command=window.destroy).pack(side="right")

    type_box.bind("<<ComboboxSelected>>", switch_type)
    tree.bind("<<TreeviewSelect>>", load_selected)
    format_var.set(next(iter(FORMAT_KINDS.values())))
    refresh()
    window.entries_view = tree  # 시험용 접근점
    window._docfit_actions = {"add": add, "remove": remove, "defaults": add_defaults,
                              "vars": (key_var, type_var, format_var, text_var, status)}
    return window
