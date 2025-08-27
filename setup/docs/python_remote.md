aoton0029: GPUを搭載したPCでWSLのPythonコンテナを立てる。そのコンテナに別のPCからvscodeでリモート接続して開発する

Workspace: Collecting workspace informationWSL上のGPU対応Pythonコンテナを立て、別PCからVSCodeでリモート開発する手順例です。

````markdown
# GPU搭載PCでWSLのPythonコンテナを立て、別PCからVSCodeでリモート開発する手順

## 1. GPU搭載PC側の準備

### WSL2 + NVIDIAドライバのセットアップ
- WindowsにWSL2をインストール
- [NVIDIA公式ガイド](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)に従い、WSL2用GPUドライバをインストール

### Docker Desktopのインストール
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)をインストール
- 設定で「WSL2バックエンド」と「GPUサポート」を有効化

### Python用GPUコンテナの起動例
```sh
docker run --gpus all -it --name pydev -v /mnt/c/Users/yourname/work:/workspace -p 2222:22 python:3.10 bash
```
- 必要に応じて`Dockerfile`で`openssh-server`や`code`コマンドを追加

## 2. SSHサーバのセットアップ（コンテナ内）

```sh
apt update && apt install -y openssh-server
service ssh start
passwd  # rootパスワード設定
```
- `/etc/ssh/sshd_config`で`PermitRootLogin yes`などを確認

## 3. VSCodeでリモート接続（別PCから）

### 必要な拡張機能
- [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)

### SSH設定例（`~/.ssh/config`）
```
Host gpu-wsl
  HostName <GPU搭載PCのIP>
  Port 2222
  User root
```

### VSCodeで「Remote-SSH: Connect to Host...」→`gpu-wsl`を選択

## 4. 開発・デバッグ

- VSCodeからコンテナ内のPython環境を利用可能
- CUDAやPyTorch等もGPUで動作

---

## 補足

- Windowsファイアウォールでポート2222を開放
- セキュリティのため公開鍵認証推奨
- Docker Composeや`devcontainer.json`を使うとより便利

````

この手順で、GPU搭載PCのWSLコンテナ上でPython開発を、別PCからVSCodeで快適に行えます。