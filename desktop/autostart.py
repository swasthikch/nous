"""Windows 11 Autostart Manager for NOUS Desktop Companion (Phase 6).

Configures silent background autostart on Windows logon using the user's
Startup folder or Task Scheduler. Uses a silent VBScript launcher so no
distracting black CMD windows appear when logging in.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_windows_startup_folder() -> Path:
    """Return the current Windows user's Startup directory."""
    appdata = os.getenv("APPDATA")
    if appdata:
        p = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if p.exists():
            return p
    # Fallback to local project directory
    return PROJECT_ROOT / "deploy" / "windows"


class WindowsAutostartManager:
    """Installs or removes NOUS background autostart launchers."""

    def __init__(self) -> None:
        self.startup_dir = get_windows_startup_folder()
        self.vbs_launcher_path = self.startup_dir / "NOUS_Companion_Silent.vbs"
        self.bat_runner_path = PROJECT_ROOT / "deploy" / "windows" / "start_companion_background.bat"

    def is_autostart_installed(self) -> bool:
        """Check whether the autostart launcher exists in the user's Startup folder."""
        return self.vbs_launcher_path.exists()

    def install(self, server_url: str = "http://127.0.0.1:8000") -> dict[str, Any]:
        """Create silent background autostart launcher for Windows 11."""
        self.bat_runner_path.parent.mkdir(parents=True, exist_ok=True)
        py_exe = sys.executable

        # 1. Create the batch runner
        bat_content = f"""@echo off
cd /d "{PROJECT_ROOT}"
"{py_exe}" -m desktop.companion "{server_url}" > "{PROJECT_ROOT}\\data\\companion.log" 2>&1
"""
        self.bat_runner_path.write_text(bat_content, encoding="utf-8")

        # 2. Create the silent VBScript wrapper (0 = hidden window)
        vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{self.bat_runner_path}" & chr(34), 0
Set WshShell = Nothing
"""
        try:
            self.vbs_launcher_path.parent.mkdir(parents=True, exist_ok=True)
            self.vbs_launcher_path.write_text(vbs_content, encoding="utf-8")
            return {
                "success": True,
                "installed": True,
                "vbs_path": str(self.vbs_launcher_path),
                "runner_path": str(self.bat_runner_path),
                "message": "Silent autostart registered in Windows Startup folder.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def uninstall(self) -> dict[str, Any]:
        """Remove autostart launcher."""
        try:
            if self.vbs_launcher_path.exists():
                self.vbs_launcher_path.unlink()
            return {"success": True, "installed": False, "message": "Autostart launcher removed."}
        except Exception as e:
            return {"success": False, "error": str(e)}


autostart_manager = WindowsAutostartManager()
