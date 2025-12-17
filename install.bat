@echo off
title 라이브러리 자동 설치
echo 프로젝트에 필요한 라이브러리를 설치합니다...

pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [오류] 설치 중 문제가 발생했습니다. Python이 설치되어 있는지 확인해주세요.
) else (
    echo [성공] 모든 라이브러리가 설치되었습니다.
)
pause