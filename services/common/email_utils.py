from html import escape
from urllib.parse import quote_plus


def build_owner_approval_email(
    approval_api_base_url: str,
    owner_email: str,
    window_id: str,
    window_end_utc: str,
    resources: list[dict],
) -> str:
    rows = []
    for resource in resources:
        resource_id = resource["resource_id"]
        remediation_type = resource["remediation_type"]
        link = (
            f"{approval_api_base_url}/window/{quote_plus(window_id)}/remediate"
            f"?resource_id={quote_plus(resource_id)}&actor={quote_plus(owner_email)}"
        )
        rows.append(
            "<tr>"
            f"<td>{escape(resource_id)}</td>"
            f"<td>{escape(remediation_type)}</td>"
            f"<td><a href=\"{escape(link)}\">Remediate</a></td>"
            "</tr>"
        )

    table_rows = "".join(rows)
    return f"""
    <html>
      <body>
        <p>The following resources breached cost policies.</p>
        <p>Approval window ends at: <strong>{escape(window_end_utc)}</strong></p>
        <table border=\"1\" cellspacing=\"0\" cellpadding=\"6\">
          <thead>
            <tr>
              <th>Resource ID</th>
              <th>Remediation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {table_rows}
          </tbody>
        </table>
      </body>
    </html>
    """


def send_email_placeholder(owner_email: str, subject: str, html_body: str) -> None:
    print(f"EMAIL PLACEHOLDER to={owner_email} subject={subject}")
    print(html_body)
