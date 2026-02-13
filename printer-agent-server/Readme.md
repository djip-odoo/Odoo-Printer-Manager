
🔐 Local Print Agent API
==========================

A cross-platform FastAPI-based local print agent to communicate with ESC/POS thermal printers over raw sockets using base64 raster data.

---

🚀 Features
-----------
- ✅ FastAPI backend with HTTP(use LNA for sending request from https)
- ✅ ESC/POS raster image printing
- ✅ Cash drawer pulse support
- ✅ Printer status reporting (cover open, paper error, etc.)
- ✅ Build as a standalone executable (Windows/Linux/macOS)
- ✅ CORS enabled for cross-origin access

---


🛠 Setup & Build Instructions
-----------------------------

### Linux / macOS:

```bash
chmod +x build.sh
./build.sh
```

### Windows:

```cmd
build_windows.bat
```

---

📦 Dependencies (frozen)
------------------------
- fastapi===0.115.12
- uvicorn[standard]===0.38.0
- pydantic===2.11.5
- nuitka===2.8.6
- python-escpos===3.1
- pyusb===1.3.1
- jinja2===3.0.3
- python-multipart===0.0.20
- zeroconf===0.148.0


---


# 📬 API Endpoints

------------------------------------------------------------------------

##  POST /vid/{vid}/pid/{pid}/cgi-bin/epos/service.cgi

Print via USB printer using Vendor ID (VID) and Product ID (PID).

### Path Parameters

-   **vid**: USB Vendor ID\
-   **pid**: USB Product ID


### Body
```xml
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
    <s:Body>
        <epos-print xmlns="http://www.epson-pos.com/schemas/2011/03/epos-print">
            <feed line="1" />
            <text align="center">This is a test receipt&#10;</text>
            <feed line="3" />
            <cut type="feed" />
        </epos-print>
    </s:Body>
</s:Envelope>
```

### Success Response

XML success response.
```xml
<response success='true' code=''></response>
```

### Error Responses

-   `USB_ERROR` 
```xml
<response success='false' code='USB_ERROR'></response>
```
-   `PARSE_ERROR`
```xml
<response success='false' code='PARSE_ERROR'></response>
```
------------------------------------------------------------------------

## POST /ip/{ip}/cgi-bin/epos/service.cgi

Print via network printer using IP address.

### Path Parameters

-   **ip**: Printer IP Address


### Body
```xml
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
    <s:Body>
        <epos-print xmlns="http://www.epson-pos.com/schemas/2011/03/epos-print">
            <feed line="1" />
            <text align="center">This is a test receipt&#10;</text>
            <feed line="3" />
            <cut type="feed" />
        </epos-print>
    </s:Body>
</s:Envelope>
```


### Success Response

XML success response.
```xml
<response success='true' code=''></response>
```

### Error Responses

-   `USB_ERROR` 
```xml
<response success='false' code='USB_ERROR'></response>
```
-   `PARSE_ERROR`
```xml
<response success='false' code='PARSE_ERROR'></response>
```
------------------------------------------------------------------------
### POST /vid/{vid}/pid/{pid}/success/cgi-bin/epos/service.cgi

Simulated success endpoint for USB printer.

### Path Parameters

-   **vid**: USB Vendor ID\
-   **pid**: USB Product ID


### Body
```xml
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
    <s:Body>
        <epos-print xmlns="http://www.epson-pos.com/schemas/2011/03/epos-print">
            <feed line="1" />
            <text align="center">This is a test receipt&#10;</text>
            <feed line="3" />
            <cut type="feed" />
        </epos-print>
    </s:Body>
</s:Envelope>
```


### Success Response

XML success response.
```xml
<response success='true' code=''></response>
```


🧪 Running the Server After Build
---------------------------------

```bash
./dist/main          # Linux/macOS
dist\main.exe       # Windows
```

It runs on:

```
http://{your_device_ip_address}:8089/
```
