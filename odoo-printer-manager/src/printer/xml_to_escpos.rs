use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use quick_xml::events::Event;
use quick_xml::Reader;
use std::error::Error;

pub fn generate_escpos_from_epos_xml(
    xml_text: &str,
    // printer: &str,
) -> Result<Vec<u8>, Box<dyn Error>> {
    let mut reader = Reader::from_str(xml_text);
    
    reader.trim_text(true);
    
    let mut buf = Vec::new();
    let mut esc: Vec<u8> = vec![0x1b, 0x40]; // ESC @ init

    let mut inside_epos = false;
    let mut current_tag = String::new();
    let mut attributes = std::collections::HashMap::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();

                if tag.ends_with("epos-print") {
                    inside_epos = true;
                }

                if inside_epos {
                    current_tag = tag.clone();
                    attributes.clear();

                    for attr in e.attributes().flatten() {
                        let key = String::from_utf8_lossy(attr.key.as_ref()).to_string();
                        let value = attr.unescape_value()?.to_string();
                        attributes.insert(key, value);
                    }
                }
            }

            Ok(Event::Text(e)) => {
                if !inside_epos {
                    continue;
                }

                let text = e.unescape()?.to_string();
                let tag = current_tag.split('}').last().unwrap_or("");

                match tag {
                    // FEED
                    "feed" => {
                        let lines: usize = attributes
                            .get("line")
                            .unwrap_or(&"1".to_string())
                            .parse()
                            .unwrap_or(1);

                        esc.extend(vec![b'\n'; lines]);
                    }

                    // TEXT
                    "text" => {
                        let align_cmd = match attributes.get("align").map(|s| s.as_str()) {
                            Some("center") => vec![0x1b, 0x61, 0x01],
                            Some("right") => vec![0x1b, 0x61, 0x02],
                            _ => vec![0x1b, 0x61, 0x00],
                        };

                        esc.extend(align_cmd);
                        esc.extend(text.as_bytes());
                        esc.push(b'\n');
                    }

                    // IMAGE
                    "image" => {
                        let raw = BASE64.decode(text.trim())?;

                        let height: usize =
                            attributes.get("height").ok_or("Missing height")?.parse()?;

                        if raw.len() % height != 0 {
                            return Err(
                                format!("Image RAW length mismatch height={}", height).into()
                            );
                        }

                        let width_bytes = raw.len() / height;

                        esc.extend([0x1d, 0x76, 0x30, 0x00]);
                        esc.push((width_bytes & 0xFF) as u8);
                        esc.push((width_bytes >> 8) as u8);
                        esc.push((height & 0xFF) as u8);
                        esc.push((height >> 8) as u8);
                        esc.extend(raw);
                    }

                    _ => {}
                }
            }

            Ok(Event::End(e)) => {
                let tag = String::from_utf8_lossy(e.name().as_ref()).to_string();
                if tag.ends_with("epos-print") {
                    break;
                }
            }

            Ok(Event::Eof) => break,
            Err(e) => return Err(Box::new(e)),
            _ => {}
        }

        buf.clear();
    }

    // CUT
    esc.extend([0x1d, 0x56, 0x00]);

    // Optional: preview async
    // tokio::spawn(send_escpos_preview(esc.clone(), printer.to_string()));

    Ok(esc)
}
