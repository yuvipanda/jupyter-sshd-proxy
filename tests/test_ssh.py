import tempfile
import pexpect
import os
import shlex
import pytest
import subprocess
import secrets
import getpass
import time
import socket

@pytest.fixture
def random_port():
    """Get a single random port."""
    # You aren't supposed to do this but who is gonna stop me?
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def jupyter_server(random_port):
    token = secrets.token_hex(16)
    c = [
        'jupyter', 'server',
        f'--port={random_port}', f'--ServerApp.token={token}', '--ip=127.0.0.1',
        '--no-browser'
    ]
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as temp_dir:
        authorized_keys_path = os.path.join(temp_dir, 'authorized_keys')
        subprocess.check_call(['ssh-keygen', '-f', authorized_keys_path, '-q', '-N', ''])

        env['JUPYTER_SSHD_PROXY_AUTHORIZED_KEYS_PATH'] = authorized_keys_path + '.pub'
        proc = subprocess.Popen(c, env=env)

        # Should healthcheck instead but HEY
        time.sleep(1)

        yield (random_port, token, authorized_keys_path)

        proc.kill()
        proc.wait()


def get_ssh_client_options(random_port, token, authorized_keys_path):
    return  [
        f'ProxyCommand=websocat --binary -H="Authorization: token {token}" asyncstdio: ws://%h:{random_port}/sshd/',
        f'User={getpass.getuser()}',
        f'IdentityFile={authorized_keys_path}',
        'StrictHostKeyChecking=no' # FIXME: Validate this correctly later
    ]

def test_ssh_command_execution(jupyter_server):
    cmd = [
        'ssh', '-v',
    ] + [f"-o={o}" for o in get_ssh_client_options(*jupyter_server)] + ['127.0.0.1', 'hostname']

    out = subprocess.check_output(cmd).decode().strip()

    assert out == socket.gethostname()


def test_ssh_interactive(jupyter_server):
    cmd = [
        'ssh', '-v',
    ] + [f"-o={o}" for o in get_ssh_client_options(*jupyter_server)] + ['127.0.0.1', 'hostname']

    proc = pexpect.spawn(shlex.join(cmd), echo=False)
    proc.sendline('hostname')
    assert proc.readline().decode().strip() == socket.gethostname()
    proc.wait()
    assert proc.exitstatus == 0

