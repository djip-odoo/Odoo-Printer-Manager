import os
import platform
import ctypes
import usb.core
import usb.backend.libusb1

def get_dll_path():
    system = platform.system()
    arch, _ = platform.architecture()

    if system != "Windows":
        return None  # For Linux/macOS, assume libusb is installed system-wide

    base_path = os.path.dirname(__file__)
    if arch == "64bit":
        return os.path.join(base_path, "libusb", "libusb-1.0_x64.dll")
    else:
        return os.path.join(base_path, "libusb", "libusb-1.0_x32.dll")

def load_libusb_backend():
    dll_path = get_dll_path()
    if dll_path and os.path.exists(dll_path):
        try:
            ctypes.CDLL(dll_path)
            print(f"[INFO] Loaded libusb DLL: {dll_path}")
        except OSError as e:
            print(f"[ERROR] Failed to load libusb DLL: {e}")
            return None

        backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
        return backend
    else:
        print("[INFO] No DLL needed or file not found. Using system libusb.")
        return usb.backend.libusb1.get_backend()

backend = load_libusb_backend()

if backend is not None:
    devices = usb.core.find(find_all=True, backend=backend)
    for dev in devices:
        print(f"Found USB device: VID=0x{dev.idVendor:04x}, PID=0x{dev.idProduct:04x}")
else:
    print("[ERROR] libusb backend could not be initialized.")
