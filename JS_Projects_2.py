import requests
from bs4 import BeautifulSoup

# URL of the GitHub markdown file (rendered view)
url = "https://github.com/EvanLi/Github-Ranking/blob/master/Top100/JavaScript.md"

# Set a user-agent header to mimic a browser
headers = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/115.0.0.0 Safari/537.36")
}

response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Failed to retrieve page. Status code: {response.status_code}")
    exit()

# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")

# Try to find the table that contains the ranking
table = soup.find("table")
project_links = []

if table:
    rows = table.find_all("tr")
    # Skip the header row (usually the first row)
    for row in rows[1:]:
        # Find the first <a> tag with an href attribute
        a_tag = row.find("a", href=True)
        if a_tag:
            href = a_tag["href"]
            # Ensure the link is a full GitHub URL
            if href.startswith("https://github.com"):
                project_links.append(href)
else:
    # Fallback: find all <a> tags in the markdown body that look like GitHub project links
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("https://github.com") and not href.endswith(".md"):
            project_links.append(href)

# Remove duplicates (if any) and print the links
unique_links = list(dict.fromkeys(project_links))
for link in unique_links:
    print(link)
