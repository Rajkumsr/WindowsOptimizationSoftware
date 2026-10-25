"""
Apex Windows Optimizer - Core Optimization Engine
A comprehensive, safe, and modular Windows performance and debloating engine.
Coordinates telemetry, system tweaks, gaming optimizations, power management,
disk maintenance, and service tuning via modular domain mixins.
"""

from typing import Callable, Optional
from .base import BaseEngine, CREATE_NO_WINDOW
from .diagnostics import DiagnosticsMixin
from .tweaks import TweaksMixin
from .gaming import GamingMixin
from .services import ServicesMixin
from .debloat import DebloatMixin
from .cleanup import CleanupMixin
from .power import PowerMixin


class OptimizationEngine(
    DiagnosticsMixin,
    TweaksMixin,
    GamingMixin,
    ServicesMixin,
    DebloatMixin,
    CleanupMixin,
    PowerMixin,
    BaseEngine
):
    """
    Apex Windows Optimizer Engine - Unified Orchestrator.
    Combines all optimization and telemetry mixins into a single, cohesive engine API.
    Maintains 100% backward compatibility with all UI and CLI callers.
    """
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        super().__init__(log_callback=log_callback)


__all__ = ["OptimizationEngine", "CREATE_NO_WINDOW"]
