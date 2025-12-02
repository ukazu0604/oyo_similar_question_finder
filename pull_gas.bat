@echo off
REM GASから最新コードを取得するバッチファイル

REM gasディレクトリに移動
cd /d "%~dp0\gas"

echo ========================================
echo GASから最新コードを取得中...
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

REM 取得実行
clasp pull
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 取得完了！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 取得に失敗しました。
    echo ========================================
)

echo.
pause
