import requests

def fetch_vulnerabilities(ecosystem, package_name, package_version):
    # GitHub Advisory Database API
    url = "https://api.github.com/graphql"  

    # Insert github fine-grained token below
    headers = {"Authorization": "Bearer <Insert_Token>", "Content-Type": "application/json"}
    vulnerabilities = []
    
    # GraphQL Query to fetch specified metrics
    query = """
    query ($package: String!, $after: String) {
      securityVulnerabilities(ecosystem: %s, package: $package, first: 100, after: $after) {
        edges {
          node {
            advisory {
              identifiers {
                type
                value
              }
              cwes(first: 100) {
                edges {
                  node {
                    cweId
                    name
                    description
                  }
                }
              }
              publishedAt
            }
            vulnerableVersionRange
            severity
            firstPatchedVersion {
              identifier
            }
            updatedAt
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """ % ecosystem.upper()
    
    variables = {"package": package_name, "after": None}
    stored_vulnerabilities = []
    
    while True:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        
        try:
            data = response.json()
        except ValueError:
            print("Invalid JSON response:", response.text)
            return
        
        if "errors" in data:
            print("Error:", data["errors"])
            return
        
        if "data" not in data or "securityVulnerabilities" not in data["data"]:
            print("Unexpected response format:", data)
            return
        
        for edge in data["data"]["securityVulnerabilities"].get("edges", []):
            node = edge["node"]
            if package_version in node["vulnerableVersionRange"]:
                stored_vulnerabilities.append({
                    "cve": node["advisory"].get("identifiers", []),
                    "cweID": [cwe["node"].get("cweId", "N/A") for cwe in node["advisory"].get("cwes", {}).get("edges", [])],
                    "cweName": [cwe["node"].get("name", "N/A") for cwe in node["advisory"].get("cwes", {}).get("edges", [])],
                    "publishedAt": node["advisory"].get("publishedAt", "N/A"),
                    "severity": node.get("severity", "N/A"),
                    "firstPatchedVersion": node["firstPatchedVersion"].get("identifier") if node.get("firstPatchedVersion") else None
                })
        
        page_info = data["data"]["securityVulnerabilities"].get("pageInfo", {})
        if not page_info.get("hasNextPage", False):
            break
        
        variables["after"] = page_info.get("endCursor")
    
    print(stored_vulnerabilities)

def fetch_npm_vulnerabilities(package_name, package_version):
    fetch_vulnerabilities("NPM", package_name, package_version)

def fetch_maven_vulnerabilities(package_name, package_version):
    fetch_vulnerabilities("MAVEN", package_name, package_version)

# Test Casee
fetch_npm_vulnerabilities("lodash", "4.17.20")
fetch_maven_vulnerabilities("org.springframework:spring-core", "2.5.6")

