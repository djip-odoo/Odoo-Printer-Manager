use rusb::{Context, UsbContext};
use serde::Serialize;
use std::collections::{HashMap, HashSet};

/* ============================================================
   Data structure (same fields as Python dict)
============================================================ */

#[derive(Debug, Serialize, Clone)]
pub struct Printer {
    pub vendor_id: String,
    pub product_id: String,
    pub manufacturer: String,
    pub vendor_name: String,
    pub product: String,
    pub matched_by: String,
}

/* ============================================================
   Constants (same as Python)
============================================================ */

fn epos_printers() -> HashMap<u16, &'static str> {
    HashMap::from([
        (0x4b43, "Caysn OR Shreyans"),
        (0x0fe6, "RuGtek or Xprinter"),
        (0x04b8, "EPSON"),
        (0x1504, "BIXOLON"),
        (0x0416, "Winbond"),
        (0x1fc9, "POSBANK"),
        (0x0519, "Star Micronics"),
    ])
}

fn system_usb_keywords() -> HashSet<&'static str> {
    HashSet::from([
        "linux",
        "xhci-hcd",
        "ehci-hcd",
        "root hub",
        "usb hub",
        "microsoft",
        "standard usb host controller",
        "usb root hub",
        "generic usb hub",
        "apple",
        "usb host controller",
        "usb high-speed bus",
    ])
}

const NAME_KEYWORDS: &[&str] = &["printer", "thermal", "receipt", "pos", "rugtek", "xprinter"];

/* ============================================================
   Helpers
============================================================ */

fn is_system_usb_device(manufacturer: &str, product: &str) -> bool {
    let m = manufacturer.to_lowercase();
    let p = product.to_lowercase();
    system_usb_keywords()
        .iter()
        .any(|k| m.contains(k) || p.contains(k))
}

fn has_printer_interface<T: UsbContext>(device: &rusb::Device<T>) -> bool {
    if let Ok(cfg) = device.active_config_descriptor() {
        for iface in cfg.interfaces() {
            for desc in iface.descriptors() {
                if desc.class_code() == 0x07 {
                    return true;
                }
            }
        }
    }
    false
}

/* ============================================================
   MAIN FUNCTION (same behavior as Python)
============================================================ */

fn list_known_epos_printers(known: bool) -> Vec<Printer> {
    let context = Context::new().expect("USB init failed");
    let devices = context.devices().expect("USB enumeration failed");
    let vendor_map = epos_printers();

    let mut printers = vec![];

    for device in devices.iter() {
        let desc = match device.device_descriptor() {
            Ok(d) => d,
            Err(_) => continue,
        };

        let vid = desc.vendor_id();
        let pid = desc.product_id();

        let is_known_vendor = vendor_map.contains_key(&vid);
        let is_printer_interface = has_printer_interface(&device);

        let mut manufacturer = "Unknown".to_string();
        let mut product = "Unknown".to_string();

        if let Ok(handle) = device.open() {
            manufacturer = handle
                .read_manufacturer_string_ascii(&desc)
                .unwrap_or(manufacturer);
            product = handle.read_product_string_ascii(&desc).unwrap_or(product);
        }

        if is_system_usb_device(&manufacturer, &product) {
            continue;
        }

        let name_combined = format!("{} {}", manufacturer, product).to_lowercase();
        let has_keyword_match = NAME_KEYWORDS.iter().any(|k| name_combined.contains(k));

        // === same skip logic as Python ===
        if known && !is_known_vendor {
            continue;
        } else if known && !(is_known_vendor || is_printer_interface || has_keyword_match) {
            continue;
        }

        let matched_by = if !known {
            "No Filter Applied"
        } else if is_known_vendor {
            "Vendor id"
        } else if is_printer_interface {
            "Interface class"
        } else {
            "Name keyword"
        };

        printers.push(Printer {
            vendor_id: format!("{:04x}", vid),
            product_id: format!("{:04x}", pid),
            manufacturer,
            product,
            vendor_name: vendor_map.get(&vid).unwrap_or(&"Unknown").to_string(),
            matched_by: matched_by.into(),
        });
    }

    printers
}

pub fn list_epos_printers(known: bool) -> Result<Vec<Printer>, String> {
    let printers = list_known_epos_printers(known);

    Ok(printers)
}
