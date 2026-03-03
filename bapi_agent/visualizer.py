"""
BAPI Agent - Parametre Gorsellestiricisi.

BAPI parametrelerini HTML/CSS kartlar ile gorsellestir.
Her parametre grubu (IMPORT/EXPORT/TABLES) farkli renklerde gosterilir.
Zorunlu alanlar vurgulanir, ornek degerler gosterilir.
"""


# Parametre yonune gore renkler
DIRECTION_COLORS = {
    "IMPORT": {"bg": "rgba(76, 175, 80, 0.15)", "border": "#4CAF50", "header": "#66BB6A", "label": "IMPORT"},
    "EXPORT": {"bg": "rgba(33, 150, 243, 0.15)", "border": "#2196F3", "header": "#42A5F5", "label": "EXPORT"},
    "TABLES": {"bg": "rgba(255, 152, 0, 0.15)", "border": "#FF9800", "header": "#FFA726", "label": "TABLES"},
    "CHANGING": {"bg": "rgba(156, 39, 176, 0.15)", "border": "#9C27B0", "header": "#AB47BC", "label": "CHANGING"},
}


def create_bapi_parameter_html(bapi_name: str, bapi_data: dict, used_bapis: list = None) -> tuple:
    """
    BAPI parametrelerini HTML kartlari olarak gorsellestir.

    Args:
        bapi_name: BAPI adi
        bapi_data: BAPI metadata dict'i
        used_bapis: Kullanilan BAPI adlari listesi

    Returns:
        (html_string, height_in_pixels)
    """
    params = bapi_data.get("parameters", [])
    if not params:
        return "", 0

    # Parametreleri yonlerine gore grupla
    groups = {}
    for param in params:
        direction = param["direction"]
        groups.setdefault(direction, []).append(param)

    # HTML olustur
    cards_html = []
    total_height = 80  # Baslik icin

    for direction in ["IMPORT", "EXPORT", "TABLES", "CHANGING"]:
        if direction not in groups:
            continue

        colors = DIRECTION_COLORS.get(direction, DIRECTION_COLORS["IMPORT"])
        group_params = groups[direction]

        group_html = f"""
        <div style="margin-bottom:16px;">
            <div style="
                background:{colors['header']};
                color:#000;
                font-weight:700;
                font-size:0.85rem;
                padding:6px 14px;
                border-radius:6px 6px 0 0;
                letter-spacing:1px;
            ">{colors['label']} Parametreleri</div>
        """

        for param in group_params:
            req_badge = ""
            if param["required"]:
                req_badge = '<span style="color:#f44336;font-weight:700;font-size:0.7rem;margin-left:8px;">ZORUNLU</span>'

            param_html = f"""
            <div style="
                background:{colors['bg']};
                border:1px solid {colors['border']}33;
                border-top:none;
                padding:10px 14px;
            ">
                <div style="font-weight:600;color:{colors['header']};font-size:0.9rem;">
                    {param['name']}
                    <span style="color:rgba(250,250,250,0.5);font-size:0.75rem;margin-left:8px;">
                        ({param['data_type']})
                    </span>
                    {req_badge}
                </div>
                <div style="color:rgba(250,250,250,0.7);font-size:0.8rem;margin-top:2px;">
                    {param['description']}
                </div>
            """

            # Alt alanlar
            if param["fields"]:
                param_html += """
                <div style="margin-top:8px;padding-left:12px;border-left:2px solid rgba(250,250,250,0.1);">
                """
                for field in param["fields"]:
                    freq_mark = '<span style="color:#f44336;">*</span>' if field["required"] else ""
                    example_html = ""
                    if field["example"]:
                        example_html = f'<span style="color:#FF8A65;font-size:0.75rem;margin-left:6px;">Ornek: {field["example"]}</span>'

                    param_html += f"""
                    <div style="
                        padding:3px 0;
                        font-size:0.8rem;
                        color:rgba(250,250,250,0.8);
                        border-bottom:1px solid rgba(250,250,250,0.05);
                    ">
                        <span style="color:#FFF;font-family:Consolas,monospace;">{field['name']}</span>
                        {freq_mark}
                        <span style="color:rgba(250,250,250,0.4);font-size:0.7rem;">
                            ({field['data_type']})
                        </span>
                        - {field['description']}
                        {example_html}
                    </div>
                    """
                param_html += "</div>"

            param_html += "</div>"
            cards_html.append(param_html)
            total_height += 60 + len(param.get("fields", [])) * 28

        group_html += "\n".join(cards_html[-len(group_params):])
        group_html += "</div>"
        cards_html.append(group_html)
        total_height += 40

    # Ana HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 12px;
                background: #0E1117;
                color: #FAFAFA;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .bapi-header {{
                background: linear-gradient(135deg, #1E1E2E, #2A2A3E);
                border: 1px solid rgba(255,87,34,0.3);
                border-radius: 8px;
                padding: 14px 18px;
                margin-bottom: 16px;
            }}
            .bapi-header h3 {{
                margin: 0;
                color: #FF5722;
                font-size: 1.1rem;
            }}
            .bapi-header .desc {{
                color: rgba(250,250,250,0.6);
                font-size: 0.85rem;
                margin-top: 4px;
            }}
            .bapi-header .op-type {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.7rem;
                font-weight: 700;
                margin-top: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="bapi-header">
            <h3>{bapi_name}</h3>
            <div class="desc">{bapi_data['description']}</div>
            <span class="op-type" style="background:rgba(255,87,34,0.2);color:#FF8A65;">
                {bapi_data['operation_type']}
            </span>
        </div>
        {"".join(cards_html)}
    </body>
    </html>
    """

    return html, min(total_height, 700)
