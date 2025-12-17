# 프로젝트 관리 뷰어 (Project Manager)

이 프로젝트는 GitHub 저장소에 있는 `HISTORY.md`와 `TODO.md` 파일을 실시간으로 읽어와, 프로젝트의 개발 기록과 할 일 목록을 시각적으로 보여주는 Flask 기반 웹 애플리케이션입니다.

## 📋 주요 기능

- **GitHub 연동**: Public 및 Private 저장소(Token 사용) 지원
- **History 뷰**: 날짜별 개발 기록 및 변경 사항을 타임라인 형태로 확인
- **To-Do 뷰**: WBS 기반의 할 일 목록 및 진행률 확인
- **Raw 파일 뷰**: 원본 Markdown 파일 내용 확인
- **자동 실행**: 실행 시 브라우저 자동 실행 및 종료 시 서버 자동 종료

## 🛠 설치 방법

이 프로젝트를 실행하기 위해서는 Python이 설치되어 있어야 합니다.

### 1. 라이브러리 설치
동봉된 `install.bat` 파일을 실행하거나, 아래 명령어를 터미널에 입력하여 필요한 라이브러리를 설치하세요.

```bash
pip install -r requirements.txt
```

## 🚀 실행 방법

### 방법 1: 배치 파일 실행 (권장)
`run.bat` 파일을 더블 클릭하면 서버가 시작되고 웹 브라우저가 자동으로 열립니다.

### 방법 2: 직접 실행
터미널에서 아래 명령어를 입력하세요.

```bash
python app.py
```

## 📦 실행 파일 빌드 (선택 사항)

PyInstaller를 사용하여 단일 실행 파일(.exe)로 배포할 수 있습니다.

```bash
pyinstaller --clean --onefile --add-data "templates;templates" app.py
```