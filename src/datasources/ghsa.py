import requests
import os
import re
import semver
import sys
import json

from datasource import BaseDataSource

class GHSAHandler(BaseDataSource):

    url = "https://api.github.com/graphql"
    
    token_env_var = "GITHUB_PAT"

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

        # Conversion for GHSA API
        if ecosystem == "mvn":
            ecosystem = "maven"

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
        result_vulnerabilities = []
        
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
                return []
            
            if "errors" in data:
                print("ERROR: ", data["errors"])
                return []
            
            if "data" not in data or "securityVulnerabilities" not in data["data"]:
                print("ERROR: Unexpected response format:", data)
                return []
            
            for edge in data["data"]["securityVulnerabilities"].get("edges", []):
                node = edge["node"]
                if self.is_version_vulnerable(package_version, node["vulnerableVersionRange"]):
                    # Find CVE identifier
                    cve_id = "Unknown"
                    for identifier in node["advisory"].get("identifiers", []):
                        if identifier.get("type") == "CVE":
                            cve_id = identifier.get("value")
                            break
                    
                    # Format CWEs
                    cwes = []
                    for cwe in node["advisory"].get("cwes", {}).get("edges", []):
                        cwes.append({
                            "cwe_id": cwe["node"].get("cweId", "Unknown"),
                            "cwe_name": cwe["node"].get("name", ""),
                            "description": cwe["node"].get("description", " ")
                        })
                    
                    # Default empty CWE if none found
                    if not cwes:
                        cwes = [{"cwe_id": "Unknown", "cwe_name": "", "description": " "}]
                    
                    result_vulnerabilities.append({
                        "packageName": package_name,
                        "version": package_version,
                        "vuln_status": {
                            "cve_id": cve_id,
                            "cwes": cwes,
                            "firstPatchedVersion": node["firstPatchedVersion"].get("identifier") if node.get("firstPatchedVersion") else "Unknown",
                            "publishedAt": node["advisory"].get("publishedAt", "Unknown")
                        }
                    })
            
            page_info = data["data"]["securityVulnerabilities"].get("pageInfo", {})
            if not page_info.get("hasNextPage", False):
                break
            
            variables["after"] = page_info.get("endCursor")
        
        # Return JSON  output
        return result_vulnerabilities

    def print_json_result(self, vulnerabilities):
        """Print the vulnerabilities in JSON format"""
        print(json.dumps(vulnerabilities, indent=4))

    @staticmethod
    def is_version_vulnerable(version, vulnerable_range):
        """
        Check if a version is within a vulnerable range, handling non-standard version formats.
        
        Args:
            version (str): The version to check (e.g. "2.5.7.SR0")
            vulnerable_range (str): The vulnerable range (e.g. ">=5.2.0, <=5.2.17")
        
        Returns:
            bool: True if the version is vulnerable, False otherwise
        """
        # Split combined ranges into individual conditions
        range_conditions = vulnerable_range.split(',')
        
        # All conditions must be met for a version to be vulnerable
        for condition in range_conditions:
            condition = condition.strip()
            # Extract the operator and version
            match = re.match(r'([<>=]+)\s*([0-9A-Za-z.-]+)', condition)
            if not match:
                continue
                
            operator, range_version = match.groups()
            
            # Perform the comparison
            comparison_result = GHSAHandler.compare_versions(version, range_version)
            
            if operator == "<":
                if comparison_result >= 0:
                    return False
            elif operator == "<=":
                if comparison_result > 0:
                    return False
            elif operator == ">":
                if comparison_result <= 0:
                    return False
            elif operator == ">=":
                if comparison_result < 0:
                    return False
            elif operator == "=":
                if comparison_result != 0:
                    return False
        
        return True

    @staticmethod
    def compare_versions(version1, version2):
        """
        Compare two version strings, handling different release lines.
        
        """
        # Extract numeric parts and suffixes
        v1_parts = re.findall(r'(\d+|[A-Za-z]+)', version1)
        v2_parts = re.findall(r'(\d+|[A-Za-z]+)', version2)
        
        # Compare parts one by one
        for i in range(min(len(v1_parts), len(v2_parts))):
            part1 = v1_parts[i]
            part2 = v2_parts[i]
            
            # If both parts are numeric, compare as integers
            if part1.isdigit() and part2.isdigit():
                num1 = int(part1)
                num2 = int(part2)
                if num1 < num2:
                    return -1
                elif num1 > num2:
                    return 1
            else:
                # For mixed or string comparisons
                # Special handling for common suffixes
                suffix_rank = {
                    "ALPHA": 0,
                    "BETA": 1,
                    "RC": 2,
                    "RELEASE": 3,
                    "SR": 4,
                    "SP": 5,
                    "SEC": 6
                }
                
                # Extract the base word 
                base1 = re.match(r'([A-Za-z]+)(\d*)', part1)
                base2 = re.match(r'([A-Za-z]+)(\d*)', part2)
                
                if base1 and base2:
                    word1, num1 = base1.groups()
                    word2, num2 = base2.groups()
                    
                    # Compare the words first
                    rank1 = suffix_rank.get(word1.upper(), -1)
                    rank2 = suffix_rank.get(word2.upper(), -1)
                    
                    if rank1 != rank2:
                        if rank1 == -1 or rank2 == -1:
                            # If one suffix isn't in our ranking, compare alphabetically
                            if word1.upper() < word2.upper():
                                return -1
                            elif word1.upper() > word2.upper():
                                return 1
                        else:
                            # Use the ranking
                            return -1 if rank1 < rank2 else 1
                    
                    # If words are the same, compare numbers if they exist
                    if num1 and num2:
                        num1_val = int(num1)
                        num2_val = int(num2)
                        if num1_val < num2_val:
                            return -1
                        elif num1_val > num2_val:
                            return 1
                    elif num1: 
                        return 1
                    elif num2:  
                        return -1
                else:
                    # Simple string comparison
                    if part1 < part2:
                        return -1
                    elif part1 > part2:
                        return 1
        
        # If we get here and one version has more parts than the other
        if len(v1_parts) < len(v2_parts):
            return -1
        elif len(v1_parts) > len(v2_parts):
            return 1
        
        # Versions are equal
        return 0

