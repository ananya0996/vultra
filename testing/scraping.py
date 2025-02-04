import os
import re
import requests
import shutil
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

def download_dependency_file(owner, repo, filename, folder):
    """
    Attempts to download a dependency file (pom.xml, build.gradle, or package.json) 
    from the repository by trying branch 'master' then 'main'. If found, saves it 
    in 'folder' with the naming convention: {repo}-{filename}.
    """
    for branch in ["master", "main"]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
        r = requests.get(raw_url)
        if r.status_code == 200 and r.text.strip():
            file_path = os.path.join(folder, f"{repo}-{filename}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Downloaded {filename} from {owner}/{repo} (branch: {branch})")
            return True
    print(f"Could not find {filename} for {owner}/{repo}")
    return False

def download_java_dependency_files(owner, repo, folder):
    """
    Attempts to download pom.xml and build.gradle for Java projects. If pom.xml is not found,
    attempts to download build.gradle.
    """
    if not download_dependency_file(owner, repo, "pom.xml", folder):
        # If pom.xml is not found, try build.gradle
        download_dependency_file(owner, repo, "build.gradle", folder)

# ===================== Main Script =====================

def main():
    # Scrape links from all three sources
    medium_projects = scrape_medium_top_java_projects()  # returns list of (name, link)
    itnext_projects = scrape_itnext_top_js_projects()      # returns list of (name, link)
    github_md_links = scrape_github_markdown_js()           # returns list of links

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

    for link in all_links:
        print(link)
    
    print("Total unique GitHub project links found:", len(all_links))
    
    # Create a fresh folder named 'dep-files'
    folder_name = "dep-files"
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name, exist_ok=True)
    
    # For each repository, attempt to download pom.xml, build.gradle (for Java), and package.json
    for link in all_links:
        owner, repo = parse_github_url(link)
        if not owner or not repo:
            print(f"Could not parse URL: {link}")
            continue
        
        # Attempt to download Java project files (pom.xml and build.gradle)
        download_java_dependency_files(owner, repo, folder_name)
        
        # Attempt to download package.json (Node.js file)
        download_dependency_file(owner, repo, "package.json", folder_name)
    
    print("Download complete. Check the 'dep-files' folder for results.")

if __name__ == "__main__":
    main()
