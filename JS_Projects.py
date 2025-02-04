import requests
from bs4 import BeautifulSoup

url = "https://itnext.io/top-33-javascript-projects-on-github-november-2021-d1e2971dfba5"
headers = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/115.0.0.0 Safari/537.36")
}

# Make the GET request
response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Error: Received status code {response.status_code}")
    exit()

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# The article content is likely inside an <article> tag; if not, fallback to the whole document.
content = soup.find("article")
if not content:
    content = soup

projects = []

# Loop through all anchor tags that include 'github.com' in their href attribute.
for a in content.find_all("a", href=True):
    href = a['href']
    # Filter out any non-project links (if necessary, you could add more filtering criteria)
    if "github.com" in href:
        project_name = a.get_text(strip=True)
        # Avoid duplicates and empty strings
        if project_name and (project_name, href) not in projects:
            projects.append((project_name, href))

# Print out the extracted project names and links
for name, link in projects:
    print("-" * 40)
    print(f"Project: {link}")
print("-" * 40)
