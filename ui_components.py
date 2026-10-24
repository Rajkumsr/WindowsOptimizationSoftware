"""
Apex Windows Optimizer - Modular UI Components & Custom Tkinter Widgets
Contains reusable widgets:
- ModernCard
- ToggleSwitch
- DonutGauge
- ToastManager
- get_app_icon_path (Centralized icon resolver)
"""

import os
import sys
import tkinter as tk
from typing import Optional, Callable
from theme import THEME, FONT_FAMILY

def get_app_icon_path() -> Optional[str]:
    """Resolves and returns the absolute path to the application icon if present."""
    candidates = [
        os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "app_icon.ico"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.ico")
    ]
    for ic in candidates:
        if ic and os.path.exists(ic):
            return ic
    return None


class ToastManager:
    """Manages non-blocking floating dark toast notifications inside the app window."""
    def __init__(self, root: tk.Tk):
        self.root = root
        self.active_toasts = []

    def show(self, title: str, message: str, toast_type: str = "success", duration_ms: int = 3500):
        icon_map = {
            "success": ("✅", THEME["success"]),
            "boost": ("⚡", THEME["primary"]),
            "warning": ("⚠️", THEME["warning"]),
            "info": ("ℹ️", THEME["accent_cyan"]),
            "danger": ("❌", THEME["danger"])
        }
        icon_symbol, border_col = icon_map.get(toast_type, ("ℹ️", THEME["primary"]))

        toast_frame = tk.Frame(
            self.root,
            bg=THEME["bg_card"],
            highlightbackground=border_col,
            highlightthickness=1,
            padx=14,
            pady=10
        )

        top_row = tk.Frame(toast_frame, bg=THEME["bg_card"])
        top_row.pack(fill=tk.X)

        tk.Label(
            top_row,
            text=icon_symbol,
            font=(FONT_FAMILY, 11),
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(
            top_row,
            text=title,
            font=(FONT_FAMILY, 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(side=tk.LEFT)

        close_btn = tk.Label(
            top_row,
            text="✕",
            font=(FONT_FAMILY, 8, "bold"),
            fg=THEME["text_dim"],
            bg=THEME["bg_card"],
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=(10, 0))

        tk.Label(
            toast_frame,
            text=message,
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            wraplength=280,
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

        self.active_toasts.append(toast_frame)
        self._reposition()

        def dismiss(event=None):
            if toast_frame in self.active_toasts:
                self.active_toasts.remove(toast_frame)
                try:
                    toast_frame.destroy()
                except Exception:
                    pass
                self._reposition()

        close_btn.bind("<Button-1>", dismiss)
        toast_frame.bind("<Button-1>", dismiss)
        self.root.after(duration_ms, dismiss)

    def _reposition(self):
        base_y = -35
        offset = 0
        for t in reversed(self.active_toasts):
            try:
                t.place(relx=1.0, rely=1.0, x=-24, y=base_y - offset, anchor="se")
                offset += 80
            except Exception:
                pass


class DonutGauge(tk.Canvas):
    """
    An anti-aliased circular donut gauge that displays and animates
    the System Health & Optimization Score using Windows system accent colors.
    """
    def __init__(self, parent, size: int = 100, thickness: int = 8, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=THEME["bg_card"],
            highlightthickness=0,
            **kwargs
        )
        self.size = size
        self.thickness = thickness
        self.current_score = 0
        self.target_score = 0
        self.rating_text = "OPTIMIZING"
        self.accent_color = THEME["primary"]
        self._animating = False

    def set_score(self, score: int, rating: str, color: str = None, animate: bool = True):
        self.target_score = max(0, min(100, int(score)))
        self.rating_text = rating
        self.accent_color = color if color else THEME["primary"]

        if animate and not self._animating:
            self._animate_step()
        elif not animate:
            self.current_score = self.target_score
            self.redraw()

    def _animate_step(self):
        self._animating = True
        diff = self.target_score - self.current_score
        if abs(diff) > 0:
            step = 1 if diff > 0 else -1
            if abs(diff) > 10:
                step = diff // 5
            self.current_score += step
            self.redraw()
            self.after(20, self._animate_step)
        else:
            self.current_score = self.target_score
            self.redraw()
            self._animating = False

    def redraw(self):
        self.delete("all")
        pad = 6
        x0 = pad
        y0 = pad
        x1 = self.size - pad
        y1 = self.size - pad

        # 1. Background full track
        self.create_oval(
            x0, y0, x1, y1,
            outline=THEME["border"],
            width=self.thickness
        )

        # 2. Progress swept arc in Windows Accent Color
        extent = -(self.current_score / 100.0) * 360.0
        if abs(extent) > 0.1:
            self.create_arc(
                x0, y0, x1, y1,
                start=90,
                extent=extent,
                style=tk.ARC,
                outline=self.accent_color,
                width=self.thickness
            )

        # 3. Inner text display
        cx = self.size / 2
        cy = self.size / 2
        self.create_text(
            cx, cy - 6,
            text=f"{int(self.current_score)}%",
            font=(FONT_FAMILY, 11, "bold"),
            fill=THEME["text_main"]
        )
        self.create_text(
            cx, cy + 9,
            text=self.rating_text[:8],
            font=(FONT_FAMILY, 6, "bold"),
            fill=self.accent_color
        )


class ModernCard(tk.Frame):
    """Sleek dark panel card with subtle highlight border."""
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", THEME["bg_card"])
        super().__init__(
            parent,
            bg=bg,
            highlightbackground=THEME["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
            **kwargs
        )


class ToggleSwitch(tk.Frame):
    """
    State-of-the-art interactive toggle switch with real-time state badge,
    optional category chip for search results, and hover animation.
    """
    def __init__(self, parent, title: str, description: str, default: bool = True,
                 command: Optional[Callable[[bool], None]] = None,
                 category_chip: Optional[str] = None):
        super().__init__(parent, bg=THEME["bg_card"])
        self.state = bool(default)
        self.command = command

        # Text Column (Left)
        text_frame = tk.Frame(self, bg=THEME["bg_card"])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header_row = tk.Frame(text_frame, bg=THEME["bg_card"])
        header_row.pack(anchor="w")

        if category_chip:
            chip_lbl = tk.Label(
                header_row,
                text=category_chip.upper(),
                font=(FONT_FAMILY, 7, "bold"),
                fg=THEME["accent_cyan"],
                bg=THEME["bg_card_alt"],
                padx=6,
                pady=1
            )
            chip_lbl.pack(side=tk.LEFT, padx=(0, 8))

        title_lbl = tk.Label(
            header_row,
            text=title,
            font=(FONT_FAMILY, 10, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        )
        title_lbl.pack(side=tk.LEFT)

        desc_lbl = tk.Label(
            text_frame,
            text=description,
            font=(FONT_FAMILY, 8),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            wraplength=640,
            justify="left"
        )
        desc_lbl.pack(anchor="w", pady=(2, 0))

        # Status Badge Pill
        self.badge_lbl = tk.Label(
            self,
            font=(FONT_FAMILY, 7, "bold"),
            padx=8,
            pady=3,
            relief="flat"
        )
        self.badge_lbl.pack(side=tk.RIGHT, padx=(10, 0))

        # Canvas Toggle Switch (Right)
        self.canvas = tk.Canvas(
            self,
            width=46,
            height=24,
            bg=THEME["bg_card"],
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(side=tk.RIGHT, padx=(12, 0))
        self.canvas.bind("<Button-1>", self.toggle)
        self.render()

    def render(self):
        self.canvas.delete("all")
        if self.state:
            # Active (ON) state
            self.canvas.create_oval(2, 2, 22, 22, fill=THEME["primary"], outline="")
            self.canvas.create_oval(24, 2, 44, 22, fill=THEME["primary"], outline="")
            self.canvas.create_rectangle(12, 2, 34, 22, fill=THEME["primary"], outline="")
            # Knob
            self.canvas.create_oval(24, 4, 42, 20, fill="#FFFFFF", outline="")
            # Badge
            self.badge_lbl.config(
                text="OPTIMIZED",
                fg=THEME["success"],
                bg=THEME["success_bg"]
            )
        else:
            # Inactive (OFF) state
            self.canvas.create_oval(2, 2, 22, 22, fill=THEME["border"], outline="")
            self.canvas.create_oval(24, 2, 44, 22, fill=THEME["border"], outline="")
            self.canvas.create_rectangle(12, 2, 34, 22, fill=THEME["border"], outline="")
            # Knob
            self.canvas.create_oval(4, 4, 22, 20, fill=THEME["text_muted"], outline="")
            # Badge
            self.badge_lbl.config(
                text="DEFAULT",
                fg=THEME["text_dim"],
                bg=THEME["bg_input"]
            )

    def toggle(self, event=None):
        self.state = not self.state
        self.render()
        if self.command:
            self.command(self.state)

    def get(self) -> bool:
        return self.state

    def set(self, val: bool):
        self.state = val
        self.render()
