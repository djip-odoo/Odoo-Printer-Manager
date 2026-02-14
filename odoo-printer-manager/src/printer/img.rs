use crate::{printer::print::{direct_network_print, direct_usb_print}};

// const PRINTER_WIDTH_PX_58: u32 = 384;
// const PRINTER_WIDTH_PX_80: u32 = 576;

pub fn usb_print(data: &[u8], vid_str: &str, pid_str: &str) -> Result<(), Box<dyn std::error::Error>> {
    let vid = u16::from_str_radix(vid_str, 16).map_err(|_| "Invalid vendor_id")?;
    let pid = u16::from_str_radix(pid_str, 16).map_err(|_| "Invalid product_id")?;
    // Send to USB printer
    direct_usb_print(data, vid, pid).map_err(|e| format!("{}", e))?;
    Ok(())
}

pub fn nw_print(data: &[u8], ip: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Send to network printer
    direct_network_print(data, ip).map_err(|e| format!("{}", e))?;

    Ok(())
}
