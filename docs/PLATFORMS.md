# Platform Setup

This repository is a Python project. Follow the steps below for your platform.

## Termux (native)

```sh
pkg update && pkg upgrade
pkg install python3 git
python -m venv .venv
python -m pip install -U pip
```

## Termux (proot-distro Debian)

Host (Termux):

```sh
pkg install proot-distro git
proot-distro install debian
proot-distro login debian
```

Inside Debian:

```sh
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
python -m pip install -U pip
```

## Debian / Ubuntu

```sh
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
python3 -m venv .venv
python -m pip install -U pip
```

## macOS

```sh
brew install python git
python3 -m venv .venv
python -m pip install -U pip
```

## Windows (PowerShell)

```powershell
winget install -e --id Python.Python.3
winget install -e --id Git.Git
python -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
```
