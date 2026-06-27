@echo off
cd /d "c:\workspace\vocab-app"
echo ====================================
echo  凌逍科学社团 · 物资管理系统 v2.1
echo  支持多设备数据云端同步 ✨
echo ====================================
echo.
echo 正在启动服务器（含数据同步API）...
echo.
python serve_lab.py
pause
