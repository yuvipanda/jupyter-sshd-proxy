# jupyter-sshd

Run sshd under Jupyter.

Primarily for use with remote JupyterHubs, so users can access them via `ssh`. Enables everything
one would normally do with `ssh` - copy files, run interactive commands, use the proprietary
VSCode [Remote Development](https://code.visualstudio.com/docs/remote/ssh) functionality, etc!

## Usage

For this document, we will assume you are running inside a containerized JupyterHub enviornment
(such as kubernetes or docker). `jupyter-sshd` itself does not require containerizatio - this is
simply to make instructions easier.

### Server pre-requisities

The following packages must be present in the container environment:

- [openssh](https://www.openssh.com/). You can install this from `conda-forge` or from `apt`
  as you desire.
- `jupyter-sshd` itself must be pre-installed in the container - you *can not* dynamically
  install it with `!pip` after you start the container.

### Client pre-requisites

[websocat](https://github.com/vi/websocat) must be installed on the client machine.
`brew install websocat` works on Mac OS, and pre-built binaries [are available](https://github.com/vi/websocat/releases)
for all other operating systems.

### Create a JupyterHub Token

We will need to create a JupyterHub token for authentication.

1. Go to the JupyterHub control panel. You can access it via `File -> Hub control panel` in
   JupyterLab, or directly going to `https://<your-hub-url>/hub/home`.

2. In the top bar, select **Token**.

3. Create a new Token, and keep it safe. **Treat this like you would treat a password to your
   JupyterHub instance**! It is recommended you set an expiry date for this.

### Start your server

`jupyter-sshd` only works after you start your JupyterHub server. So, start your server!

### Setup your `~/.ssh/config`

We will set up our ssh config file to tell `ssh` how to connect to our JupyterHub. Add
an entry that looks like this to the end of your `~/.ssh/config` file (create it if it
does not exist).

```
Host <YOUR-JUPYTERHUB-DOMAIN>
    ProxyCommand=websocat --binary -H='Authorization: token <YOUR-JUPYTERHUB-TOKEN>' asyncstdio: wss://%h/user/<YOUR-JUPYTERHUB-USERNAME>/sshd/
```

replace:

 - `<YOUR-JUPYTERHUB-DOMAIN>` with your hub domain (for example, `hub.openveda.cloud`)
 - `<YOUR-JUPYTERHUB-TOKEN>` with the token you generated earlier
 - `<YOUR-JUPYTERHUB-USERNAME>` with your jupyterhub username

Here's an example:

```
Host hub.openveda.cloud
    ProxyCommand=websocat --binary -H='Authorization: token a56ff59c93f64fb587f46b06af9422ee' asyncstdio: wss://%h/user/yuvipanda/sshd/
```

We're almost there!

### Setup ssh keys on your JupyterHub

There are still two levels of authentication - your JupyterHub token, as well as some ssh keys. You need to put some ssh public keys
in `~/.ssh/authorized_keys` after you start your JupyterHub server, and have the private keys available in your ssh client machine.

The simplest way to do this is to rely on your GitHub public keys!

1. After you start your JupyterHub server, open a terminal in JupyterLab
2. Run the following commands:

   ```bash
   mkdir -p ~/.ssh
   curl -L https://github.com/<YOUR-GITHUB-USERNAME>.keys > ~/.ssh/authorized_keys
   chmod 0600 ~/.ssh/authorized_keys
   ```

   replacing `<YOUR-GITHUB-USERNAME>` with your github username.

With that, we are ready to go!

### `ssh` into your JupyterHub!

After all this is setup, you're now able to ssh in! Try:

```
ssh <YOUR-JUPYTERHUB-DOMAIN>
```

and it should just work! You can also use this with the proprietary Visual Studio code Remote SSH feature,
use `sftp` to copy files over (although it will be slow), create tunnels, etc!