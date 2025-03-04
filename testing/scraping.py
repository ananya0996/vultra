import os
import re
import requests
import shutil
import zipfile
import io
from bs4 import BeautifulSoup

# ===================== Scraping Functions =====================

def scrape_medium_top_java_projects():
    """
    Scrapes the Medium article "50 Top Java Projects on GitHub".
    """
    url = "https://medium.com/issuehunt/50-top-java-projects-on-github-adbfe9f67dbc"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36")
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code} for Medium page.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find("article")
    if not content:
        content = soup

    projects = []
    for a in content.find_all("a", href=True):
        href = a['href']
        if "github.com" in href and "/search" not in href:
            project_name = a.get_text(strip=True)
            if project_name and (project_name, href) not in projects:
                projects.append((project_name, href))
    return projects

def scrape_itnext_top_js_projects():
    """
    Scrapes the ITNEXT article for top JavaScript projects.
    """
    url = "https://itnext.io/top-33-javascript-projects-on-github-november-2021-d1e2971dfba5"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36")
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code} for ITNEXT page.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find("article")
    if not content:
        content = soup

    projects = []
    for a in content.find_all("a", href=True):
        href = a['href']
        if "github.com" in href and "/search" not in href:
            project_name = a.get_text(strip=True)
            if project_name and (project_name, href) not in projects:
                projects.append((project_name, href))
    return projects

def scrape_github_markdown_js():
    """
    Scrapes the GitHub markdown file (JavaScript.md) containing the top 100 JavaScript
    projects from the repository and returns a list of unique GitHub project links.
    """
    url = "https://github.com/EvanLi/Github-Ranking/blob/master/Top100/JavaScript.md"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36")
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve GitHub markdown file. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    project_links = []
    
    if table:
        rows = table.find_all("tr")
        # Skip header row
        for row in rows[1:]:
            a_tag = row.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                if href.startswith("https://github.com") and "/search" not in href:
                    project_links.append(href)
    else:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("https://github.com") and not href.endswith(".md") and "/search" not in href:
                project_links.append(href)
    
    unique_links = list(dict.fromkeys(project_links))
    return unique_links

# ===================== Utility Functions =====================

def parse_github_url(url):
    """
    Extracts the owner and repository name from a GitHub URL.
    """
    url = url.split("#")[0].strip()  # Remove fragment identifiers
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if match:
        owner, repo = match.groups()
        repo = repo.replace(".git", "")
        return owner, repo
    return None, None

def download_maven_project(owner, repo, project_folder):
    """
    Checks if the repository contains a pom.xml (indicating a Maven project) and if so,
    downloads the entire repository as a ZIP file, extracting it into project_folder.
    """
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/pom.xml"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            print(f"Detected Maven project for {owner}/{repo} on branch {branch}")
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
            r_zip = requests.get(zip_url)
            if r_zip.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r_zip.content)) as z:
                    z.extractall(project_folder)
                print(f"Downloaded full Maven project for {owner}/{repo} from branch {branch}")
                return True
            else:
                print(f"Failed to download ZIP for {owner}/{repo} from branch {branch}")
    return False

def download_js_project(owner, repo, project_folder):
    """
    Attempts to download a dependency JSON file for a JavaScript project.
    First, it tries to download 'package.json'. If that fails, it scrapes the repository's
    file list for any JSON file (ignoring package-lock.json) and downloads it as package.json.
    """
    # Try direct download of package.json
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/package.json"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            file_path = os.path.join(project_folder, "package.json")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Downloaded package.json from {owner}/{repo} (branch: {branch})")
            return True

    # If not found, scrape the repository page for any JSON file (excluding package-lock.json)
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

# ===================== Main Script =====================

def main():
    # Scrape links from all three sources
    medium_projects = scrape_medium_top_java_projects()  # list of (name, link)
    itnext_projects = scrape_itnext_top_js_projects()      # list of (name, link)
    github_md_links = scrape_github_markdown_js()           # list of links

    # Combine all links (only use the URL part) and remove duplicates
    all_links = []
    for _, link in medium_projects:
        if link not in all_links:
            all_links.append(link)
    for _, link in itnext_projects:
        if link not in all_links:
            all_links.append(link)
    for link in github_md_links:
        if link not in all_links:
            all_links.append(link)

    print("Total unique GitHub project links found:", len(all_links))
    
    # Create a fresh base folder named 'dep-files'
    base_folder = "dep-files"
    if os.path.exists(base_folder):
        shutil.rmtree(base_folder)
    os.makedirs(base_folder, exist_ok=True)
    
    # For each repository, create a project folder and process based on project type
    for link in all_links:
        owner, repo = parse_github_url(link)
        if not owner or not repo:
            print(f"Could not parse URL: {link}")
            continue
        
        # Create a folder for the individual project
        project_folder = os.path.join(base_folder, repo)
        os.makedirs(project_folder, exist_ok=True)
        
        # For Maven projects (detected via pom.xml), download the entire repository
        if download_maven_project(owner, repo, project_folder):
            continue  # Skip further processing if full Maven project downloaded
        
        # For JavaScript projects, download the dependency JSON file and save as package.json
        if download_js_project(owner, repo, project_folder):
            continue
        
        print(f"No dependency file found for {owner}/{repo}")
    
    print("Download complete. Check the 'dep-files' folder for results.")

if __name__ == "__main__":
    main()
