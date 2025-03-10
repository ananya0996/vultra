
# vulnerability_report.py
import json

def generate_html_report(json_file, output_html="vulnerability_report.html"):
    # Read HTML template
    with open("report_template.html", "r") as template_file:
        html_content = template_file.read()

    # Load JSON data
    with open(json_file, "r") as f:
        data = json.load(f)

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
    json_input = '''[
        {
            "s_no": 1,
            "package_hierarchy": "Package A > Package B > Package C",
            "vulnerable_versions": ["1.2", "1.2"],
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-12345",
                    "vulnerability_type": "SQL Injection",
                    "severity": "HIGH",
                    "patched_version": "1.5"
                },
                {
                    "vulnerability_id": "CVE-45678",
                    "vulnerability_type": "Null Pointer Deref",
                    "severity": "MED",
                    "patched_version": "1.4"
                }
            ]
        },
        {
            "s_no": 2,
            "package_hierarchy": "Package X",
            "vulnerable_versions": ["4.5"],
            "vulnerabilities": [
                {
                    "vulnerability_id": "CVE-54321",
                    "vulnerability_type": "Hardcoded Credentials",
                    "severity": "LOW",
                    "patched_version": "4.9"
                }
            ]
        }
    ]'''

    with open("vulnerabilities.json", "w") as f:
        f.write(json_input)

    generate_html_report("vulnerabilities.json")