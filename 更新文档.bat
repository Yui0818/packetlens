@echo off
REM ============================================================
REM  pcaptool 学习文档一键更新 —— 双击运行
REM  作用：重新生成《pcaptool学习笔记.docx》，
REM        并复制一份到桌面（随时打开就能看）。
REM ============================================================
cd /d "%~dp0"

echo ========== 更新学习文档 ==========
wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/Projects/pcaptool && python3 tools/make_doc.py"

copy /y "docs\pcaptool学习笔记.docx" "%USERPROFILE%\Desktop\pcaptool学习笔记.docx" >nul
echo.
echo 已更新：docs\pcaptool学习笔记.docx（并复制到桌面）
pause
