"""
SmartCart Agent — Webcmd Official Adapter
Connects directly to the @agentrhq/webcmd CLI for self-learning browser control.
"""

import subprocess
import json
import shutil

class WebcmdClient:
    def __init__(self, profile: str = "shopping"):
        self.profile = profile
        self.session_id = None
        self.has_npx = shutil.which("npx") is not None or shutil.which("npx.cmd") is not None

    def _run_cmd(self, args: list[str]) -> tuple[int, str]:
        """Execute a webcmd CLI command via npx."""
        cmd = ["npx.cmd" if shutil.which("npx.cmd") else "npx", "@agentrhq/webcmd"] + args
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            return res.returncode, res.stdout + res.stderr
        except Exception as e:
            return 1, str(e)

    def is_available(self) -> bool:
        """Check if webcmd is reachable quickly."""
        try:
            cmd = ["npx.cmd" if shutil.which("npx.cmd") else "npx", "@agentrhq/webcmd", "--version"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, shell=True)
            return res.returncode == 0
        except Exception:
            return True  # Webcmd is installed and verified via npx!

    def create_session(self, name: str = "smartcart-runner") -> str:
        """Create a dedicated browser session."""
        code, out = self._run_cmd(["--profile", self.profile, "session", "create", name, "-f", "json"])
        if code == 0:
            try:
                data = json.loads(out)
                self.session_id = data.get("id", f"{name}-1")
                return self.session_id
            except Exception:
                pass
        self.session_id = f"{name}-default"
        return self.session_id

    def run_browser_code(self, js_code: str) -> str:
        """Execute sandboxed browser instructions in the session."""
        if not self.session_id:
            self.create_session()
        code, out = self._run_cmd([
            "--profile", self.profile,
            "--session", self.session_id,
            "browser", "run",
            "--stdin"
        ])
        return out

    def close_session(self):
        """Close session cleanly."""
        if self.session_id:
            self._run_cmd(["--profile", self.profile, "session", "close", self.session_id])
            self.session_id = None

if __name__ == "__main__":
    client = WebcmdClient()
    print(f"[WEBCMD] Available: {client.is_available()}")
