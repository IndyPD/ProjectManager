1.0 사전 준비 (Preparation)
1.1 환경 설정
# [x] 1.1.1 PyInstaller 라이브러리 설치 확인 (pip install pyinstaller)
# [x] 1.1.2 가상환경 활성화 및 의존성 패키지 최신화
1.2 프로젝트 점검
# [x] 1.2.1 app.py의 PyInstaller 경로 처리 코드 확인 (sys.frozen)
# [x] 1.2.2 templates 폴더 경로 및 정적 파일 위치 확인
2.0 실행 파일 빌드 (Build)
2.1 빌드 명령어 실행
# [x] 2.1.1 PyInstaller 빌드 명령어 작성 (--onefile, --add-data)
# [x] 2.1.2 터미널에서 빌드 실행
2.2 빌드 후 처리
# [x] 2.2.1 dist 폴더 내 실행 파일(app.exe) 생성 확인
# [x] 2.2.2 spec 파일 확인 및 필요 시 수정
3.0 테스트 및 배포 (Test & Deploy)
3.1 기능 테스트
# [ ] 3.1.1 생성된 exe 파일 실행 및 서버 구동 확인
# [ ] 3.1.2 브라우저 자동 실행 및 페이지 로딩 테스트
3.2 배포 준비
# [ ] 3.2.1 불필요한 빌드 폴더(build, __pycache__) 정리
# [ ] 3.2.2 최종 실행 파일 배포
최종 업데이트: 2025년 12월 17일