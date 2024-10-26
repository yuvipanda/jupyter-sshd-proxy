import setuptools
from os import path

HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name="jupyter-sshd-proxy",
    version='0.3.0',
    url="https://github.com/yuvipanda/jupyter-sshd-proxy",
    author="Yuvi Panda",
    description="Run sshd under jupyter",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    classifiers=['Framework :: Jupyter'],
    install_requires=[
        'jupyter-server-proxy>=4.3.0'
    ],
    entry_points={
        'jupyter_serverproxy_servers': [
            'sshd = jupyter_sshd_proxy:setup_sshd',
        ]
    }
)
