# epson_epos_handler.py
import socket
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Body, Response
import logging
import usb.core
import usb.util
import base64
from ddl_path import load_libusb_backend
from preview_handler import send_escpos_preview
import asyncio
router = APIRouter()
logger = logging.getLogger("epson-epos")

# ================================================================
# Utils
# ================================================================
def xml_success():
    return Response("<response success='true' code=''></response>", media_type="text/xml")

def xml_error(code, msg=""):
    return Response(f"<response success='false' code='{code}'>{msg}</response>", media_type="text/xml")


# ================================================================
# Epson ePOS XML → ESC/POS Converter
# ================================================================
def generate_escpos_from_epos_xml(xml_text: str, printer: str) -> bytes:
    ns = {
        "s": "http://schemas.xmlsoap.org/soap/envelope/",
        "e": "http://www.epson-pos.com/schemas/2011/03/epos-print"
    }

    root = ET.fromstring(xml_text)
    epos = root.find(".//e:epos-print", ns)
    if epos is None:
        raise Exception("<epos-print> not found")
    esc = b"\x1b@"  # ESC @ (init)

    for child in epos:
        tag = child.tag.split("}")[-1]

        # FEED
        if tag == "feed":
            esc += b"\n" * int(child.attrib.get("line", "1"))

        # TEXT
        elif tag == "text":
            align = child.attrib.get("align", "left")
            esc += {
                "center": b"\x1b\x61\x01",
                "right":  b"\x1b\x61\x02"
            }.get(align, b"\x1b\x61\x00")

            esc += (child.text or "").encode("utf-8") + b"\n"

        # IMAGE
        elif tag == "image":
            img_data_b64 = (child.text or "").strip()
            if not img_data_b64:
                continue

            raw = base64.b64decode(img_data_b64)
            height = int(child.attrib["height"])

            if len(raw) % height != 0:
                raise Exception(f"Image RAW length mismatch height={height}")

            width_bytes = len(raw) // height
            esc += b"\x1d\x76\x30\x00"
            esc += bytes([width_bytes & 0xFF, width_bytes >> 8])
            esc += bytes([height & 0xFF, height >> 8])
            esc += raw

    esc += b"\x1dV\x00"  # CUT
    asyncio.create_task(send_escpos_preview(esc, printer))
    return esc


# ================================================================
# USB Printing
# ================================================================
def direct_usb_print(data: bytes, pid: str, vid: str):
    try:
        dev = usb.core.find(
            idVendor=int(vid, 16),
            idProduct=int(pid, 16),
            backend=load_libusb_backend()
        )
        if dev is None:
            raise Exception("USB printer not found")

        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except:
            pass

        usb.util.claim_interface(dev, 0)
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        ep_out = None
        for ep in intf:
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                ep_out = ep.bEndpointAddress
                break

        if ep_out is None:
            raise Exception("No USB OUT endpoint found")
        
        dev.write(ep_out, data, timeout=5000)

        usb.util.release_interface(dev, 0)
        dev.reset()
        return True

    except Exception as e:
        logger.error(f"USB Print Error: {e}")
        return False


# ================================================================
# Network Printing
# ================================================================
def direct_network_print(data: bytes, ip: str):
    try:
        with socket.create_connection((ip, 9100), timeout=10) as s:
            s.sendall(data)
        return True
    except Exception as e:
        logger.error(f"Network Print Error: {e}")
        return False


# ================================================================
# ROUTES
# ================================================================
@router.post("/vid/{vid}/pid/{pid}/cgi-bin/epos/service.cgi")
async def epson_usb_route(vid: str, pid: str, xml_data: str = Body(..., media_type="text/xml")):
    try:
        esc = generate_escpos_from_epos_xml(xml_data, vid+"_"+pid)
        return xml_success() if direct_usb_print(esc, pid, vid) else xml_error("USB_ERROR")
    except Exception as e:
        return xml_error("PARSE_ERROR", str(e))


@router.post("/ip/{ip}/cgi-bin/epos/service.cgi")
async def epson_ip_route(ip: str, xml_data: str = Body(..., media_type="text/xml")):
    try:
        esc = generate_escpos_from_epos_xml(xml_data, str(ip))
        return xml_success() if direct_network_print(esc, ip) else xml_error("NETWORK_ERROR")
    except Exception as e:
        return xml_error("PARSE_ERROR", str(e))

@router.post("/vid/{vid}/pid/{pid}/success/cgi-bin/epos/service.cgi")
async def epson_usb_route_success(vid: str, pid: str, xml_data: str = Body(..., media_type="text/xml")):
    try:
        generate_escpos_from_epos_xml(xml_data, vid+"_"+pid )
        print("")
        logger.error(f"=================== success at VID: {vid} | PID: {pid} ")
        return xml_success()
    except Exception as e:
        return xml_error("PARSE_ERROR", str(e))
