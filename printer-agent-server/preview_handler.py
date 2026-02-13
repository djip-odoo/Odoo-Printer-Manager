# escpos_preview_handler.py

import io
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Response
from PIL import Image, ImageDraw, ImageFont

router = APIRouter()
printer_clients = {}
printer_images = {}

font = ImageFont.load_default()
CANVAS_WIDTH = 600


# -----------------------------
# WebSocket endpoint
# -----------------------------
@router.websocket("/preview/ws/{printer}")
async def preview_ws(websocket: WebSocket, printer: str):
    await websocket.accept()

    if printer not in printer_clients:
        printer_clients[printer] = set()

    printer_clients[printer].add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        printer_clients[printer].discard(websocket)
    except:
        printer_clients[printer].discard(websocket)


# -----------------------------
# Broadcast combined PNG
# -----------------------------
async def broadcast_new_image(img: Image.Image, printer: str):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    if printer not in printer_clients:
        return

    dead = []
    for ws in printer_clients[printer]:
        try:
            await ws.send_text(b64)
        except:
            dead.append(ws)

    for ws in dead:
        printer_clients[printer].discard(ws)



# -----------------------------
# Render ESC/POS raster image
# -----------------------------
def render_escpos_image(data: bytes, width_bytes: int, height: int) -> Image.Image:
    width = width_bytes * 8
    img = Image.new("1", (width, height), 1)  # 1 = white
    pixels = img.load()

    for y in range(height):
        for x_byte in range(width_bytes):
            index = y * width_bytes + x_byte
            if index >= len(data):
                continue
            byte = data[index]
            for bit in range(8):
                x = x_byte * 8 + (7 - bit)  # MSB first
                if x >= width:
                    continue
                pixels[x, y] = 0 if (byte >> bit) & 1 else 1
    return img.convert("RGB")


# -----------------------------
# ESC/POS → Image Preview (prepend mode)
# -----------------------------
async def send_escpos_preview(esc_bytes: bytes, printer:str):
    img = Image.new("RGB", (CANVAS_WIDTH, 4000), "white")
    draw = ImageDraw.Draw(img)
    y = 20
    x = 20
    align = "left"

    i = 0
    while i < len(esc_bytes):
        b = esc_bytes[i]

        # ESC @ → init
        if b == 0x1b and i + 1 < len(esc_bytes) and esc_bytes[i + 1] == 0x40:
            y = 20
            x = 20
            align = "left"
            i += 2
            continue

        # ESC a n → alignment
        elif b == 0x1b and i + 2 < len(esc_bytes) and esc_bytes[i + 1] == 0x61:
            n = esc_bytes[i + 2]
            align = {0: "left", 1: "center", 2: "right"}.get(n, "left")
            i += 3
            continue

        # GS v 0 → raster image
        elif b == 0x1d and i + 5 < len(esc_bytes) and esc_bytes[i + 1] == 0x76 and esc_bytes[i + 2] == 0x30:
            mode = esc_bytes[i + 3]
            xL = esc_bytes[i + 4]
            xH = esc_bytes[i + 5]
            yL = esc_bytes[i + 6]
            yH = esc_bytes[i + 7]
            width_bytes = xL + (xH << 8)
            height = yL + (yH << 8)
            data_start = i + 8
            data_end = data_start + width_bytes * height
            raster_data = esc_bytes[data_start:data_end]

            if raster_data:
                im = render_escpos_image(raster_data, width_bytes, height)
                # Alignment
                px = {"left": 20, "center": (CANVAS_WIDTH - im.width)//2, "right": CANVAS_WIDTH - im.width - 20}[align]
                img.paste(im, (px, y))
                y += im.height + 20

            i = data_end
            continue

        # Cut command (GS V 0)
        elif b == 0x1d and i + 2 < len(esc_bytes) and esc_bytes[i + 1] == 0x56:
            y += 50
            i += 3
            continue

        # Printable text
        elif 0x20 <= b <= 0x7E:
            ch = chr(b)
            bbox = draw.textbbox((0, 0), ch, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            px = {"left": x, "center": (CANVAS_WIDTH - w)//2, "right": CANVAS_WIDTH - w - 20}[align]
            draw.text((px, y), ch, font=font, fill="black")
            x += w
            i += 1
            continue

        # Newline
        elif b == 0x0a:
            x = 20
            y += 25
            i += 1
            continue

        else:
            i += 1  # skip unknown byte

    cropped = img.crop((0, 0, CANVAS_WIDTH, y + 50))

    # --- Prepend this print to preview list ---
    if printer_images.get(printer):
        printer_images[printer].insert(0, cropped)
    else:
        printer_images[printer] = [cropped]
    await broadcast_new_image(cropped, printer)



# -----------------------------
# /preview HTML page
# -----------------------------
@router.get("/preview/{printer}")
async def preview_html(printer: str):
    y = printer.split("_")
    if len(y) == 2:
        url = f"/vid/{y[0]}/pid/{y[1]}"
    else:
        url = f"/ip/{printer}"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>ESC/POS Preview — {printer}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />

        <style>
            :root {{
                --bg: #f4f6f8;
                --card: #ffffff;
                --border: #e0e0e0;
                --text: #222;
                --muted: #666;
                --success: #2ecc71;
                --danger: #e74c3c;
                --accent: #4f46e5;
            }}

            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 24px;
                background: var(--bg);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                color: var(--text);
            }}

            h1 {{
                font-size: 1.4rem;
                margin: 0 0 6px;
            }}

            .subtitle {{
                color: var(--muted);
                font-size: 0.9rem;
            }}

            .card {{
                background: var(--card);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.06);
                margin-bottom: 20px;
            }}

            .header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
            }}

            .status {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 0.85rem;
                font-weight: 600;
            }}

            .dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: var(--danger);
            }}

            .dot.connected {{
                background: var(--success);
            }}

            .endpoint {{
                font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
                background: #f9fafb;
                border: 1px solid var(--border);
                padding: 10px 12px;
                border-radius: 8px;
                font-size: 0.85rem;
                margin-top: 6px;
                word-break: break-all;
            }}

            .label {{
                font-size: 0.75rem;
                color: var(--muted);
                margin-top: 14px;
            }}

            #container {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
                gap: 16px;
            }}

            .preview {{
                background: #fff;
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.04);
                animation: fadeIn 0.25s ease-out;
            }}

            .preview img {{
                width: 100%;
                max-width: 360px;
                display: block;
                margin: auto;
            }}

            @keyframes fadeIn {{
                from {{
                    opacity: 0;
                    transform: translateY(6px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            .copy-row {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .copy-btn {{
                border: 1px solid #ddd;
                background: #fff;
                padding: 6px 10px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.8rem;
            }}

            .copy-btn:hover {{
                background: #f3f4f6;
            }}

        </style>
    </head>
    <body>

        <div class="card">
            <div class="header">
                <div>
                    <h1>ESC/POS Live Preview</h1>
                    <div class="subtitle">Printer: <strong>{printer}</strong></div>
                </div>

                <div class="status">
                    <div id="status-dot" class="dot"></div>
                    <span id="status-text">Connecting…</span>
                </div>
            </div>
            <div class="copy-row">
                <div class="label">Print endpoint</div>
                <div id="print-endpoint" class="endpoint"></div>
                <button class="copy-btn" onclick="copyText('print-endpoint', this)">
                    Copy
                </button>
            </div>

            <div class="copy-row">
                <div class="label">Success callback</div>
                <div id="print-endpoint-success" class="endpoint"></div>
                <button class="copy-btn" onclick="copyText('print-endpoint-success', this)">
                    Copy
                </button>
            </div>
        </div>

        <div id="container"></div>

        <script>
            const statusText = document.getElementById("status-text");
            const statusDot = document.getElementById("status-dot");

            const ws = new WebSocket("ws://" + location.host + "/preview/ws/{printer}");

            ws.onopen = () => {{
                statusText.innerText = "Connected";
                statusDot.classList.add("connected");

                document.getElementById("print-endpoint").innerText =
                    location.host + "{url}";
                document.getElementById("print-endpoint-success").innerText =
                    location.host + "{url}/success";

                setInterval(() => ws.send("ping"), 5000);
            }};

            ws.onmessage = (ev) => {{
                const container = document.getElementById("container");

                const wrapper = document.createElement("div");
                wrapper.className = "preview";

                const img = document.createElement("img");
                img.src = "data:image/png;base64," + ev.data;

                wrapper.appendChild(img);
                container.insertBefore(wrapper, container.firstChild);
            }};

            ws.onclose = () => {{
                statusText.innerText = "Disconnected";
                statusDot.classList.remove("connected");
            }};

            function copyText(elementId, btn) {{
                const text = document.getElementById(elementId).innerText;

                if (navigator.clipboard) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        flashCopied(btn);
                    }});
                }} else {{
                    // fallback
                    const temp = document.createElement("textarea");
                    temp.value = text;
                    document.body.appendChild(temp);
                    temp.select();
                    document.execCommand("copy");
                    document.body.removeChild(temp);
                    flashCopied(btn);
                }}
            }}

            function flashCopied(btn) {{
                const old = btn.innerText;
                btn.innerText = "Copied ✓";
                btn.disabled = true;

                setTimeout(() => {{
                    btn.innerText = old;
                    btn.disabled = false;
                }}, 1200);
            }}
        </script>

    </body>
    </html>
    """

    return Response(html, media_type="text/html")
