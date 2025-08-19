UbuntuにDockerをインストールする手順は以下の通りです。Docker公式リポジトリから最新版のDockerをインストールする方法をおすすめします。

### 1. 既存の古いDockerを削除（インストールされている場合のみ）
```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

### 2. パッケージ情報を更新
```bash
sudo apt-get update
```

### 3. 依存パッケージのインストール
```bash
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

### 4. Docker公式GPGキーの追加
```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 5. Dockerリポジトリの追加
```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 6. パッケージ情報を再度更新
```bash
sudo apt-get update
```

### 7. Dockerエンジン、CLI、コンテナランタイムのインストール
```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 8. Dockerの動作確認
```bash
sudo docker run hello-world
```

---

**補足：**
- `sudo`なしでdockerコマンドを実行したい場合は、`sudo usermod -aG docker $USER` を実行後、一度ログアウトして再ログインしてください。
- 詳細は[公式ドキュメント](https://docs.docker.com/engine/install/ubuntu/)も参照できます。

ご不明点があればご質問ください。