"""
Apex Windows Optimizer - Live Activity Log Terminal View
Modular renderer and action handlers for real-time activity stream,
log copying, and file export.
"""

import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard
from ui.views.common import render_section_header


def render_terminal_log(app):
    """Renders the real-time activity logging console."""
    render_section_header(
        app,
        "Live Activity & Command Log",
        "Real-time stream of all system optimization actions, registry changes, and PowerShell results."
    )

    toolbar = ModernCard(app.content_container)
    toolbar.pack(fill=tk.X, pady=(0, 8))

    tk.Button(
        toolbar,
        text="📋 Copy Log",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_main"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4,
        command=lambda: action_copy_log(app)
    ).pack(side=tk.LEFT, padx=(0, 8))

    tk.Button(
        toolbar,
        text="💾 Save Log to File",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_main"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4,
        command=lambda: action_save_log(app)
    ).pack(side=tk.LEFT, padx=(0, 8))

    tk.Button(
        toolbar,
        text="🗑️ Clear Terminal",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card_alt"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=4,
        command=lambda: action_clear_log(app)
    ).pack(side=tk.LEFT)

    term_frame = tk.Frame(app.content_container, bg=THEME["bg_input"])
    term_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(term_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    app.terminal_text = tk.Text(
        term_frame,
        bg=THEME["bg_input"],
        fg=THEME["text_main"],
        font=("Consolas", 9),
        relief="flat",
        wrap=tk.WORD,
        yscrollcommand=scrollbar.set,
        highlightbackground=THEME["border"],
        highlightthickness=1,
        padx=12,
        pady=12
    )
    app.terminal_text.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=app.terminal_text.yview)

    app.terminal_text.tag_config("TIME", foreground=THEME["text_dim"])
    app.terminal_text.tag_config("INFO", foreground=THEME["accent_cyan"])
    app.terminal_text.tag_config("SUCCESS", foreground=THEME["success"])
    app.terminal_text.tag_config("WARNING", foreground=THEME["warning"])
    app.terminal_text.tag_config("ERROR", foreground=THEME["danger"])
    app.terminal_text.tag_config("MSG", foreground=THEME["text_main"])

    if os.path.exists(app.engine.session_log_path):
        try:
            with open(app.engine.session_log_path, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line:
                        parts = line.split(" ", 2)
                        if len(parts) >= 3 and parts[1].startswith("[") and parts[1].endswith("]"):
                            lvl = parts[1][1:-1]
                            app.terminal_text.insert(tk.END, f"{parts[0]} ", "TIME")
                            app.terminal_text.insert(tk.END, f"{parts[1]} ", lvl)
                            app.terminal_text.insert(tk.END, f"{parts[2]}\n", "MSG")
                        else:
                            app.terminal_text.insert(tk.END, f"{line}\n", "MSG")
        except Exception:
            pass


def action_copy_log(app):
    """Copies current terminal text to system clipboard."""
    content = app.terminal_text.get("1.0", tk.END)
    app.root.clipboard_clear()
    app.root.clipboard_append(content)
    messagebox.showinfo("Apex Optimizer", "Activity log copied to clipboard.")


def action_save_log(app):
    """Prompts file save dialog to export session log."""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".log",
        filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
        initialfile=f"ApexOptimizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    if file_path:
        content = app.terminal_text.get("1.0", tk.END)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Apex Optimizer", f"Log saved to: {file_path}")


def action_clear_log(app):
    """Clears all text from the live terminal display."""
    app.terminal_text.delete("1.0", tk.END)
