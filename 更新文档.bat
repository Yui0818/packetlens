@echo off
REM ============================================================
REM  pcaptool 文档一键更新 —— 双击运行
REM  作用：重新生成三份 Word 文档（学习笔记 + 完全教程 + 逐行手册），
REM        并各复制一份到桌面（随时打开就能看）。
REM ============================================================
cd /d "%~dp0"

echo ========== 更新文档 ==========
wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/Projects/pcaptool && python3 tools/make_doc.py && python3 tools/make_guide.py && python3 tools/make_manual.py"

copy /y "docs\pcaptool学习笔记.docx" "%USERPROFILE%\Desktop\pcaptool学习笔记.docx" >nul
copy /y "docs\pcaptool完全教程.docx" "%USERPROFILE%\Desktop\pcaptool完全教程.docx" >nul
copy /y "docs\pcaptool逐行手册.docx" "%USERPROFILE%\Desktop\pcaptool逐行手册.docx" >nul
echo.
echo 已更新 docs\ 下三份文档（并复制到桌面）
pause
