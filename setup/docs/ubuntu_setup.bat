@echo off
setlocal

REM ユーザーにディストリビューション名を入力させる
set /p DISTRO_NAME=Ubuntuディストリビューション名を入力してください:

REM Ubuntuを指定名でインストール
wsl --install -d Ubuntu --name %DISTRO_NAME%

REM インストール完了まで待機（必要に応じて調整）
echo インストール完了後、Enterキーを押してください...
pause

REM setup.shを実行（setup.shはホームディレクトリに配置しておくこと）
wsl -d %DISTRO_NAME% bash ~/setup.sh

REM setup.sh終了後、ディストリビューションをエクスポート
set EXPORT_PATH=%CD%\%DISTRO_NAME%.tar
echo ディストリビューションをエクスポート中: %EXPORT_PATH%
wsl --export %DISTRO_NAME% "%EXPORT_PATH%"

echo エクスポートが完了しました: %EXPORT_PATH%
pause

endlocal