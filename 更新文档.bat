@echo off
REM ============================================================
REM  packetlens 文档一键更新 —— 双击运行
REM  作用：重新生成三份 Word 文档（学习笔记 + 完全教程 + 逐行手册），
REM        导出 PDF 版，全部放进桌面的「packetlens文档」文件夹。
REM ============================================================
cd /d "%~dp0"

echo ========== 更新文档 ==========
wsl.exe -d Ubuntu -- bash -c "cd /mnt/d/Projects/packetlens && python3 tools/make_doc.py && python3 tools/make_guide.py && python3 tools/make_manual.py"

set DOCDIR=%USERPROFILE%\Desktop\packetlens文档
if not exist "%DOCDIR%" mkdir "%DOCDIR%"

copy /y "docs\packetlens学习笔记.docx" "%DOCDIR%\packetlens学习笔记.docx" >nul
copy /y "docs\packetlens完全教程.docx" "%DOCDIR%\packetlens完全教程.docx" >nul
copy /y "docs\packetlens逐行手册.docx" "%DOCDIR%\packetlens逐行手册.docx" >nul

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\export_pdf.ps1" -SrcDir "docs" -OutDir "%DOCDIR%"
echo.
echo 已更新「packetlens文档」文件夹（3 份 Word + 3 份 PDF）
pause
