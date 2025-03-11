from datasource import BaseDataSource
import subprocess
import requests
import re
import json
from packaging.version import Version, parse


class NVDHandler(BaseDataSource):
    package_manager=["mvn","npm"]
    def handle(self, lib_version, package,package_manager):
        if self.is_rc_version(lib_version):

            return self.direct_update_for_rc_version(package,lib_version,package_manager,"")
        else:
            return self.get_cpe_number_and_check_vulnerability(package, lib_version)


    def is_rc_version(self, lib_version):
        """Detect pre-release versions (rc, beta, SNAPSHOT, etc.)"""
        return bool(re.search(
            r"(rc|beta|alpha|preview|snapshot|nightly|m\d+|SNAPSHOT)",
            lib_version,
            re.IGNORECASE
        ))



    # --- Fetch Latest Stable Version (npm + Maven) ---
    def direct_update_for_rc_version(self,package_name, package_version, package_manager, groupId):
        """Fetch latest stable version for npm or Maven packages"""
        if self.is_rc_version(package_version):
            try:
                if package_manager == "npm":
                    # NPM logic (unchanged)
                    result = subprocess.run(
                        [r"C:\Program Files\nodejs\npm.cmd", "show", package_name, "versions", "--json"],
                        capture_output=True, text=True, check=True
                    )
                    versions = json.loads(result.stdout)
                    stable_versions = [v for v in versions if not self.is_rc_version(v)]
                    latest_stable = stable_versions[-1] if stable_versions else None
                    return f"Update to {latest_stable}" if latest_stable else "No stable version found."

                elif package_manager == "maven":
                    groupId = groupId
                    artifactId = package_name
                    url = f"https://search.maven.org/solrsearch/select?q={groupId}+AND+a:{artifactId}&rows=10&wt=json"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json();
                        if data["response"]["numFound"] > 0:
                            latest_version = [doc["latestVersion"] for doc in data["response"]["docs"]]
                            return f"Update to {latest_version}" if latest_version else "No stable version found."




                else:
                    return f"Unsupported package manager: {package_manager}"

            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return f"{package_name} ({package_version}) is stable."

    def get_valid_group_id(self,artifact_id):
        """Fetch valid group IDs for a given artifact."""
        url = f"https://search.maven.org/solrsearch/select?q=a:{artifact_id}&rows=10&wt=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            group_ids = {doc["g"] for doc in data["response"]["docs"]}
            return list(group_ids)
        return None

    # Function to get the CPE number of a vulnerable package and check the base score
    def get_cpe_number_and_check_vulnerability(self,package_name, package_version):
        status = "not vulnerable"
        start_limit = ""
        end_limit = ""
        nvd_api = 'https://services.nvd.nist.gov/rest/json/cves/2.0'

        try:
            url=f"{nvd_api}?keywordSearch={package_name}+{package_version}"
            response = requests.get(f"{nvd_api}?keywordSearch={package_name}+{package_version}")

            if response.status_code == 200:
                nvd_data = response.json()
                vulnerabilities = nvd_data.get("vulnerabilities", [])

                for vulnerability in vulnerabilities:
                    cve_id = vulnerability.get('cve', {}).get('id', 'Unknown CVE')
                    configurations = vulnerability.get('cve', {}).get('configurations', [])

                    # Extracting the CVSS base score
                    base_score = 0
                    cvss_metrics = vulnerability.get('cve', {}).get('metrics', {}).get('cvssMetricV31', [])

                    for metric in cvss_metrics:
                        cvss_data = metric.get('cvssData', {})
                        severity = cvss_data.get('baseSeverity')
                        base_score = max(base_score, cvss_data.get('baseScore', 0))



                    # If baseScore is >=7, consider vulnerable directly
                    if base_score >= 7:
                        print(f"Base Score is {base_score}, marking {package_name} as vulnerable!")
                        return "Vulnerable"

                    # Checking version-based vulnerabilities
                    for config in configurations:
                        for node in config.get('nodes', []):
                            for match in node.get('cpeMatch', []):
                                cpe23Uri = match.get('criteria', '')
                                if match.get('versionStartIncluding'):
                                    start_limit = "include"
                                    start = match.get('versionStartIncluding')
                                else:
                                    start_limit = "exclude"
                                    start = match.get('versionStartExcluding', 'N/A')
                                if match.get('versionEndIncluding'):
                                    end_limit = "include"
                                    end = match.get('versionEndIncluding')
                                else:
                                    end_limit = "exclude"
                                    end = match.get('versionEndExcluding', 'N/A')

                                if start == 'N/A' and end == 'N/A':
                                    continue
                                vulnerability = match.get('vulnerable')

                                cpe_entry = {
                                    "vulnerable": vulnerability,
                                    "criteria": cpe23Uri,
                                    "start": start,
                                    "end": end
                                }

                                isValid = self.is_valid_cpe(cpe_entry, package_name, package_version, start_limit, end_limit)
                                status, safe_version = isValid  # No more errors
                                if status:
                                    status1 = "Vulnerable"
                                    result = {
                                        "vulnerability_status": status1,
                                        "severity": severity,
                                        "cpe_affected": cve_id,
                                        "base_score": base_score,
                                        "next_safe_version": safe_version
                                    }

                                    return result

            else:
                print('Error:', response.status_code)
                return None

        except requests.exceptions.RequestException as e:
            print('Error:', e)
            return None

        return status

    def get_next_patch_version(current_version):
        version = Version(current_version)
        next_version = f"{version.major}.{version.minor}.{version.micro + 1}"
        return next_version

    def is_valid_cpe(self,cpe_entry, target_product, package_version, start_limit, end_limit):
        # Step 1: Extract product name dynamically from criteria
        criteria = cpe_entry.get("criteria", "")
        parts = criteria.split(":")  # CPE format: cpe:2.3:a:<vendor>:<product>:...

        if len(parts) < 4 or parts[2] != "a":  # Ensure it's an application
            return False, None

        product_name = parts[3].lower()

        # Step 2: Ensure the extracted product matches the target product
        if target_product.lower() not in product_name and product_name not in target_product.lower():
            return False, None

        # Step 3: Ensure the entry is marked as vulnerable
        if not cpe_entry.get("vulnerable", False):
            return False, None

        # Step 4: Extract version constraints
        version_start = cpe_entry.get("start")
        version_end = cpe_entry.get("end")

        # Convert package_version and CPE versions to comparable format
        package_version = Version(package_version)
        if version_start != "N/A":
            version_start = Version(version_start)
        if version_end != "N/A":
            version_end = Version(version_end)

        # Version checks based on inclusion/exclusion limits
        if version_start == 'N/A' and version_end:
            if end_limit == "exclude":
                if package_version < version_end:
                    print("Vulnerable for this CPE:", criteria)
                    return True, version_end
                else:
                    return False, None
            elif end_limit == "include":
                if package_version <= version_end:
                    return True, version_end
                else:
                    return False, None

        if version_start != 'N/A' and version_end != 'N/A':
            if start_limit == 'include' and end_limit == 'include':
                if version_start <= package_version <= version_end:
                    print(version_start)
                    print(version_end)
                    next_safe_version = self.get_next_patch_version(version_end)
                    return True, next_safe_version
                else:
                    return False, None
            elif start_limit == 'exclude' and end_limit == 'exclude':
                if version_start < package_version < version_end:
                    print(version_start)
                    print(version_end)
                    return True, version_end
                else:
                    return False, None
            if start_limit == 'include' and end_limit == 'exclude':
                if version_start <= package_version < version_end:
                    print(version_start)
                    print(version_end)
                    next_safe_version = version_end
                    return True, next_safe_version
                else:
                    return False, None
            elif start_limit == 'exclude' and end_limit == 'include':
                if version_start < package_version <= version_end:
                    print(version_start)
                    print(version_end)
                    next_safe_version = self.get_next_patch_version(version_end)
                    return True, next_safe_version
                else:
                    return False, None

        if version_end == 'N/A' and version_start:
            if start_limit == "include":
                if package_version >= version_start:
                    print(version_start)
                    print(version_end)
                    return True, version_start
                else:
                    return False, None
            elif start_limit == 'exclude':
                if package_version > version_start:
                    print(version_start)
                    print(version_end)
                    return True, version_start
                else:
                    return False, None

        return False, None

if __name__ == "__main__":
    nvd_handler = NVDHandler()
    print(nvd_handler.handle("4.17.20", "lodash", "npm"))












