use rusb::{Context, Direction, TransferType, UsbContext};
use std::io::Write;
use std::net::TcpStream;
use std::time::Duration;

/// ================================================================
/// USB Printing (ESC/POS)
/// ================================================================

pub fn direct_usb_print(data: &[u8], vid: u16, pid: u16) -> Result<(), String> {
    let context = Context::new().map_err(|e| e.to_string())?;

    // Open device → THIS IS THE HANDLE
    let handle = context
        .open_device_with_vid_pid(vid, pid)
        .ok_or("USB printer not found")?;

    // Linux: detach kernel driver if needed
    handle.set_auto_detach_kernel_driver(true).ok();

    // Most ESC/POS printers use interface 0
    handle.claim_interface(0).map_err(|e| e.to_string())?;

    // Find BULK OUT endpoint
    let device = handle.device();
    let device_desc = device.device_descriptor().map_err(|e| e.to_string())?;

    let mut out_ep = None;

    for i in 0..device_desc.num_configurations() {
        let config = device.config_descriptor(i).map_err(|e| e.to_string())?;
        for interface in config.interfaces() {
            for iface_desc in interface.descriptors() {
                for ep in iface_desc.endpoint_descriptors() {
                    if ep.direction() == Direction::Out
                        && ep.transfer_type() == TransferType::Bulk
                    {
                        out_ep = Some(ep.address());
                        break;
                    }
                }
            }
        }
    }

    let ep = out_ep.ok_or("No BULK OUT endpoint found")?;

    // Write ESC/POS data
    handle
        .write_bulk(ep, data, Duration::from_secs(5))
        .map_err(|e| e.to_string())?;

    handle.release_interface(0).ok();
    handle.reset().ok();

    Ok(())
}


/// ================================================================
/// Network Printing (ESC/POS over TCP 9100)
/// ================================================================
pub fn direct_network_print(data: &[u8], ip: &str) -> Result<(), String> {
    let mut stream = TcpStream::connect_timeout(
        &format!("{}:9100", ip).parse().unwrap(),
        Duration::from_secs(10),
    )
    .map_err(|e| e.to_string())?;

    stream.write_all(data).map_err(|e| e.to_string())?;

    Ok(())
}
