def get_tooltip_css(msg):
    return f"""
        <style>
            .tooltip {{
                # display: inline-block;
                cursor: pointer;
                margin-left: 0%;
                margin-top: -18px;
                border-radius: 9px;
                border: 3px;
                border-style: ridge;
                border-color: darkred;
                text-align: center;
                background-color: #dc143c;
            }}

            .tooltip .tooltiptext {{
                visibility: hidden;
                width: max-content;
                background-color: #dc143c;
                color: #fff;
                border-radius: 6px;
                padding: 8px 10px;
                position: absolute;
                left: 0%;
                z-index: 1;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 14px;
                white-space: normal;
            }}

            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
        </style>
        <div class="tooltip">❌ <font style='color:#ffa07a;'>ERROR</font>
            <span class="tooltiptext" style='top:-55px; left:40px'>{msg}</span>
        </div>
    """


def get_self_review_css(reviewer):
    return f"""
        <style>
            div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
                position: fixed;
                top: 4.2rem;
                width: 89.6%;
                opacity: 0.7;
                background-color: black;
                z-index: 999;
            }}
        </style>
        <div class="fixed-header">
            <center><h6 style='color: white;'>The reviewer is: <font style='color:magenta;'>{reviewer}</font></h4></center>
        </div>
    """
