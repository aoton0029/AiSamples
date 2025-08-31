# イメージをビルド
docker build -t python13.3:dev .

# イメージをtarファイルにエクスポート
docker save -o python13_3.tar python13.3:dev