@echo off
setlocal
chcp 65001
REM ユーザーにディストリビューション名を入力させる
set /p DISTRO_NAME=Ubuntuディストリビューション名を入力してください:

REM Ubuntuを指定名でインストール
@REM wsl --install -d Ubuntu --name %DISTRO_NAME% --no-launch
wsl --import Ubuntu D:\WSL\Ubuntu D:\WSL\UbuntuBase.tar

REM setup.shを実行（setup.shはホームディレクトリに配置しておくこと）
wsl -d %DISTRO_NAME% bash ./ubuntu_setup.sh

REM setup.sh終了後、ディストリビューションをエクスポート
set EXPORT_PATH=%CD%\%DISTRO_NAME%.tar
echo ディストリビューションをエクスポート中: %EXPORT_PATH%
wsl --export %DISTRO_NAME% "%EXPORT_PATH%"

echo エクスポートが完了しました: %EXPORT_PATH%
pause

endlocal