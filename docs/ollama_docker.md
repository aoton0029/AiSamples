docker run -d --name ollama -p 11434:11434 -v D:\ollama-models:/root/.ollama ollama/ollama


docker save -o ollama_image.tar ollama/ollama

docker exec ollama ollama run llama3.1:8b

docker exec ollama ollama delete

docker network create ollama-net
docker run -d --name ollama --network ollama-net -p 11434:11434 ollama/ollama
docker run -d --name dify --network ollama-net -p 5000:5000 dify/dify


以下の2つのファイルを用意することで、ご希望の動作を実現できます。

---

## 1. Shellスクリプト（例: `create_ollama_model.sh`）

```bash
#!/bin/bash

# 引数チェック
if [ $# -ne 2 ]; then
  echo "Usage: $0 <model_name> <Modelfile_path>"
  exit 1
fi

MODEL_NAME="$1"
MODELFILE_PATH="$2"

# コンテナ名（必要に応じて変更）
CONTAINER_NAME="ollama"

# コマンド実行
docker exec -i "$CONTAINER_NAME" ollama create "$MODEL_NAME" -f "$MODELFILE_PATH"
```

---

## 2. WSL用バッチファイル（例: `run_ollama_create.bat`）

```bat
@echo off
REM 引数1: モデル名, 引数2: Modelfileのパス
wsl ./create_ollama_model.sh %1 %2
```

---

## 使い方

1. `create_ollama_model.sh`に実行権限を付与  
   ```bash
   chmod +x create_ollama_model.sh
   ```

2. Windows側でバッチファイルをダブルクリックするか、  
   コマンドプロンプトで以下のように実行  
   ```
   run_ollama_create.bat モデル名 /path/to/Modelfile
   ```
   例:
   ```
   run_ollama_create.bat mymodel /home/youruser/Modelfile
   ```

---

### 注意点

- `CONTAINER_NAME`はご自身のOllamaコンテナ名に合わせてください。
- Modelfileのパスは**WSL側のパス**（例: `/home/ユーザー名/Modelfile`）で指定します。
- WindowsバッチからWSLを呼び出す形なので、WSLがセットアップされている必要があります。

ご不明点があれば教えてください！


了解しました。  
Modelfileを相対パスで指定できるように、スクリプト側ではそのまま引数として受け渡せばOKです。

### 具体例

#### 1. `create_ollama_model.sh`

```bash
#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: $0 <model_name> <Modelfile_relative_path>"
  exit 1
fi

MODEL_NAME="$1"
MODELFILE_PATH="$2"
CONTAINER_NAME="ollama"

# 相対パスのままdocker execで渡す
docker exec -i "$CONTAINER_NAME" ollama create "$MODEL_NAME" -f "$MODELFILE_PATH"
```

#### 2. `run_ollama_create.bat`

```bat
@echo off
REM 引数1: モデル名, 引数2: Modelfileの相対パス
wsl ./create_ollama_model.sh %1 %2
```

---

### 使い方例

- カレントディレクトリに`Modelfile`がある場合  
  ```
  run_ollama_create.bat mymodel ./Modelfile
  ```
- サブディレクトリの場合  
  ```
  run_ollama_create.bat mymodel ./subdir/Modelfile
  ```

---

#### 注意

- バッチファイルとシェルスクリプトの実行場所（カレントディレクトリ）に応じて、相対パスが解釈されます。
- dockerコンテナ側にも同じパスが存在する必要があります（docker volumeやbind mountでファイルを共有している場合は問題ありません）。

ご不明点があればご質問ください！