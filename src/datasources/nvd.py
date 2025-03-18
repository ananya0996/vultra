import os

from datasource import BaseDataSource
import subprocess
import requests
import re
import json
from packaging.version import Version, parse


class NVDHandler(BaseDataSource):
    package_manager = ["mvn", "npm"]

    def handle(self, lib_version, package, package_manager):
        if self.is_rc_version(lib_version):

            return self.direct_update_for_rc_version(package, lib_version, package_manager, "")
        else:
            return self.get_cpe_number_and_check_vulnerability(package, lib_version)

    def is_rc_version(self, lib_version):
        """Detect pre-release versions (rc, beta, SNAPSHOT, etc.)"""
        return bool(re.search(
            r"(rc|beta|alpha|preview|snapshot|nightly|m\d+|SNAPSHOT)",
            lib_version,
            re.IGNORECASE
        ))

    def direct_update_for_rc_version(self, package_name, package_version, package_manager, groupId=None):
        self.results = []
        try:
            if package_manager == "npm":
                get_all = subprocess.run(
                    [r"C:\Program Files\nodejs\npm.cmd", "show", package_name, "versions", "--json"],
                    capture_output=True, text=True, check=True, shell=True
                )
                versions = json.loads(get_all.stdout)
                stable_versions = [v for v in versions if not self.is_rc_version(v)]
                latest_stable = stable_versions[-1] if stable_versions else None
                result = [{
                    "packageName": package_name,
                    "version": package_version,
                    "stable_version": latest_stable,
                    "vuln_status": []
                }]
                self.results.append(result)
                return json.dumps(result, indent=4)
            elif package_manager == "maven":

                if ":" in package_name:
                    parts = package_name.split(":")
                    extracted_groupId = parts[0]
                    artifactId = parts[1]
                else:
                    extracted_groupId = groupId
                    artifactId = package_name


                url = f"https://search.maven.org/solrsearch/select?q=g:{extracted_groupId}+AND+a:{artifactId}&rows=10&wt=json"
                print(url)
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data["response"]["numFound"] > 0:
                        latest_version = data["response"]["docs"][0]["latestVersion"]
                        result = [{
                            "packageName": package_name,
                            "version": package_version,
                            "stable_version": latest_version,
                            "vuln_status": []
                        }]
                        self.results.append(result)
                        return json.dumps(result, indent=4)
            else:
                return f"Unsupported package manager: {package_manager}"
        except Exception as e:
            return f"Error: {str(e)}"

    def get_valid_group_id(self, artifact_id):
        """Fetch valid group IDs for a given artifact."""
        url = f"https://search.maven.org/solrsearch/select?q=a:{artifact_id}&rows=10&wt=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            group_ids = {doc["g"] for doc in data["response"]["docs"]}
            return list(group_ids)
        return None

    def is_valid_cve(self, cpe_entry, target_product):
        criteria = cpe_entry.get("criteria", "")
        parts = criteria.split(":")  # CPE format: cpe:2.3:a:<vendor>:<product>:...
        if len(parts) < 4 or parts[2] != "a":
            return False

        product_name = parts[3].lower()
        if target_product.lower() not in product_name and product_name not in target_product.lower():
            return False

        return True

    results = []

    def get_cpe_number_and_check_vulnerability(self, package_name, package_version):
        self.results = []

        start_limit = ""
        end_limit = ""
        nvd_api = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.abspath(os.path.join(script_dir, "..", "mapping", "CWEMapperNVD.json"))

        try:
            with open(file_path, 'r') as file:
                cwe_mapper = json.load(file)
        except Exception as e:
            print(f"Error loading CWE mapper: {e}")
            cwe_mapper = {}

        try:
            url = f"{nvd_api}?keywordSearch={package_name}"
            print(url)
            response = requests.get(f"{nvd_api}?keywordSearch={package_name}")

            if response.status_code == 200:
                nvd_data = response.json()
                vulnerabilities = nvd_data.get("vulnerabilities", [])
                if len(vulnerabilities) == 0:
                    return {}

                for vulnerability in vulnerabilities:
                    cve_id = vulnerability.get('cve', {}).get('id', 'Unknown CVE')
                    configurations = vulnerability.get('cve', {}).get('configurations', [])

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
                                vulnerability_possibility = match.get('vulnerable')

                                cpe_entry = {
                                    "vulnerable": vulnerability_possibility,
                                    "criteria": cpe23Uri,
                                    "start": start,
                                    "end": end
                                }
                                valid_cve = self.is_valid_cve(cpe_entry, package_name)
                                if valid_cve == False:
                                    break
                                if valid_cve:
                                    vul_status, next_patched_version = self.is_vulnerable(cpe_entry, package_name,
                                                                                          package_version, start_limit,
                                                                                          end_limit)
                                    if vul_status:
                                        cwe_list = []
                                        weaknesses = vulnerability.get('cve', {}).get('weaknesses', [])
                                        for weakness in weaknesses:
                                            for desc in weakness.get('description', []):
                                                if desc.get('lang') == 'en':
                                                    cwe_id = desc.get('value', '')

                                                    if cwe_id in cwe_mapper:
                                                        cwe_name = cwe_mapper[cwe_id].get("name", "")
                                                        cwe_description = cwe_mapper[cwe_id].get("description", "")

                                                    cwe_list.append({
                                                        "cwe_id": cwe_id,
                                                        "cwe_name": cwe_name,
                                                        "description": cwe_description
                                                    })
                                        result = {
                                            "packageName": package_name,
                                            "version": package_version,
                                            "stable_version":"",
                                            "vuln_status": {
                                                "cve_id": cve_id,
                                                "cwes": cwe_list,
                                                "firstPatchedVersion": str(
                                                    next_patched_version) if next_patched_version else None,
                                                "publishedAt": vulnerability.get('cve', {}).get('published', '')
                                            }
                                        }
                                        self.results.append(result)
                return json.dumps(self.results, indent=4)

            else:
                print('Error:', response.status_code)
                return json.dumps(None)

        except requests.exceptions.RequestException as e:
            print('Error:', e)
            return json.dumps(None)

        return json.dumps(None)

    def get_next_patch_version(current_version):
        version = Version(current_version)
        next_version = f"{version.major}.{version.minor}.{version.micro + 1}"
        return next_version

    def is_vulnerable(self, cpe_entry, target_product, package_version, start_limit, end_limit):

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
                    next_safe_version = version_end

                    return True, next_safe_version
                else:
                    return False, None
            if start_limit == 'include' and end_limit == 'exclude':
                if version_start <= package_version < version_end:
                    next_safe_version = version_end
                    return True, next_safe_version
                else:
                    return False, None
            elif start_limit == 'exclude' and end_limit == 'include':
                if version_start < package_version <= version_end:
                    next_safe_version = self.get_next_patch_version(version_end)
                    return True, next_safe_version
                else:
                    return False, None

        if version_end == 'N/A' and version_start:
            if start_limit == "include":
                if package_version >= version_start:
                    return True, version_start
                else:
                    return False, None
            elif start_limit == 'exclude':
                if package_version > version_start:
                    return True, version_start
                else:
                    return False, None

        return False, None


# if __name__ == "__main__":
#     nvd_handler = NVDHandler()
#     # print(nvd_handler.handle("4.17.21-beta","lodash","npm"))
#     # print(nvd_handler.handle("org.springframework:spring-core","5.3.0-RC1","maven"))
#     # print(nvd_handler.handle("5.3.0-RC1", "org.springframework:spring-core", "maven"))
#     print(nvd_handler.handle("2.14.1", "Log4J", "npm"))
