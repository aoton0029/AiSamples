UbuntuにDockerをインストールするには、以下の手順を実行します。

### 1. 既存のDockerがあれば削除
```sh
sudo apt-get remove docker docker-engine docker.io containerd runc
```

### 2. 必要なパッケージのインストール
```sh
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### 3. Dockerの公式GPG鍵を追加
```sh
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### 4. Dockerリポジトリを追加
```sh
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 5. Docker Engineのインストール
```sh
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 6. インストール確認
```sh
sudo docker run hello-world
```

これでDockerがUbuntuにインストールされます。  
もし非rootユーザーでdockerコマンドを使いたい場合、以下も実行してください：

```sh
sudo usermod -aG docker $USER
```
その後、ログアウト＆ログインしてください。

ご質問があればどうぞ！