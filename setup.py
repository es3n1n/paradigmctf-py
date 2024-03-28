from setuptools import find_packages, setup


setup(
    name='paradigmctf.py',
    version='1.0.0',
    description='Packages used for Paradigm CTF',
    packages=find_packages(),
    python_requires='>=3.7, <4',
    install_requires=[
        'web3==6.11.3',
        'kubernetes==28.1.0',
        'redis==5.0.1',
        'fastapi==0.110.0',
        'docker==6.1.3',
        'pwntools==4.11.0',
        'filelock==3.13.3',
    ],
    py_modules=['foundry', 'ctf_server', 'ctf_launchers', 'ctf_solvers'],
)
