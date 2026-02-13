import logging
import uvicorn
import os
import sys
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from check_status import check_printer_status
from get_printer_list import list_known_epos_printers , printer_list_page
from fastapi.responses import HTMLResponse

from epson_epos_handler import router as epson_router
from preview_handler import router as preview_route
import ddl_path

from set_local_ip import get_lan_ip

PORT=8089


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("print-server")

app = FastAPI(
    title="Local Print Agent API",
    description="A FastAPI server to communicate with ESC/POS thermal printers over USB.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusCheckRequest(BaseModel):
    vendor_id: str
    product_id: str

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return printer_list_page(request)

@app.get("/check-host")
def check_host_route():
    return {"status": "ok", "message": "success", "server_ip": get_lan_ip()+":"+str(PORT)}

@app.get("/printer-list")
async def printer_list(request: Request, all: bool = Query(False, description="Return all devices")):
    """
    Returns the list of known EPOS printers.
    If all=true, include all printers (even offline or unconfigured).
    """
    printers = list_known_epos_printers(known=not all)  # pass the param to your function
    return {"status": "success", "message": printers}


@app.get("/vid/{vid}/pid/{pid}/printer/status-usb/saved")
def checkPrinterStatus(vid: str, pid: str):
    return check_printer_status(vid, pid)

app.include_router(epson_router)
app.include_router(preview_route)

def resource_path(filename: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.abspath(filename)

if __name__ == "__main__":
    # ssl_dir = resource_path("ssl")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        # ssl_certfile=os.path.join(ssl_dir, "printer-server.local.crt"),
        # ssl_keyfile=os.path.join(ssl_dir, "printer-server.local.key"),
    )
