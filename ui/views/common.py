"""
Apex Windows Optimizer - UI Views Common Helpers
Reusable header banners, scrollable canvases, and section hero components.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Tuple
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard


def render_section_hero(app, title: str, subtitle: str, tweak_keys: List[str], toggle_dict: Dict, on_apply: Callable, icon: str = "⚡") -> Callable:
    """
    Renders a state-of-the-art Windows 11 Fluent Category Hero Banner with:
    - Category Title and Description
    - Live Progress Bar (X of Y Optimizations Active)
    - 1-Click Quick Action Buttons: '✨ Recommend All', '↩️ Reset Defaults', '💾 Save & Apply'
    """
    hero_card = ModernCard(app.content_container, pady=12, padx=16)
    hero_card.pack(fill=tk.X, pady=(0, 12))

    top_row = tk.Frame(hero_card, bg=THEME["bg_card"])
    top_row.pack(fill=tk.X)

    title_box = tk.Frame(top_row, bg=THEME["bg_card"])
    title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

    h_title = tk.Label(
        title_box,
        text=f"{icon}  {title}",
        font=(FONT_FAMILY, 13, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_card"]
    )
    h_title.pack(anchor="w")

    h_sub = tk.Label(
        title_box,
        text=subtitle,
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card"],
        wraplength=520,
        justify="left"
    )
    h_sub.pack(anchor="w", pady=(2, 0))

    # Quick Actions on Right
    actions_frame = tk.Frame(top_row, bg=THEME["bg_card"])
    actions_frame.pack(side=tk.RIGHT)

    def recommend_all():
        for k in tweak_keys:
            if k in toggle_dict:
                target = False if k == "fast_startup" else True
                toggle_dict[k].set(target)
        update_hero_meter()

    def reset_all():
        for k in tweak_keys:
            if k in toggle_dict:
                target = True if k == "fast_startup" else False
                toggle_dict[k].set(target)
        update_hero_meter()

    rec_btn = tk.Button(
        actions_frame,
        text="✨ Recommend All",
        font=(FONT_FAMILY, 8, "bold"),
        fg=THEME["accent_cyan"],
        bg=THEME["bg_card_alt"],
        activebackground=THEME["border"],
        activeforeground=THEME["text_main"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=5,
        command=recommend_all
    )
    rec_btn.pack(side=tk.LEFT, padx=(0, 6))

    rst_btn = tk.Button(
        actions_frame,
        text="↩️ Reset Defaults",
        font=(FONT_FAMILY, 8),
        fg=THEME["text_muted"],
        bg=THEME["bg_card_alt"],
        activebackground=THEME["border"],
        activeforeground=THEME["text_main"],
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=5,
        command=reset_all
    )
    rst_btn.pack(side=tk.LEFT, padx=(0, 6))

    apply_btn = tk.Button(
        actions_frame,
        text="💾 Save & Apply",
        font=(FONT_FAMILY, 8, "bold"),
        fg="#FFFFFF",
        bg=THEME["primary"],
        activebackground=THEME["primary_hover"],
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=5,
        command=on_apply
    )
    apply_btn.pack(side=tk.LEFT)

    # Bottom Row: Category Progress Meter
    progress_row = tk.Frame(hero_card, bg=THEME["bg_card"])
    progress_row.pack(fill=tk.X, pady=(10, 0))

    meter_lbl = tk.Label(
        progress_row,
        text="Calculating status...",
        font=(FONT_FAMILY, 8, "bold"),
        fg=THEME["primary_light"],
        bg=THEME["bg_card"]
    )
    meter_lbl.pack(side=tk.LEFT)

    prog_bar = ttk.Progressbar(progress_row, mode="determinate", length=220, style="TProgressbar")
    prog_bar.pack(side=tk.RIGHT)

    def update_hero_meter():
        active_count = 0
        total_count = len(tweak_keys)
        for k in tweak_keys:
            if k in toggle_dict:
                val = toggle_dict[k].get()
                if (k == "fast_startup" and not val) or (k != "fast_startup" and val):
                    active_count += 1
        pct = int((active_count / total_count * 100)) if total_count > 0 else 0
        meter_lbl.config(text=f"CATEGORY OPTIMIZATION: {active_count} of {total_count} Active ({pct}%)")
        prog_bar['value'] = pct

    hero_card.after(50, update_hero_meter)
    return update_hero_meter


def render_section_header(app, title: str, subtitle: str):
    """Renders a standard clean section title and subtitle."""
    title_frame = tk.Frame(app.content_container, bg=THEME["bg_app"])
    title_frame.pack(fill=tk.X, pady=(0, 14))

    tk.Label(
        title_frame,
        text=title,
        font=(FONT_FAMILY, 14, "bold"),
        fg=THEME["text_main"],
        bg=THEME["bg_app"]
    ).pack(anchor="w")

    tk.Label(
        title_frame,
        text=subtitle,
        font=(FONT_FAMILY, 9),
        fg=THEME["text_muted"],
        bg=THEME["bg_app"]
    ).pack(anchor="w", pady=(2, 0))


def create_scrollable_container(app) -> Tuple[tk.Canvas, tk.Frame]:
    """Creates a smooth scrollable canvas container inside content_container."""
    container = tk.Frame(app.content_container, bg=THEME["bg_app"])
    container.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(container, bg=THEME["bg_app"], highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=THEME["bg_app"])

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    def on_canvas_configure(event):
        canvas.itemconfig(window_id, width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Scoped mousewheel binding
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _bind_wheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_wheel(event):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _bind_wheel)
    canvas.bind("<Leave>", _unbind_wheel)

    return canvas, scrollable_frame
