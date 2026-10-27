import contextlib
import io
import os
import sys
import tempfile
import types
import unittest
import winreg
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main
import build_exe
from core.cleanup import CleanupMixin
from core.base import BaseEngine
from core.diagnostics import DiagnosticsMixin
from core.services import ServicesMixin
from ui.app import ApexOptimizerApp
from ui.views import dashboard


class CleanupEngine(CleanupMixin):
    def __init__(self, targets):
        self.targets = targets
        self.messages = []
        self.command_result = (0, "")

    def get_cleanup_targets(self):
        return self.targets

    def run_cmd(self, command):
        return self.command_result

    def log(self, message, level="INFO"):
        self.messages.append((message, level))


class ServicesEngine(ServicesMixin):
    def __init__(self, command_result):
        self.command_result = command_result
        self.messages = []
        self.script = ""

    def run_ps(self, script):
        self.script = script
        return self.command_result

    def log(self, message, level="INFO"):
        self.messages.append((message, level))


class ImprovementTests(unittest.TestCase):
    def test_cleanup_counts_only_successfully_deleted_file_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "top.bin").write_bytes(b"12345")
            nested = root / "nested"
            nested.mkdir()
            (nested / "inner.bin").write_bytes(b"1234567")
            engine = CleanupEngine([{"id": "test", "name": "Test", "path": str(root)}])

            freed, formatted, failures = engine.execute_cleanup(["test"])

            self.assertEqual(freed, 12)
            self.assertEqual(formatted, "12 B")
            self.assertEqual(failures, 0)
            self.assertEqual(list(root.iterdir()), [])

    def test_cleanup_does_not_count_files_that_could_not_be_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "kept.bin").write_bytes(b"12345")
            (root / "removed.bin").write_bytes(b"123")
            engine = CleanupEngine([{"id": "test", "name": "Test", "path": str(root)}])
            original_remove = os.remove

            def remove_with_locked_file(path):
                if path.endswith("kept.bin"):
                    raise PermissionError("locked")
                original_remove(path)

            with patch("core.cleanup.os.remove", side_effect=remove_with_locked_file):
                freed, _, failures = engine.execute_cleanup(["test"])

            self.assertEqual(freed, 3)
            self.assertEqual(failures, 1)
            self.assertTrue((root / "kept.bin").exists())
            self.assertTrue(any(level == "WARNING" for _, level in engine.messages))

    def test_winsxs_estimate_is_not_fabricated(self):
        engine = CleanupEngine([{"id": "winsxs", "name": "WinSxS", "path": ""}])
        sizes = engine.scan_cleanup_sizes()
        self.assertEqual(sizes["winsxs"], (0, "Estimate unavailable (DISM)"))

    def test_build_cleanup_preserves_tracked_spec_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_dir = root / "build"
            build_dir.mkdir()
            (build_dir / "temporary.txt").write_text("temporary", encoding="utf-8")
            spec_file = root / "ApexWindowsOptimizer.spec"
            spec_file.write_text("tracked spec", encoding="utf-8")

            build_exe.clean_previous_builds(str(root))

            self.assertTrue(spec_file.exists())
            self.assertFalse(build_dir.exists())

    def test_services_report_partial_failures_and_reject_invalid_names(self):
        engine = ServicesEngine((0, "OK:DiagTrack\nERR:MapsBroker:access denied\n"))

        count = engine.optimize_services([
            ("DiagTrack", "disabled"),
            ("MapsBroker", "demand"),
            ("Bad'; Write-Output 'INJECTED", "disabled"),
        ])

        self.assertEqual(count, 1)
        self.assertNotIn("INJECTED", engine.script)
        self.assertTrue(any(level == "ERROR" for _, level in engine.messages))
        self.assertTrue(any(level == "WARNING" for _, level in engine.messages))

    def test_registry_fallback_failures_are_logged(self):
        engine = object.__new__(BaseEngine)
        engine.log = Mock()
        engine.run_cmd = Mock(return_value=(1, "access denied"))

        with patch("core.base.winreg.CreateKeyEx", side_effect=OSError("registry unavailable")):
            result = engine.set_reg(
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Test",
                "Example",
                1,
            )

        self.assertFalse(result)
        engine.log.assert_called_once()
        self.assertEqual(engine.log.call_args.args[1], "ERROR")

    def test_health_score_uses_live_state_names(self):
        all_score_keys = {
            "network_throttling", "system_responsiveness", "fast_shutdown",
            "disable_telemetry", "optimize_edge", "disable_recall",
            "enable_hags", "mmcss_priority", "disable_power_throttling",
            "irp_stack_size", "long_paths", "disable_p2p_update",
            "disable_lockscreen_ads", "disable_office_telemetry",
            "reset_hpet", "windowed_optimizations",
        }

        result = DiagnosticsMixin.calculate_health_score(
            object(), {key: True for key in all_score_keys}
        )

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["applied_count"], 16)

    def test_status_updates_are_scheduled_on_ui_event_loop(self):
        callbacks = []
        app = object.__new__(ApexOptimizerApp)
        app.root = SimpleNamespace(
            after=lambda delay, callback: callbacks.append(callback),
            winfo_exists=lambda: True,
        )
        app.status_label = SimpleNamespace(config=lambda **kwargs: setattr(app, "status_text", kwargs["text"]))
        app.progress_bar = SimpleNamespace(
            start=lambda interval: setattr(app, "progress_running", True),
            stop=lambda: setattr(app, "progress_running", False),
        )

        app.set_status("Working", is_busy=True)

        self.assertEqual(app.status_text if hasattr(app, "status_text") else None, None)
        self.assertEqual(len(callbacks), 1)
        callbacks.pop()()
        self.assertEqual(app.status_text, "Working")
        self.assertTrue(app.progress_running)

    def test_quick_optimization_aborts_when_backup_fails(self):
        class Engine:
            def __init__(self):
                self.changes_applied = False

            def create_restore_point(self, description):
                return False

            def log(self, message, level):
                pass

            def apply_system_performance_tweaks(self, options):
                self.changes_applied = True

        engine = Engine()
        toasts = []
        app = SimpleNamespace(
            engine=engine,
            set_status=lambda *args, **kwargs: None,
            show_toast=lambda *args: toasts.append(args),
            root=SimpleNamespace(after=lambda delay, callback: callback()),
        )

        class ImmediateThread:
            def __init__(self, target, daemon=True):
                self.target = target

            def start(self):
                self.target()

        with patch.object(dashboard.threading, "Thread", ImmediateThread):
            dashboard.run_quick_optimize(app)

        self.assertFalse(engine.changes_applied)
        self.assertEqual(toasts[0][2], "danger")

    def test_presets_use_engine_option_names_and_require_backup(self):
        class Engine:
            def __init__(self):
                self.calls = []

            def create_restore_point(self, description):
                self.calls.append(("backup", description))
                return True

            def __getattr__(self, name):
                if name.startswith("apply_") or name.startswith("toggle_") or name == "set_fast_startup":
                    def record(*args, **kwargs):
                        self.calls.append((name, args, kwargs))
                        return 1
                    return record
                raise AttributeError(name)

            def disable_telemetry_tasks(self):
                self.calls.append(("disable_telemetry_tasks",))

            def detect_all_tweak_states(self):
                return {}

        def create_app():
            return SimpleNamespace(
                engine=Engine(),
                active_tab="other",
                set_status=lambda *args, **kwargs: None,
                show_toast=lambda *args: None,
                switch_tab=lambda tab: None,
                root=SimpleNamespace(after=lambda delay, callback: callback()),
            )

        class ImmediateThread:
            def __init__(self, target, daemon=True):
                self.target = target

            def start(self):
                self.target()

        with patch.object(dashboard.threading, "Thread", ImmediateThread):
            gaming_app = create_app()
            dashboard.apply_gaming_preset(gaming_app)
            gaming_call = next(call for call in gaming_app.engine.calls if call[0] == "apply_gaming_tweaks")
            self.assertEqual(gaming_app.engine.calls[0][0], "backup")
            self.assertEqual(set(gaming_call[1][0]), {
                "enable_hags", "windowed_optimizations", "mmcss_priority",
                "disable_power_throttling", "ultimate_performance",
            })

            privacy_app = create_app()
            dashboard.apply_privacy_preset(privacy_app)
            explorer_call = next(call for call in privacy_app.engine.calls if call[0] == "apply_explorer_ui_tweaks")
            self.assertEqual(explorer_call[1][0], {"disable_start_bing": True})

            defaults_app = create_app()
            dashboard.apply_defaults_preset(defaults_app)
            defaults_call = next(call for call in defaults_app.engine.calls if call[0] == "apply_gaming_tweaks")
            self.assertEqual(defaults_call[1][0]["enable_hags"], False)
            self.assertEqual(defaults_call[1][0]["mmcss_priority"], False)

    def test_cli_reports_failure_and_skips_restart(self):
        class Engine:
            def __init__(self, log_callback=None):
                pass

            def get_hardware_info(self):
                return {"cpu_name": "Test CPU", "total_ram": "1 GB", "chassis_type": "Test"}

            def run_winget_upgrade_all(self):
                return 1, "failed"

        fake_module = types.ModuleType("core.optimizer")
        fake_module.OptimizationEngine = Engine
        args = SimpleNamespace(
            optimize=False, gaming=False, cleanup=False, boost=False,
            winget=True, restart=True,
        )
        output = io.StringIO()

        with patch.dict(sys.modules, {"core.optimizer": fake_module}), \
                patch.object(main.os, "system") as restart, \
                contextlib.redirect_stdout(output):
            result = main.run_cli_mode(args)

        self.assertEqual(result, 1)
        restart.assert_not_called()
        self.assertIn("[ERROR]", output.getvalue())
        self.assertIn("Restart skipped", output.getvalue())


if __name__ == "__main__":
    unittest.main()
