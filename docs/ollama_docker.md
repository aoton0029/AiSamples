docker run -d --name ollama -p 11434:11434 -v D:\ollama-models:/root/.ollama ollama/ollama


docker save -o ollama_image.tar ollama/ollama

docker exec ollama ollama run llama3.1:8b

docker exec ollama ollama delete

docker network create ollama-net
docker run -d --name ollama --network ollama-net -p 11434:11434 ollama/ollama
docker run -d --name dify --network ollama-net -p 5000:5000 dify/dify



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