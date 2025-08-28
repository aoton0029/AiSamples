FROM python:3.13-slim

# 作業ディレクトリ作成
WORKDIR /app

# 必要なパッケージインストール
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pandas numpy matplotlib

# アプリケーションファイルをコピー（例: main.py）
COPY ./main.py /app/main.py

# FastAPIを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]