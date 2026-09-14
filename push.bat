@echo off
REM ============================================================
REM  pcaptool 一键备份脚本 —— 双击运行即可
REM  作用：把当前项目所有改动提交(commit)并推送到 GitHub
REM  GitHub 就是最可靠的云端备份，改完代码双击它=完成备份
REM ============================================================
cd /d "%~dp0"

echo ========== pcaptool 备份开始 ==========

REM 1. 检查有没有改动需要提交
git add -A
git status --short

REM 2. 如果没有任何改动，提示并结束
set CHANGED=
for /f "delims=" %%i in ('git status --short') do set CHANGED=1
if not defined CHANGED (
    echo.
    echo "没有待提交的改动，备份结束（代码已在 GitHub 上）。"
    goto :push
)

REM 3. 请输入提交说明（留空则用默认时间戳信息）
set /p MSG="请输入本次提交说明（直接回车用默认）: "
if "%MSG%"=="" (
    set MSG=update %date% %time%
)

REM 4. 用你的身份提交（不含任何 AI 署名）
git -c user.name="Yui0818" -c user.email="324952380+Yui0818@users.noreply.github.com" commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo "提交失败，请检查。"
    pause
    exit /b 1
)

:push
REM 5. 通过本机代理推送到 GitHub（保证能连上）
git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin master
if errorlevel 1 (
    echo.
    echo "推送失败，请检查网络/代理。"
) else (
    echo.
    echo "===== 备份成功！代码已推送 GitHub：https://github.com/Yui0818/pcaptool ====="
)

echo.
pause
