@echo off
chcp 65001 >nul
echo 正在迁移数据到 OneDrive...

set SRC=%USERPROFILE%\Documents\lifeplanner_data.json
set DST=%OneDrive%\lifeplanner_data.json

if not exist "%SRC%" (
    echo 未找到旧数据文件：%SRC%
    pause
    exit /b 1
)

if exist "%DST%" (
    echo 目标已存在，备份为 lifeplanner_data_backup.json
    copy /y "%DST%" "%OneDrive%\lifeplanner_data_backup.json"
)

copy /y "%SRC%" "%DST%"
echo 迁移完成！数据已保存到：%DST%
pause
