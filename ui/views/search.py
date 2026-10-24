"""
Apex Windows Optimizer - Search View
Modular renderer and dispatch controller for universal tweak search results.
"""

import threading
import tkinter as tk
from ui.theme import THEME, FONT_FAMILY
from ui.components import ModernCard, ToggleSwitch
from ui.search_data import ALL_SEARCHABLE_TWEAKS
from ui.views.common import render_section_header, create_scrollable_container


def render_search_results(app, query: str):
    """Renders cross-category search results with live inline toggles."""
    app.active_tab = "search"
    for tid, btn in app.tab_buttons.items():
        btn.configure(bg=THEME["bg_sidebar"], fg=THEME["text_muted"], font=(FONT_FAMILY, 9))

    for w in app.content_container.winfo_children():
        w.destroy()

    render_section_header(
        app,
        f"Search Results: '{query}'",
        "Instantly view and toggle matching optimizations across all system categories."
    )

    scroll_canvas, scroll_content = create_scrollable_container(app)

    matched = [
        t for t in ALL_SEARCHABLE_TWEAKS
        if query in t[0].lower() or query in t[2].lower() or query in t[3].lower() or query in t[1].lower()
    ]

    if not matched:
        no_card = ModernCard(scroll_content)
        no_card.pack(fill=tk.X, pady=(20, 0))
        tk.Label(
            no_card,
            text="🔍 No matching tweaks found",
            font=(FONT_FAMILY, 11, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"]
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            no_card,
            text=f"No system optimizations matched '{query}'. Try searching for 'telemetry', 'gaming', 'dns', 'battery', or 'gpu'.",
            font=(FONT_FAMILY, 9),
            fg=THEME["text_muted"],
            bg=THEME["bg_card"]
        ).pack(anchor="w")
        return

    cat_names = {
        "system": "System Performance",
        "privacy": "Privacy & Tracking",
        "explorer": "Explorer & Shell",
        "gaming": "Gaming & GPU",
        "battery": "Battery & Power"
    }

    for key, tab, title, desc in matched:
        card = ModernCard(scroll_content)
        card.pack(fill=tk.X, pady=(0, 8))

        curr_val = app.live_states.get(key, True)
        chip = cat_names.get(tab, tab.capitalize())

        def make_cmd(k=key, t=tab, tit=title):
            return lambda state: apply_search_toggle(app, k, t, tit, state)

        t_switch = ToggleSwitch(card, title, desc, default=curr_val, command=make_cmd(), category_chip=chip)
        t_switch.pack(fill=tk.X)


def apply_search_toggle(app, key: str, tab: str, title: str, state: bool):
    """Dispatches search toggle changes to corresponding engine modules."""
    app.live_states[key] = state
    def worker():
        if tab == "system":
            app.engine.apply_system_performance_tweaks({key: state})
        elif tab == "privacy":
            app.engine.apply_privacy_telemetry_tweaks({key: state})
        elif tab == "explorer":
            app.engine.apply_explorer_ui_tweaks({key: state})
        elif tab == "gaming":
            app.engine.apply_gaming_tweaks({key: state})
        elif tab == "battery":
            if key == "processor_eco":
                app.engine.toggle_processor_eco(state)
            elif key == "pcie_aspm":
                app.engine.toggle_pcie_aspm(state)
            elif key == "fast_startup":
                app.engine.set_fast_startup(not state)
        st_text = "Enabled [OPTIMIZED]" if state else "Reverted [DEFAULT]"
        app.root.after(0, lambda: app.show_toast(f"Tweak Updated", f"{title}: {st_text}", "success" if state else "info"))
    threading.Thread(target=worker, daemon=True).start()
