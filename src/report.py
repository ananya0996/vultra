import json
import os

def generate_html_report(json_data, output_html="vulnerability_report.html"):
    # Correct path to template files
    template_path = "src\\report_template\\report_template.html"
    styles_path = "src\\report_template\\report_template.css"

    if not os.path.exists(template_path):
            print(f"ERROR: Template file not found at {template_path}")
            return False

    if not os.path.exists(styles_path):
            print(f"ERROR: Template file not found at {styles_path}")
            return False
    
    with open(template_path, "r") as template_file:
        html_content = template_file.read()
    
    with open(styles_path, "r") as styles_file:
        css_content = styles_file.read()
    
    if not json_data:
            print("No vulnerability data to report.")
            return False

    table_rows = []
    s_no = 1
    
    for entry in json_data:
        package_name = entry['package_name']
        version = entry['version']
        vulnerabilities = entry['vulnerabilities']
        paths = entry['paths'] if entry.get('paths') is not None else [None]

        # Handle paths as a list of strings
        if not isinstance(paths, list):
            paths = [None]
        
        for path in paths:
            is_transitive = path is not None
            
            if path:
                # Split by "->" instead of " > "
                path_parts = path.split("->")
                
                # The last item in path_parts might already be the vulnerable package
                if path_parts[-1] != package_name:
                    formatted_path = ' > '.join(
                        [f'<span class="parent-package">{p}</span>' for p in path_parts] + 
                        [f'<span class="vulnerable-package">{package_name}</span>']
                    )
                else:
                    # If the path already includes the vulnerable package
                    formatted_path = ' > '.join(
                        [f'<span class="parent-package">{p}</span>' for p in path_parts[:-1]] + 
                        [f'<span class="vulnerable-package">{path_parts[-1]}</span>']
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
                <td>{', '.join(first_vuln['vuln_types']) if isinstance(first_vuln['vuln_types'], list) else 'N/A'}</td>
                <td class="severity-{first_vuln['severity'].lower()}">{first_vuln['severity']}</td>
                <td>{first_vuln['firstPatchedVersion']}</td>
            </tr>
            """)

            # Subsequent rows
            for vuln in vulnerabilities[1:]:
                table_rows.append(f"""
                <tr class="{'transitive' if is_transitive else 'direct'}">
                    <td>{vuln['cve']}</td>
                    <td>{', '.join(vuln['vuln_types']) if isinstance(vuln['vuln_types'], list) else 'N/A'}</td>
                    <td class="severity-{vuln['severity'].lower()}">{vuln['severity']}</td>
                    <td>{vuln['firstPatchedVersion']}</td>
                </tr>
                """)
            
            s_no += 1

    html_content = html_content.replace("/* CSS_PLACEHOLDER */", css_content)
    html_content = html_content.replace("<!-- TABLE_ROWS -->", "\n".join(table_rows))

    with open(output_html, "w") as f:
        f.write(html_content)
    print(f"HTML report generated successfully: {os.path.abspath(output_html)}")