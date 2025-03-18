import json

def generate_html_report(json_data, output_html="vulnerability_report.html"):
    with open("report_template.html", "r") as template_file:
        html_content = template_file.read()
    
    with open("styles.css", "r") as styles_file:
        css_content = styles_file.read()

    table_rows = []
    s_no = 1
    
    for entry in json_data:
        package_name = entry['package_name']
        version = entry['version']
        vulnerabilities = entry['vulnerabilities']
        paths = entry['paths'] if entry.get('paths') is not None else [None]

        for path in paths:
            is_transitive = path is not None
            
            if path:
                path_parts = path.split(' > ')
                formatted_path = ' > '.join(
                    [f'<span class="parent-package">{p}</span>' for p in path_parts] + 
                    [f'<span class="vulnerable-package">{package_name}</span>']
                )
            else:
                formatted_path = f'<span class="vulnerable-package">{package_name}</span>'

            num_vulns = len(vulnerabilities)
            
            if num_vulns == 0:
                continue

            # First row with rowspan
            first_vuln = vulnerabilities[0]
            table_rows.append(f"""
            <tr class="{'transitive' if is_transitive else 'direct'}">
                <td rowspan="{num_vulns}">{s_no}</td>
                <td rowspan="{num_vulns}">{formatted_path}</td>
                <td rowspan="{num_vulns}">{version}</td>
                <td>{first_vuln['cve']}</td>
                <td>{', '.join(first_vuln['vuln_types']) or 'N/A'}</td>
                <td class="severity-{first_vuln['severity'].lower()}">{first_vuln['severity']}</td>
                <td>{first_vuln['firstPatchedVersion']}</td>
            </tr>
            """)

            # Subsequent rows
            for vuln in vulnerabilities[1:]:
                table_rows.append(f"""
                <tr class="{'transitive' if is_transitive else 'direct'}">
                    <td>{vuln['cve']}</td>
                    <td>{', '.join(vuln['vuln_types']) or 'N/A'}</td>
                    <td class="severity-{vuln['severity'].lower()}">{vuln['severity']}</td>
                    <td>{vuln['firstPatchedVersion']}</td>
                </tr>
                """)
            
            s_no += 1

    html_content = html_content.replace("/* CSS_PLACEHOLDER */", css_content)
    html_content = html_content.replace("<!-- TABLE_ROWS -->", "\n".join(table_rows))

    with open(output_html, "w") as f:
        f.write(html_content)

if __name__ == "__main__":
    test_data = [
        {
            'package_name': 'Package C',
            'version': '1.5',
            'paths': [
                'Package A > Package B',  # B imports C v1.5
                'Package D'  # D imports C v1.5
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
                    'vuln_types': []  # CWEs not available
                }
            ]
        },
        {
            'package_name': 'Package X',
            'version': '5.1',
            'paths': None,  # X is a direct dependency
            'vulnerabilities': [
                {
                    'cve': 'CVE-1234-78787',
                    'severity': 'HIGH',
                    'firstPatchedVersion': '6.0',
                    'vuln_types': [
                        'Malicious code'
                    ]
                }
            ]
        },
        {
            'package_name': 'Package C',
            'version': '2.2',
            'paths': [
                'Package Z'  # Z imports C v2.2
            ],
            'vulnerabilities': [
                {
                    'cve': 'CVE-1234-56789',
                    'severity': 'MODERATE',
                    'firstPatchedVersion': '2.7',
                    'vuln_types': [
                        'SQL Injection'
                    ]
                }
            ]
        }
    ]

    generate_html_report(test_data)
