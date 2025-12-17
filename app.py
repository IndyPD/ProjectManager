import sys
import os

# [중요] PyInstaller 실행 환경에서 DLL 로드 경로 문제 해결 (최상단에 위치해야 함)
if getattr(sys, 'frozen', False):
    # 실행 파일(app.exe)이 위치한 디렉토리를 PATH 환경변수에 추가하여 DLL을 찾을 수 있게 함
    os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']
    
    # [디버깅] SSL 모듈 로드 테스트 (실행 시 바로 확인 가능하도록 추가)
    try:
        import ssl
        print("✅ SSL 모듈 로드 성공")
    except Exception as e:
        print(f"❌ SSL 모듈 로드 실패: {e}")
        print("❗ 팁: Conda 환경의 Library\\bin 폴더에 있는 '모든 .dll 파일'을 실행 파일(app.exe)이 있는 폴더로 복사해보세요.")

from flask import Flask, render_template, request, jsonify
import json
import requests
from datetime import datetime
import re # 정규표현식 모듈 추가
import threading
import webbrowser
import time
import traceback
# import ssl # 에러 발생 방지를 위해 주석 처리 (위의 PATH 설정으로 requests 내부에서 정상 로드됨)

# Flask 애플리케이션 초기화
if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 경우, 임시 경로(_MEIPASS)에서 템플릿을 찾도록 설정
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    app = Flask(__name__, template_folder=template_folder)
else:
    app = Flask(__name__)

# [설정 추가] 템플릿 자동 리로드 및 브라우저 캐시 방지
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.after_request
def add_header(response):
    """브라우저가 페이지를 캐싱하지 않도록 헤더를 설정하여 변경 사항이 즉시 반영되게 함"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# --- GitHub 기본 설정 ---
# 기본적으로 연결할 저장소 정보
DEFAULT_REPO_OWNER = "IndyPD"
DEFAULT_REPO_NAME = "test_project"
DEFAULT_REPO_URL_FULL = f"https://github.com/{DEFAULT_REPO_OWNER}/{DEFAULT_REPO_NAME}"
# Raw 파일을 가져올 브랜치 이름 (사용자가 임의로 지정한 것으로 보임)
DEFAULT_RAW_BRANCH = "main" # 기본 브랜치를 'main'으로 변경하거나 'readme'로 유지 (여기서는 'main'으로 변경했습니다.)

# --- 히스토리 파일 관리 설정 ---
HISTORY_FILE = 'repo_history.json'

def load_history_data():
    """히스토리 파일에서 목록을 읽어옵니다."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history_data(new_item):
    """새로운 항목을 히스토리에 저장합니다. (중복 제거 및 최신순 정렬)"""
    history = load_history_data()
    
    # 동일한 URL과 Branch를 가진 기존 항목 제거 (최신으로 업데이트하기 위함)
    history = [item for item in history if not (item['url'] == new_item['url'] and item.get('branch') == new_item.get('branch'))]
    
    # 맨 앞에 추가
    history.insert(0, new_item)
    
    # 최대 개수 제한 (예: 20개)
    history = history[:20]
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def delete_history_data(target_url, target_branch):
    """히스토리에서 특정 항목을 삭제합니다."""
    history = load_history_data()
    
    # URL과 Branch가 일치하는 항목 제거
    new_history = [
        item for item in history 
        if not (item['url'] == target_url and item.get('branch') == target_branch)
    ]
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error deleting history: {e}")
        return False

def update_history_data(original_url, original_branch, new_data):
    """히스토리 항목을 수정합니다."""
    history = load_history_data()
    
    # 기존 항목 제거 (URL과 Branch가 일치하는 것)
    history = [
        item for item in history 
        if not (item['url'] == original_url and item.get('branch') == original_branch)
    ]
    
    # 새 데이터 추가 (맨 앞)
    history.insert(0, new_data)
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error updating history: {e}")
        return False

# --- 자동 종료를 위한 Heartbeat 설정 ---
last_heartbeat = time.time()

def monitor_shutdown():
    """마지막 하트비트 수신 후 일정 시간이 지나면 서버를 강제 종료합니다."""
    global last_heartbeat
    while True:
        time.sleep(1)
        # 5초 이상 신호가 없으면 종료 (브라우저 닫힘 간주)
        if time.time() - last_heartbeat > 5:
            print("브라우저 연결이 끊어졌습니다. 서버는 계속 실행됩니다. (종료하려면 창을 닫거나 Ctrl+C)")
            break

@app.route('/heartbeat')
def heartbeat():
    """프론트엔드로부터 생존 신호를 받습니다."""
    global last_heartbeat
    last_heartbeat = time.time()
    return "OK"

@app.route('/api/history')
def get_history_api():
    """프론트엔드에 히스토리 목록을 JSON으로 반환합니다."""
    return jsonify(load_history_data())

@app.route('/api/history/delete', methods=['POST'])
def delete_history_api():
    """프론트엔드 요청에 따라 히스토리 항목을 삭제합니다."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
        
    url = data.get('url')
    branch = data.get('branch')
    
    if delete_history_data(url, branch):
        return jsonify(load_history_data())
    else:
        return jsonify({"error": "Failed to delete"}), 500

@app.route('/api/history/update', methods=['POST'])
def update_history_api():
    """히스토리 항목 수정 API"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
        
    original_url = data.get('original_url')
    original_branch = data.get('original_branch')
    new_item = data.get('new_data')
    
    if update_history_data(original_url, original_branch, new_item):
        return jsonify(load_history_data())
    else:
        return jsonify({"error": "Failed to update"}), 500

def fetch_raw_file_content(owner, name, file_path, branch, token=None):
    """
    GitHub의 raw file 내용을 가져와 반환합니다. (토큰 없이 단순 파일 다운로드)
    """
    raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/{file_path}"
    
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        response = requests.get(raw_url, headers=headers)
        response.raise_for_status()
        return response.text

    except requests.exceptions.HTTPError as errh:
        # 파일이 없을 경우 (404 등)
        error_message = f"--- ERROR (Console): Failed to find {file_path} on branch '{branch}'. (HTTP {errh.response.status_code}) ---"
        print(error_message) # 콘솔 출력 추가
        return f"--- ERROR: {file_path} 파일을 브랜치 '{branch}'에서 찾을 수 없습니다. (HTTP {errh.response.status_code}) ---"
    except requests.exceptions.RequestException as e:
        # API 호출 오류 (네트워크 등)
        error_message = f"--- ERROR (Console): Request error occurred while reading {file_path}. ({e}) ---"
        print(error_message) # 콘솔 출력 추가
        return f"--- ERROR: {file_path} 파일 읽기 요청 오류 발생 ({e}) ---"

def parse_markdown_history(markdown_content, url_full):
    """
    HISTORY.md 내용을 파싱하여 history_data 구조로 변환합니다.
    - 형식: vX.X.X - YYYY-MM-DD (Title)
    - 섹션: 1. 하드웨어 (Hardware), 2. 소프트웨어 (Software) 등
    """
    if markdown_content.startswith('--- ERROR:'):
        # 파일 읽기 오류가 발생한 경우 진단 메시지 반환
        return [{
            "version": "Raw File Error (Diagnostic)",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "title": "Raw HISTORY.md 파일 읽기 실패",
            "sections": {
                "hardware": "API 연동 기반이므로 하드웨어 변경 사항은 없습니다.",
                "software": markdown_content,
                "issues": f"GitHub 저장소 '{url_full}'의 Raw 파일에 오류가 있습니다.",
                "other": "파일 경로, 브랜치 이름을 확인하거나 파일 내용을 확인하세요."
            }
        }]

    history_list = []
    
    # 버전 헤더를 기준으로 전체 내용을 분할합니다.
    # 정규식: (v1.0.0) - (2024-01-01) ((제목)) \n [내용]
    segments = re.split(r'(v\d+\.\d+\.\d+)\s*-\s*(\d{4}-\d{2}-\d{2})\s*\((.*?)\)\s*\n', markdown_content)

    # 섹션 순서를 고정하기 위한 맵
    SECTION_ORDER = ["hardware", "software", "issues", "other"]
    
    # 첫 번째 요소는 분할로 인한 빈 문자열일 수 있으므로 1부터 시작하여 4개씩 건너뜁니다.
    for i in range(1, len(segments), 4):
        if i + 3 >= len(segments):
            break

        version = segments[i].strip()
        date_str = segments[i+1].strip()
        title = segments[i+2].strip()
        content = segments[i+3]
        
        sections_map = {}
        
        # 섹션 패턴: (\d+\.\s*(.*?))\n(.*?)(?=\n\d+\.\s*|$|$)
        # 숫자로 시작하는 섹션 헤더를 찾아 섹션 바디를 추출합니다.
        section_matches = re.findall(r'(\d+\.\s*(.*?))\n(.*?)(?=\n\d+\.\s*|$)', content, re.DOTALL)
        
        for _, section_title_raw, section_body in section_matches:
            section_title_clean = section_title_raw.split('(')[0].strip().lower()
            current_section = 'hardware' if '하드웨어' in section_title_clean else \
                              'software' if '소프트웨어' in section_title_clean else \
                              'issues' if '이슈' in section_title_clean else \
                              'other' if '기타' in section_title_clean else None
            
            if current_section:
                # 섹션 내용을 줄바꿈 기준으로 정리하여 저장
                lines = [line.strip() for line in section_body.split('\n') if line.strip()]
                sections_map[current_section] = ". ".join(lines)


        # 섹션 순서 고정 및 기본값 설정
        sections_data = {}
        for key in SECTION_ORDER:
            content_raw = sections_map.get(key, '')
            # 줄 바꿈을 .으로 대체했으므로, 내용이 없으면 기본값('- 기록 없음') 설정
            if not content_raw:
                sections_data[key] = "- 기록 없음"
            else:
                sections_data[key] = content_raw

        history_list.append({
            "version": version,
            "date": date_str,
            "title": title,
            "sections": sections_data
        })
        
    if not history_list and not markdown_content.startswith('--- ERROR:'):
         # 유효한 기록 형식을 찾지 못했을 경우 진단 메시지 반환
         return [{
            "version": "진단 메시지 (Diagnostic)",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "title": "Raw 파일에서 유효한 기록을 찾을 수 없습니다.",
            "sections": {
                "hardware": "API 연동 기반이므로 하드웨어 변경 사항은 없습니다.",
                "software": "Markdown 파일에 'vX.X.X - YYYY-MM-DD (Title)' 형식이 없습니다.",
                "issues": "히스토리 데이터를 보려면 Markdown 형식을 확인해야 합니다.",
                "other": f"저장소: {url_full}"
            }
        }]

    return history_list

def parse_markdown_todo(markdown_content, url_full):
    """
    TODO.md 내용을 파싱하여 todo_data 구조로 변환합니다.
    - 형식: # [ ] WBS_ID Description
    """
    if markdown_content.startswith('--- ERROR:'):
        # 파일 읽기 오류가 발생한 경우 진단 메시지 반환
        return [{
            "id": "진단",
            "title": "Raw TODO.md 파일 읽기 실패",
            "color": "bg-red-700",
            "subtasks": [{
                "id": "1.1",
                "title": f"오류 메시지: {markdown_content}",
                "tasks": [{"id": "#0", "description": "파일 경로, 브랜치 이름을 확인하거나 파일 내용을 확인하세요.", "status": "unchecked"}]
            }]
        }]

    all_items = []
    lines = markdown_content.split('\n')
    
    # Task 정규식: # [ ] 또는 # [x] 로 시작하는 라인
    # 그룹 1: status (' ' or 'x')
    # 그룹 2: WBS ID (optional, e.g., 1.1.1)
    # 그룹 3: Description
    task_pattern = re.compile(r'^#\s*\[\s*([ x])\]\s*(?:(\d+(?:\.\d+)*)\s+)?(.*)')
    
    last_updated_text = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if "최종 업데이트" in line:
            last_updated_text = line
            continue
            
        match = task_pattern.match(line)
        if match:
            status_char, wbs_id, description = match.groups()
            status = 'checked' if status_char == 'x' else 'unchecked'
            all_items.append({"type": "task", "id": wbs_id if wbs_id else "", "description": description.strip(), "status": status})
        else:
            # 체크박스가 없는 일반 텍스트/헤더
            all_items.append({"type": "text", "content": line})

    # 추출된 Task를 단일 Phase/Subtask 구조로 감싸서 반환합니다.
    if all_items:
        todo_list = [{
            "id": "Project",
            "title": "전체 작업 목록",
            "last_updated": last_updated_text,
            "color": "bg-blue-600",
            "subtasks": [{
                "id": "", # 서브 태스크 ID는 비워둠
                "title": "Task 상세 목록",
                "tasks": all_items
            }]
        }]
    
    else:
        # Task 라인을 찾지 못했을 경우 진단 메시지 반환
        diagnostic_message = "Markdown 파일에서 '# [ ] WBS_ID Description' 형태의 Task 라인을 찾지 못했습니다."
        print(f"--- ERROR (Console): TODO.md 파싱 실패. {diagnostic_message} (저장소: {url_full}) ---")
        todo_list = [{
            "id": "진단",
            "title": "Raw 파일에서 유효한 Task를 찾을 수 없습니다.",
            "color": "bg-gray-500",
            "subtasks": [{"id": "", "title": f"저장소 '{url_full}' 확인 필요",
                         "tasks": [{"id": "#0", "description": diagnostic_message, "status": "unchecked"}]}]
        }]
        
    return todo_list


@app.route('/')
def index():
    """메인 페이지 렌더링 (HTTP 요청 시 1회 실행)"""
    try:
        # 쿼리 파라미터에서 저장소 정보를 가져옵니다.
        owner = request.args.get('owner')
        repo_name = request.args.get('repo')
        project_name = request.args.get('project_name') # 프로젝트명 추가
        # 브랜치 이름을 쿼리 파라미터에서 가져옵니다.
        branch_name = request.args.get('branch') 
        token = request.args.get('token') # 토큰 가져오기

        # 초기 로드 상태 확인 (쿼리 파라미터가 없으면 초기 로드)
        is_initial_load = not owner or not repo_name
        
        # 기본값 설정
        owner = owner if owner else DEFAULT_REPO_OWNER
        repo_name = repo_name if repo_name else DEFAULT_REPO_NAME
        branch_name = branch_name if branch_name else DEFAULT_RAW_BRANCH # 브랜치 이름 기본값 설정
        current_repo_url = f"https://github.com/{owner}/{repo_name}"
        
        # ------------------------------------------------------------------
        
        dynamic_history_data = []
        dynamic_todo_data = []
        raw_history_content = ""
        raw_todo_content = ""

        if not is_initial_load:
            # "GitHub 연결" 버튼이 눌린 후 (쿼리 파라미터가 있을 때) 데이터 로드 및 파싱 실행
            
            # 1. Raw Markdown 파일 내용 가져오기 (branch_name 전달)
            raw_history_content = fetch_raw_file_content(owner, repo_name, "HISTORY.md", branch_name, token) 
            raw_todo_content = fetch_raw_file_content(owner, repo_name, "TODO.md", branch_name, token)

            # 2. Raw Markdown 파일 내용을 파싱하여 UI 구조에 맞게 변환
            dynamic_history_data = parse_markdown_history(raw_history_content, current_repo_url)
            dynamic_todo_data = parse_markdown_todo(raw_todo_content, current_repo_url)
            
            # 프로젝트명이 URL 파라미터로 오지 않았을 경우(외부 링크 등), 기존 히스토리에서 검색 시도
            if not project_name:
                history = load_history_data()
                for item in history:
                    if item['url'] == current_repo_url and item.get('branch') == branch_name:
                        project_name = item.get('project_name', '')
                        break

            # 3. 성공적으로 로드된 경우 히스토리 파일에 저장
            # 에러가 발생하지 않은 경우(적어도 하나의 파일이 정상 로드된 경우)에만 저장
            if not (raw_history_content.startswith("--- ERROR") and raw_todo_content.startswith("--- ERROR")):
                save_history_data({
                    'project_name': project_name if project_name else f"{owner}/{repo_name}", # 프로젝트명 저장
                    'owner': owner,
                    'repo': repo_name,
                    'url': current_repo_url,
                    'branch': branch_name,
                    'token': token, # 편의를 위해 토큰도 저장 (로컬 파일)
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        else:
            # 초기 로드 상태일 경우, UI에 표시될 Raw Content를 비워둡니다.
            raw_history_content = "연결 버튼을 눌러 GitHub 저장소의 Raw 파일을 불러오세요."
            raw_todo_content = "연결 버튼을 눌러 GitHub 저장소의 Raw 파일을 불러오세요."


        # ------------------------------------------------------------------

        # Jinja2 템플릿으로 데이터를 전달합니다. (branch_name 추가)
        return render_template('index.html', 
                            history_data=dynamic_history_data,
                            todo_data=dynamic_todo_data,
                            raw_history_content=raw_history_content,
                            raw_todo_content=raw_todo_content,
                            github_repo_url=current_repo_url,
                            github_raw_branch=branch_name,
                            github_token=token,
                            project_name=project_name)
    except Exception as e:
        # 에러 발생 시 브라우저에 상세 내용을 출력 (디버깅용)
        return f"<h1>500 Internal Server Error</h1><pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    # Flask 앱 실행
    
    # 1. 종료 감지 스레드 시작 (초기 로딩 시간 고려하여 5초 여유 부여)
    last_heartbeat = time.time() + 5
    threading.Thread(target=monitor_shutdown, daemon=True).start()

    # 2. 브라우저 자동 실행 및 서버 시작 (Debug 모드 해제 필수)
    webbrowser.open("http://127.0.0.1:5000")
    try:
        app.run(debug=False)
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}")
    finally:
        input("프로그램을 종료하려면 엔터(Enter) 키를 누르세요...")