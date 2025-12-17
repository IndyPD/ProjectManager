import requests
import sys
import os
from urllib.parse import urlparse

# --- GitHub 설정 ---
DEFAULT_BRANCH = "readme"

def parse_github_url(url):
    """
    GitHub URL에서 소유자(owner)와 저장소 이름(repo name)을 추출합니다.
    URL 형식: https://github.com/owner/repo(.git)
    """
    try:
        if url.endswith('.git'):
            url = url[:-4] # .git 제거
        
        # URL 객체를 사용하여 경로 부분을 추출
        path = urlparse(url).path.strip('/')
        
        parts = path.split('/')
        
        if len(parts) >= 2:
            owner = parts[0]
            repo_name = parts[1]
            return owner, repo_name
        else:
            return None, None
            
    except Exception as e:
        print(f"Error during URL parsing: {e}")
        return None, None

def read_address_file(file_name="addr.txt"):
    """
    addr.txt 파일에서 GitHub 주소를 읽어와 파싱합니다.
    """
    print(f"Reading address from: {file_name}")
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            github_url = f.readline().strip()
            if not github_url:
                print("Error: The address file is empty.")
                sys.exit(1)
            
            owner, repo_name = parse_github_url(github_url)
            
            if not owner or not repo_name:
                print(f"Error: Could not parse owner/repo from URL: {github_url}")
                sys.exit(1)
                
            return owner, repo_name, github_url

    except FileNotFoundError:
        print(f"Error: '{file_name}' not found. Please create this file and add the GitHub URL.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_name}': {e}")
        sys.exit(1)


def read_github_file(owner, repo_name, file_path, branch=DEFAULT_BRANCH):
    """
    GitHub Raw Content URL을 사용하여 파일 내용을 가져와 출력합니다.
    """
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{file_path}"
    
    print(f"\n--- Reading Raw File: {file_path} from branch: {branch} ---")
    print(f"URL: {raw_url}")
    print("-" * 50)

    try:
        # requests 라이브러리를 사용하여 파일 내용 가져오기
        response = requests.get(raw_url)
        
        # HTTP 오류(4xx 또는 5xx)가 발생하면 예외 발생
        response.raise_for_status()

        # 파일 내용을 콘솔에 출력
        print(response.text)

    except requests.exceptions.HTTPError as errh:
        # 404 (Not Found) 오류 등
        print(f"Error: HTTP 오류 발생 ({errh})")
        print(f"Warning: '{file_path}' 파일이 저장소 '{repo_name}'의 '{branch}' 브랜치에 존재하지 않을 수 있습니다.")
    except requests.exceptions.RequestException as e:
        print(f"Error: 알 수 없는 요청 오류 발생 ({e})")
    
    print("-" * 50)
    print(f"'{file_path}' 파일 읽기 시도 완료.")


if __name__ == "__main__":
    # requests 모듈 확인
    try:
        import requests
    except ImportError:
        print("Error: 'requests' module not found. Please run 'pip install requests'")
        sys.exit(1)
        
    print("--- GitHub Address Reader Start ---")

    # 1. addr.txt 파일에서 주소 읽기 및 파싱
    owner, repo_name, full_url = read_address_file("addr.txt")
    print(f"Successfully connected to: {full_url}")
    print(f"Owner: {owner}, Repository: {repo_name}, Branch: {DEFAULT_BRANCH}")

    # 2. HISTORY.md 파일 읽고 출력
    read_github_file(owner, repo_name, "HISTROY.md")

    # 3. TODO.md 파일 읽고 출력
    read_github_file(owner, repo_name, "TODO.md")
    
    print("\n--- All file operations completed. ---")