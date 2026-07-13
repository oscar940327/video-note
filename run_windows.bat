@echo off
set /p URL=請貼上 YouTube 或 Bilibili 網址：
.venv\Scripts\python.exe transcribe_video.py "%URL%" --model small
pause
