WSL（Windows Subsystem for Linux）上で、オフラインPCに「curl」「wget」「Ubuntuの最低限必要なライブラリ・ツール」をインストールするためには、オンライン環境のPCで必要なパッケージ（debファイル）をダウンロードし、それらをUSB等でオフラインPCに持ち込んでインストールします。

以下の手順が一般的です。

---

## 1. インストールしたいパッケージのリスト（最小構成例）

- curl
- wget
- ca-certificates
- openssl
- tar
- gzip
- bzip2
- xz-utils
- less
- nano（必要に応じて）
- build-essential（開発系が必要なら）

---

## 2. オンラインPCで必要なパッケージをダウンロード

### (A) 必要なパッケージの依存関係も含めて一括ダウンロード

1. オンラインPCで同じUbuntuバージョンを用意（例：Ubuntu 22.04）。
2. `apt`リポジトリを最新化。
   ```sh
   sudo apt update
   ```
3. 必要なパッケージをダウンロードするディレクトリを作成。
   ```sh
   mkdir ~/offline_packages
   cd ~/offline_packages
   ```
4. 必要なパッケージ（例：curl, wget）のdebファイルと依存関係を一括ダウンロード。
   ```sh
   sudo apt-get install --download-only curl wget ca-certificates openssl tar gzip bzip2 xz-utils less nano
   ```
   これで `/var/cache/apt/archives/` にdebファイルがたまります。

5. debファイルをまとめてコピー
   ```sh
   cp /var/cache/apt/archives/*.deb ~/offline_packages/
   ```

---

### (B) 依存関係も自動で取得したい場合

`aptitude`や`apt-rdepends`を使う方法もありますが、最も手軽なのは `apt` の `--download-only` を使う方法です。  
または、以下のようなスクリプトでまとめて取得もできます：

```sh
sudo apt-get install --download-only curl wget ca-certificates openssl tar gzip bzip2 xz-utils less nano
cp /var/cache/apt/archives/*.deb ~/offline_packages/
```

---

## 3. オフラインPCにコピーしてインストール

1. ダウンロードしたdebファイル（`~/offline_packages/`内）をUSB等でオフラインPCにコピー
2. オフラインPCで以下を実行：
   ```sh
   cd ~/offline_packages
   sudo dpkg -i *.deb
   sudo apt-get install -f   # 依存関係で漏れがあればここで解決
   ```

---

## 4. Ubuntuイメージ自体をオフラインでWSLにインストールしたい場合

- [公式Ubuntuイメージダウンロードページ](https://cloud-images.ubuntu.com/wsl/)から `.appx` や `.tar.gz` をダウンロードし、オフラインPCにコピー。
- WSL上で「インポート」する：
    ```sh
    wsl --import <distro_name> <インストール先パス> <tarファイルパス>
    ```

---

## 5. 注意事項

- オンラインPCとオフラインPCのUbuntuバージョン（例：22.04, 20.04）が一致している必要があります。
- 依存パッケージが多い場合は抜け漏れがないように`apt-get install --download-only`を推奨します。
- 開発系（gccなど）が必要なら`build-essential`も追加してください。

---

**上記の手順で不足や追加したいツールがあれば教えてください。具体的なUbuntuバージョン（例：20.04/22.04など）が分かれば、コマンド例をより詳細に記載できます。**


---


オフラインPCでDocker Engine（および必要な関連パッケージ）をインストールするには、オンラインPCでdebパッケージ一式を取得し、それをUSBなどでオフラインPCに持ち込んでインストールします。  
以下はUbuntu（例：22.04など）環境を想定した手順です。

---

## 1. 必要なDockerパッケージ一覧
最低限インストールすべき主なパッケージ（バージョンによって変わる場合あり）：
- docker-ce
- docker-ce-cli
- containerd.io
- docker-buildx-plugin
- docker-compose-plugin

---

## 2. オンラインPCでパッケージ一式をダウンロード

### (A) Docker公式リポジトリ追加
```sh
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
```

### (B) パッケージと依存関係を一括ダウンロード
```sh
mkdir ~/docker-offline
cd ~/docker-offline
sudo apt-get install --download-only docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
cp /var/cache/apt/archives/*.deb ~/docker-offline/
```

※ `apt-get install --download-only` で依存パッケージも一緒にダウンロードされます。

---

## 3. オフラインPCへファイル移動＆インストール

1. USB等で `~/docker-offline/` フォルダごとオフラインPCにコピー
2. オフラインPCで次を実行
   ```sh
   cd ~/docker-offline
   sudo dpkg -i *.deb
   sudo apt-get install -f   # 依存関係不足があれば解決
   ```

---

## 4. インストール確認
```sh
sudo systemctl status docker
docker --version
```

---

## 5. 注意点
- UbuntuバージョンがオンラインPCとオフラインPCで一致している必要あり
- カーネル要件やcgroup設定など、OS側の要件を事前に確認
- セキュリティ的にGPGキーなどもオフラインで配布したい場合は、`/usr/share/keyrings/docker-archive-keyring.gpg`も一緒にコピー

---

### 参考リンク
- [Docker公式: UbuntuにDocker Engineをインストール（オフライン対応のヒントあり）](https://docs.docker.com/engine/install/ubuntu/)
- [debパッケージの依存解決を手動でやる場合](https://wiki.debian.org/DebianRepository/Offline)

---

より具体的なUbuntuバージョンや他に必要なツールがあればご指定ください。  
**コマンド一式やファイル一覧の自動生成スクリプトも作成可能です。**

---


Docker ComposeをオフラインPCにインストールする方法は2通りあります。

---

## 方法1: 「docker-compose-plugin」パッケージ（推奨）

Docker公式は「docker compose v2」以降は「docker-compose-plugin」として配布しており、  
これはaptのdebパッケージとしてダウンロードできます。  
（Docker Engineのdebパッケージと同じ手順で取得可能）

### オンラインPCでの手順

```sh
# Docker公式リポジトリを追加済み前提
sudo apt update
sudo apt-get install --download-only docker-compose-plugin
cp /var/cache/apt/archives/docker-compose-plugin*.deb .
```

`docker-compose-plugin*.deb`をUSBなどでオフラインPCにコピーし、以下でインストール：

```sh
sudo dpkg -i docker-compose-plugin*.deb
```

**コマンド例:**
```sh
docker compose version
```
（`docker compose` で動作します）

---

## 方法2: バイナリファイルを直接ダウンロードする（v1系またはv2単体バイナリ）

### オンラインPCでの手順

1. [公式GitHubリリースページ](https://github.com/docker/compose/releases)から
   最新版のバイナリ（例: `docker-compose-linux-x86_64` や `docker-compose-linux-aarch64` など）
   をダウンロード。

   例（v2系の場合）:
   ```sh
   curl -L "https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64" -o docker-compose
   chmod +x docker-compose
   ```

2. USB等でオフラインPCへコピーし、PATHの通った場所へ置く：
   ```sh
   sudo mv docker-compose /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. バージョン確認
   ```sh
   docker-compose version
   ```
   または
   ```sh
   docker compose version
   ```

---

## 注意事項

- Docker Compose v2は `docker compose` サブコマンドで利用し、v1は `docker-compose` コマンドです。
- Docker本体（docker-ceなど）が既にインストールされている必要があります。
- オフラインPCのOSアーキテクチャ（x86_64/arm64等）に合ったバイナリを選んでください。

---

### まとめ

- **推奨：aptで「docker-compose-plugin」をダウンロードし、debファイルをオフラインPCでdpkg -iでインストール**
- **または：バイナリを直接ダウンロードしてコピー**

ご希望の方式（debパッケージ or バイナリ）やOS・アーキテクチャの詳細があればさらに具体的な手順をお伝えします。


---


WSL（Windows Subsystem for Linux）で**オフラインPCにgitをインストール**したい場合、  
インターネット接続があるPCでパッケージをダウンロードし、  
オフラインPCへファイルを持ち込んでインストールする方法が一般的です。

---

## 手順

### 1. オンラインPCでgitパッケージをダウンロード

1. **WSL（Ubuntuなど）を起動**
2. 以下コマンドで必要なdebファイルをダウンロード  
   （例：Ubuntu 20.04の場合）

   ```sh
   mkdir ~/git-offline
   cd ~/git-offline
   apt-get download git
   ```

3. **依存パッケージもダウンロード**  
   依存関係があるため、下記コマンドが便利です。

   ```sh
   apt-get install --download-only git
   ```
   これで`/var/cache/apt/archives/`に必要なdebファイルが全てダウンロードされます。

4. **debファイルをまとめてUSBメモリ等にコピー**

   ```sh
   cp /var/cache/apt/archives/*.deb ~/git-offline/
   ```

---

### 2. オフラインPCへファイルをコピー

- USBメモリや外付けHDDなどで`git-offline`フォルダごとコピーします。

---

### 3. オフラインPCでgitをインストール

1. **WSL（Ubuntuなど）で`git-offline`フォルダに移動**
   ```sh
   cd ~/git-offline
   ```

2. **まとめてインストール**
   ```sh
   sudo dpkg -i *.deb
   ```

3. **依存エラーが出た場合**
   ```sh
   sudo apt-get install -f
   ```
   ＊依存ファイルが足りない場合は再度オンラインPCで不足分をダウンロードしてください。

---

## 注意
- オフラインPCのUbuntuバージョンと、オンラインPCのバージョンを必ず揃えてください。
- 必要な依存ファイルも全てコピーすること。

---

### 参考記事
- [Ubuntu公式：パッケージのオフラインインストール](https://wiki.ubuntu.com/AptGet/Offline/JA)

---

ご不明点があれば、具体的なエラーや環境（WSLのバージョンやUbuntuのバージョン）を教えてください！
