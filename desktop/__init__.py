"""NOUS Windows 11 Desktop Companion Package (Phase 6)."""

from desktop.telemetry import windows_telemetry, WindowsHardwareReport
from desktop.companion import desktop_companion, DesktopCompanion
from desktop.autostart import autostart_manager, WindowsAutostartManager

__all__ = [
    "windows_telemetry",
    "WindowsHardwareReport",
    "desktop_companion",
    "DesktopCompanion",
    "autostart_manager",
    "WindowsAutostartManager",
]
