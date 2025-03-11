import requests
import os
import re
import semver
import sys

from datasource import BaseDataSource

class GHSAHandler(BaseDataSource):

    url = "https://api.github.com/graphql"
    
    token_env_var = "GITHUB_ACCESS_TOKEN"

    headers = {
        "Authorization": "Bearer ",
        "Content-Type": "application/json"
    }

    def __init__(self):
        access_token = os.getenv(self.token_env_var)
        if not access_token or access_token == "":
            print(f"ERROR: Environment variable {self.token_env_var} not set.")
            sys.exit(1)
        
        self.headers['Authorization'] += access_token

    def handle(self, package_name, package_version, ecosystem):
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
            response = requests.post(self.url,
                                     json = {
                                         "query": query,
                                         "variables": variables
                                         },
                                         headers = self.headers)
            
            try:
                data = response.json()
            except ValueError:
                print("ERROR: Invalid JSON response:", response.text)
                return
            
            if "errors" in data:
                print("ERROR: ", data["errors"])
                return
            
            if "data" not in data or "securityVulnerabilities" not in data["data"]:
                print("ERROR: Unexpected response format:", data)
                return
            
            for edge in data["data"]["securityVulnerabilities"].get("edges", []):
                node = edge["node"]
                if self.is_version_vulnerable(package_version, node["vulnerableVersionRange"]):
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

    def is_version_vulnerable(version, vulnerable_range):
        """
        Check if a version is within a vulnerable range, respecting suffixes.
        
        Args:
            version (str): The version to check (e.g. "2.0.0Alpha")
            vulnerable_range (str): The vulnerable range (e.g. "<2.1.1")
        
        Returns:
            bool: True if the version is vulnerable, False otherwise
        """
        # Parse the vulnerable range
        # Common formats: <2.1.1, >=1.0.0 <2.0.0, etc.
        
        # Extract the version parts and operators
        range_parts = re.findall(r'([<>=]+)\s*([0-9]+(?:\.[0-9]+)*(?:[-+][0-9A-Za-z-.]+)?|[0-9A-Za-z-.]+)', vulnerable_range)
        
        # No valid range parts found
        if not range_parts:
            return False
            
        try:
            # Check if this is a simple comparison (e.g., <2.1.1)
            for operator, range_version in range_parts:
                # Make sure we're comparing versions with the same suffix structure
                version_suffix = extract_suffix(version)
                range_suffix = extract_suffix(range_version)
                
                # If suffixes don't match and we're not dealing with a standard version,
                # then we need special handling
                if version_suffix != range_suffix and (version_suffix or range_suffix):
                    # If range has suffix but version doesn't, or vice versa, 
                    # we need suffix-aware comparison
                    if operator == "<" or operator == "<=":
                        # For "less than" comparisons, we can't compare versions with different suffix types directly
                        # We only consider it vulnerable if the suffixes match or if both are standard versions
                        if version_suffix != range_suffix:
                            continue
                    
                    # For "greater than" comparisons, similar logic applies
                    if operator == ">" or operator == ">=":
                        if version_suffix != range_suffix:
                            continue
                
                # Standard semver comparison for versions with matching or no suffixes
                normalized_version = normalize_version(version)
                normalized_range_version = normalize_version(range_version)
                
                # Use semver's comparison functions
                if operator == "<":
                    if semver.compare(normalized_version, normalized_range_version) >= 0:
                        return False
                elif operator == "<=":
                    if semver.compare(normalized_version, normalized_range_version) > 0:
                        return False
                elif operator == ">":
                    if semver.compare(normalized_version, normalized_range_version) <= 0:
                        return False
                elif operator == ">=":
                    if semver.compare(normalized_version, normalized_range_version) < 0:
                        return False
                elif operator == "=":
                    if semver.compare(normalized_version, normalized_range_version) != 0:
                        return False
            
            # If we've made it through all the checks, the version is vulnerable
            return True
            
        except ValueError:
            # If we can't parse the versions, default to not vulnerable
            print(f"Warning: Could not parse version comparison: {version} vs {vulnerable_range}")
            return False

    def extract_suffix(version):
        """Extract any suffix (alpha, beta, etc.) from a version string."""
        match = re.search(r'[0-9]+(?:\.[0-9]+)*(?:-([0-9A-Za-z-.]+))?', version)
        if match and match.group(1):
            return match.group(1)
        
        # Check for non-standard suffixes (like Alpha, Beta that aren't using semver format)
        match = re.search(r'[0-9]+(?:\.[0-9]+)*([A-Za-z]+)', version)
        if match:
            return match.group(1)
        
        return ""
    
    def normalize_version(version):
        """Convert version to a semver-compatible format."""
        # Extract components
        if not re.match(r'^[0-9]+(\.[0-9]+)*', version):
            # If it doesn't start with numbers, make it a valid semver
            version = "0.0.0-" + version
            return version
        
        # Extract base version and suffix
        base_match = re.match(r'^([0-9]+(?:\.[0-9]+)*)(.*)$', version)
        if not base_match:
            return "0.0.0"
        
        base = base_match.group(1)
        suffix = base_match.group(2)
        
        # Ensure base has at least 3 components (major.minor.patch)
        parts = base.split('.')
        while len(parts) < 3:
            parts.append('0')
        base = '.'.join(parts)
        
        # Convert non-standard suffixes to semver format
        if suffix and not suffix.startswith('-') and not suffix.startswith('+'):
            suffix = '-' + suffix
        
        return base + suffix