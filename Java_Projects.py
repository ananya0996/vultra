import requests
from bs4 import BeautifulSoup

url = "https://medium.com/issuehunt/50-top-java-projects-on-github-adbfe9f67dbc"
headers = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/115.0.0.0 Safari/537.36")
}

# Make the GET request
response = requests.get(url, headers=headers)

# Check if we got a valid response
if response.status_code != 200:
    print(f"Error: Received status code {response.status_code}")
    exit()

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# In some cases the article content is contained in an <article> tag
content = soup.find("article")
if not content:
    content = soup

projects = []

# Search for all links that point to GitHub
for a in content.find_all("a", href=True):
    href = a['href']
    if "github.com" in href:
        # Sometimes the text may include extra characters or whitespace
        project_name = a.get_text(strip=True)
        if project_name and (project_name, href) not in projects:
            projects.append((project_name, href))

# Print out the project names and links
for name, link in projects:
    print("-" * 40)
    print(f"Project: {name}")
print("-" * 40)
