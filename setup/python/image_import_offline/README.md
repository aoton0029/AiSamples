```sh
# イメージをインポート
docker load -i my-python-app.tar

# コンテナを実行（ボリュームマウントでソース編集可能）
docker run -it --rm -v ${PWD}:/app -p 8000:8000 my-python-app:latest bash

# または直接アプリを実行
docker run -it --rm -v ${PWD}:/app -p 8000:8000 my-python-app:latest python app.py
```



1. イメージからコンテナを起動してソース編集
```sh
# コンテナを起動（インタラクティブモード）
docker run -it --name my-dev-container my-python-app:latest bash

# または、ホストのソースをマウントして編集
docker run -it --name my-dev-container -v ${PWD}:/app my-python-app:latest bash
```
2. 編集済みコンテナを新しいイメージとしてコミット
```sh
# 別ターミナルで（コンテナを起動したまま）
docker commit my-dev-container my-python-app:production

# またはタグを付けて保存
docker commit -m "Production version with source code" -a "Developer" my-dev-container my-python-app:v1.0
```
3. 確定版イメージをエクスポート
```sh
# 作業中のコンテナを停止・削除
docker stop my-dev-container
docker rm my-dev-container

# 確定版イメージをエクスポート
docker save -o my-python-app-production.tar my-python-app:production
```
4. オフラインPCで確定版を実行
```sh
# イメージをインポート
docker load -i my-python-app-production.tar

# 確定版を実行（ソース変更なし）
docker run -p 8000:8000 my-python-app:production python app.py

# バックグラウンドで実行
docker run -d --name production-app -p 8000:8000 my-python-app:production python app.py
```
5. 複数バージョン管理
```sh
# 開発版、テスト版、本番版を管理
docker commit my-dev-container my-python-app:development
docker commit my-test-container my-python-app:testing  
docker commit my-prod-container my-python-app:production

# 各バージョンをエクスポート
docker save -o my-python-app-dev.tar my-python-app:development
docker save -o my-python-app-test.tar my-python-app:testing
docker save -o my-python-app-prod.tar my-python-app:production
```