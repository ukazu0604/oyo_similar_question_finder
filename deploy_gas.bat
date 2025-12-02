@echo off
REM GASにデプロイするバッチファイル

REM gasディレクトリに移動
cd /d "%~dp0\gas"

echo ========================================
echo GASにデプロイ中...
echo ========================================
echo.

REM claspがインストールされているか確認
where clasp >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: claspがインストールされていません。
    echo 以下のコマンドでインストールしてください:
    echo   npm install -g @google/clasp
    echo.
    pause
    exit /b 1
)

REM .clasp.jsonが設定されているか確認
findstr /C:"<YOUR_SCRIPT_ID>" .clasp.json >nul 2>&1
if %errorlevel% equ 0 (
    echo エラー: .clasp.jsonにスクリプトIDが設定されていません。
    echo.
    echo 以下の手順で設定してください:
    echo 1. GASエディタを開く
    echo 2. プロジェクトの設定 → スクリプトID をコピー
    echo 3. gas\.clasp.json を開く
    echo 4. ^<YOUR_SCRIPT_ID^> を実際のスクリプトIDに置き換え
    echo.
    pause
    exit /b 1
)

REM デプロイ実行
clasp push
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo デプロイ完了！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo デプロイに失敗しました。
    echo ========================================
    echo.
    echo ログインしていない場合は、以下のコマンドを実行してください:
    echo   clasp login
)

echo.
pause
