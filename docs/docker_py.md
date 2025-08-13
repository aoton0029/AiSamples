DockerでPythonのイメージを使い、必要なライブラリをインストールしてパッケージ化（パック）する手順を説明します。

### 1. `Dockerfile` の作成

まず、作業ディレクトリに `Dockerfile` を作成します。  
例：Python 3.10と `requests` ライブラリをパックしたい場合

```dockerfile
# ベースイメージ（公式のPythonイメージを使用）
FROM python:3.10

# 必要なPythonライブラリを記述したrequirements.txtをコピー
COPY requirements.txt /app/requirements.txt

# 作業ディレクトリを設定
WORKDIR /app

# ライブラリのインストール
RUN pip install --no-cache-dir -r requirements.txt

# 必要ならアプリケーションコードをコピー
# COPY . /app
```

### 2. `requirements.txt` の作成

インストールしたいPythonライブラリを記載します。

```
requests
numpy
pandas
```

### 3. Dockerイメージのビルド

ターミナルで以下のコマンドを実行します：

```sh
docker build -t my-python-app .
```

### 4. Dockerコンテナの実行

```sh
docker run --rm my-python-app
```

---

#### 補足
- 他に必要なライブラリやバージョンがあれば `requirements.txt` に追記してください。
- Pythonのバージョンは `FROM python:3.x` の部分で変更できます。
- アプリケーションコードもパックしたい場合は `COPY . /app` などで追加できます。

---

**もし具体的なライブラリや用途がある場合、教えてください。サンプルをより詳細に作成します！**