@echo off
title Project Manager Server
echo 프로젝트 관리 서버를 시작합니다...

:: 현재 배치 파일이 있는 폴더로 작업 경로 변경
cd /d "%~dp0"

:: Conda 환경(nrmk)의 Python 실행 파일 경로 지정
:: 이전 로그 경로를 기반으로 설정했습니다.
set PYTHON_EXE=C:\Users\neuromeka\.conda\envs\nrmk\python.exe
:: 시스템에 설치된 기본 Python으로 실행
:: (각 PC의 환경 변수 PATH에 등록된 python을 자동으로 찾습니다)
python app.py

:: Python 스크립트 실행
"%PYTHON_EXE%" app.py

:: 프로그램 종료 또는 에러 발생 시 창이 바로 닫히지 않도록 대기
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 프로그램 실행 중 문제가 발생했습니다.
    pause
) else (
    pause
)