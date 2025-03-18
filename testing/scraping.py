import os
import requests
import time
import re
import shutil
import zipfile
import io
from bs4 import BeautifulSoup

ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN", "")
headers = {'Authorization': f'token {ACCESS_TOKEN}'} if ACCESS_TOKEN else {}

def search_repos(query, page=1, per_page=100):
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': query,
        'sort': 'stars',
        'order': 'desc',
        'page': page,
        'per_page': per_page
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error searching repos: {response.status_code}")
        return []
    return response.json().get('items', [])

def repo_has_file_with_extension(repo, extension):
    default_branch = repo.get("default_branch", "main")
    url = f'https://api.github.com/repos/{repo["full_name"]}/contents'
    response = requests.get(url, headers=headers, params={"ref": default_branch})
    if response.status_code != 200:
        return False
    for item in response.json():
        if item['type'] == 'file' and item['name'].endswith(extension):
            return True
    return False

def collect_repos(query, extension, max_repos):
    repos_list = []
    page = 1
    while len(repos_list) < max_repos:
        print(f"Fetching page {page} for query '{query}'")
        repos = search_repos(query, page=page)
        if not repos:
            print("No more repos found.")
            break
        for repo in repos:
            if repo_has_file_with_extension(repo, extension):
                repos_list.append(repo['html_url'])
                print(f"Found repo {len(repos_list)}: {repo['html_url']}")
                if len(repos_list) >= max_repos:
                    break
        page += 1
        time.sleep(1)
    return repos_list

def parse_github_url(url):
    """
    Extracts the owner and repository name from a GitHub URL.
    """
    url = url.split("#")[0].strip()
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if match:
        owner, repo = match.groups()
        repo = repo.replace(".git", "")
        return owner, repo
    return None, None

def download_maven_project(owner, repo, project_folder):
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/pom.xml"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            print(f"Detected Maven project for {owner}/{repo} (branch: {branch})")
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            r_zip = requests.get(zip_url)
            if r_zip.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r_zip.content)) as z:
                    z.extractall(project_folder)
                print(f"Downloaded full Maven project for {owner}/{repo} (branch: {branch})")
                return True
            else:
                print(f"Failed to download ZIP for {owner}/{repo} (branch: {branch})")
    return False

def download_js_project(owner, repo, project_folder):
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/package.json"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            file_path = os.path.join(project_folder, "package.json")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Downloaded package.json from {owner}/{repo} (branch: {branch})")
            return True
            
    for branch in ["master", "main"]:
        tree_url = f"https://github.com/{owner}/{repo}/tree/{branch}"
        r_page = requests.get(tree_url)
        if r_page.status_code == 200:
            soup = BeautifulSoup(r_page.text, "html.parser")
            links = soup.find_all("a", href=True)
            for a in links:
                href = a['href']
                if f"/{branch}/" in href and href.endswith(".json"):
                    filename = href.split("/")[-1]
                    if filename.lower() == "package-lock.json":
                        continue
                    raw_url_candidate = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
                    r_candidate = requests.get(raw_url_candidate)
                    if r_candidate.status_code == 200 and r_candidate.text.strip():
                        file_path = os.path.join(project_folder, "package.json")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(r_candidate.text)
                        print(f"Downloaded {filename} as package.json from {owner}/{repo} (branch: {branch})")
                        return True
    return False

def main():
    print("Collecting top 50 npm projects with a .json file...")
    js_repos = collect_repos('topic:JavaScript language:JavaScript', '.json', 50)
    print("\nCollecting top 50 maven projects with a .xml file...")
    java_repos = collect_repos('topic:Java language:Java', '.xml', 50)

    all_links = list(set(js_repos + java_repos))
    print(f"\nTotal unique GitHub project links collected: {len(all_links)}")

    base_folder = "testing/dep-files"
    if os.path.exists(base_folder):
        shutil.rmtree(base_folder)
    os.makedirs(base_folder, exist_ok=True)

    for link in all_links:
        owner, repo = parse_github_url(link)
        if not owner or not repo:
            print(f"Could not parse URL: {link}")
            continue
        
        project_folder = os.path.join(base_folder, repo)
        os.makedirs(project_folder, exist_ok=True)
        
        if download_maven_project(owner, repo, project_folder):
            continue
        
        if download_js_project(owner, repo, project_folder):
            continue
        
        print(f"No dependency file found for {owner}/{repo}")
    
    print("\nDownload complete. Check the 'dep-folder' folder for results.")

if __name__ == "__main__":
    main()
