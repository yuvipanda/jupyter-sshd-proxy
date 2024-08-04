import os
import shutil
import subprocess

from typing import Any, Dict

HOSTKEY_PATH = os.path.expanduser('~/.ssh/jupyter_sshd_hostkey')

def setup_sshd() -> Dict[str, Any]:
    if not os.path.exists(HOSTKEY_PATH):
        # Create a per-user hostkey if it does not exist
        os.makedirs(os.path.dirname(HOSTKEY_PATH), mode=0o700, exist_ok=True)
        subprocess.check_call(['ssh-keygen', '-f', HOSTKEY_PATH, '-q', '-N', ''])

    sshd_path = shutil.which('sshd')

    cmd = [
        sshd_path, '-h', HOSTKEY_PATH, '-D', '-e',
        '-o', 'ListenAddress 127.0.0.1:{port}'
    ]
    return {
        "command": cmd,
        "raw_socket_proxy": True,
        "timeout": 60,
        "launcher_entry": {"enabled": False},
    }
