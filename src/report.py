import json

def generate_html_report(json_data, output_html="vulnerability_report.html"):
    # Read HTML template
    with open("report_template.html", "r") as template_file:
        html_content = template_file.read()

    # Generate table rows
    table_rows = []
    for entry in data:
        num_vulns = len(entry["vulnerabilities"])
        package_parts = entry["package_hierarchy"].split(" > ")

        # First row
        first_row = f"""
        <tr>
            <td rowspan="{num_vulns}">{entry["s_no"]}</td>
            <td rowspan="{num_vulns}">
                {"<span class='parent-package'>" + " > ".join(package_parts[:-1]) + "</span> > " if len(package_parts) > 1 else ""}
                <span class='vulnerable-package'>{package_parts[-1]}</span>
            </td>
            <td>{entry["vulnerable_versions"][0]}</td>
            <td>{entry["vulnerabilities"][0]["vulnerability_id"]}</td>
            <td>{entry["vulnerabilities"][0]["vulnerability_type"]}</td>
            <td class="severity-{entry["vulnerabilities"][0]["severity"]}">{entry["vulnerabilities"][0]["severity"]}</td>
            <td>{entry["vulnerabilities"][0]["patched_version"]}</td>
        </tr>
        """
        table_rows.append(first_row)

        # Subsequent rows
        for i in range(1, num_vulns):
            subsequent_row = f"""
            <tr>
                <td>{entry["vulnerable_versions"][i]}</td>
                <td>{entry["vulnerabilities"][i]["vulnerability_id"]}</td>
                <td>{entry["vulnerabilities"][i]["vulnerability_type"]}</td>
                <td class="severity-{entry["vulnerabilities"][i]["severity"]}">{entry["vulnerabilities"][i]["severity"]}</td>
                <td>{entry["vulnerabilities"][i]["patched_version"]}</td>
            </tr>
            """
            table_rows.append(subsequent_row)

    # Insert rows into template
    html_content = html_content.replace("<!-- TABLE_ROWS -->", "\n".join(table_rows))

    # Save report
    with open(output_html, "w") as f:
        f.write(html_content)

if __name__ == "__main__":
    # Test data
    data = [
        {
            'package_name': 'Package C',
            'version': '1.5',
            'paths': [
                'Package A > Package B', # B imports C v1.5
                'Package D' # D imports C v1.5
            ],
            'vulnerabilities': [
                {
                    'cve': 'CVE-1234-56789',
                    'severity': 'MODERATE',
                    'firstPatchedVersion': '1.9',
                    'vuln_types': [
                        'SQL Injection',
                        'Null Pointer Dereferencing'
                    ]
                },
                {
                    'cve': 'CVE-9283-28373',
                    'severity': 'LOW',
                    'firstPatchedVersion': '1.7',
                    'vuln_types': [] # CWEs not available
                }
            ]
        },
        {
            'package_name': 'Package X',
            'version': '5.1',
            'paths': None, # X is a direct dependency
            'vulnerabilities': [
                {
                    'cve': 'CVE-1234-78787',
                    'severity': 'HIGH',
                    'firstPatchedVersion': '6.0',
                    'vuln_types': [
                        'Malicious code'
                    ]
                },
            ]
        },
        {
            'package_name': 'Package C',
            'version': '2.2',
            'paths': [
                'Package Z' # Z imports C v2.2
            ],
            'vulnerabilities': [
                {
                    'cve': 'CVE-1234-56789',
                    'severity': 'MODERATE',
                    'firstPatchedVersion': '2.7',
                    'vuln_types': [
                        'SQL Injection'
                    ]
                },
            ]
        }
    ]

    generate_html_report(data)