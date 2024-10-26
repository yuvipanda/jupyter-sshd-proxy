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
from urllib.request import urlopen, Request
from urllib.error import URLError

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

    # sshd requires that the path to the authorized keys (and every ancestor) is fully owned
    # by the user who is trying to log in (or root), and mode is not group or world writeable.
    # Since that's not necessarily true for `/tmp`, we can not put our keys there for tests.
    # Create them instead in cwd, which we assume matches this description instead. We
    # clean up after ourselves.
    dir_prefix = os.path.join(os.getcwd(), "tmp-")
    with tempfile.TemporaryDirectory(prefix=dir_prefix) as temp_dir:
        os.chmod(temp_dir, 0o700)
        authorized_keys_path = os.path.join(temp_dir, 'authorized_keys')
        subprocess.check_call(['ssh-keygen', '-f', authorized_keys_path, '-q', '-N', ''])

        env['JUPYTER_SSHD_PROXY_AUTHORIZED_KEYS_PATH'] = authorized_keys_path + '.pub'
        proc = subprocess.Popen(c, env=env)

        # Wait for server to be fully up before we yield
        req = Request(f"http://127.0.0.1:{random_port}/api/status", headers={"Authorization": f"token {token}"})
        while True:
            try:
                resp = urlopen(req)
                if resp.status == 200:
                    break
            except URLError as e:
                if not isinstance(e.reason, ConnectionRefusedError):
                    raise
            print("Waiting for jupyter server to come up...")
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
        'ssh',
    ] + [f"-o={o}" for o in get_ssh_client_options(*jupyter_server)] + ['127.0.0.1', 'hostname']

    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    print(proc.stderr)

    assert proc.stdout.decode().strip() == socket.gethostname()


def test_ssh_interactive(jupyter_server):
    # Explicitly call /bin/sh without any args, so we can run without any prompts
    cmd = [
        'ssh',
    ] + [f"-o={o}" for o in get_ssh_client_options(*jupyter_server)] + ['127.0.0.1', '/bin/sh']

    proc = pexpect.spawn(shlex.join(cmd), echo=False)
    proc.sendline('hostname')
    assert proc.readline().decode().strip() == socket.gethostname()
    proc.sendline("exit")
    proc.wait()
    assert proc.exitstatus == 0


# Test for both the sftp protocol (default on newer scp) ("-s"), and the older
# scp protocol ("-O").
@pytest.mark.parametrize("extra_scp_args", [["-s"], ["-O"]])
def test_scp(jupyter_server, extra_scp_args):
    with tempfile.NamedTemporaryFile() as f, tempfile.TemporaryDirectory() as d:
        file_contents = secrets.token_hex()
        f.write(file_contents.encode())
        f.flush()

        target_path = os.path.join(d, "target")

        cmd = [
            'scp', '-v',
        ] + extra_scp_args + [f"-o={o}" for o in get_ssh_client_options(*jupyter_server)] + [
            f.name, f'127.0.0.1:{target_path}'
        ]

        proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        with open(target_path) as tpf:
            assert tpf.read() == file_contents