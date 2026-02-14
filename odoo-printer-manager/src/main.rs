mod libusb;
mod logger;
mod printer;

use logger::log;
use printer::{
    img::{nw_print, usb_print},
    list::list_epos_printers,
    xml_to_escpos::generate_escpos_from_epos_xml,
};

use crate::printer::list::Printer;
use axum::{
    extract::Path,
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::trace::TraceLayer;

use tower_http::cors::{Any, CorsLayer};

fn xml_error(code: &str, msg: &str) -> Response<String> {
    let body = format!(
        r#"<response success='false' code='{}'>{}</response>"#,
        code, msg
    );

    Response::builder()
        .status(StatusCode::BAD_REQUEST)
        .header("Content-Type", "text/xml; charset=utf-8")
        .body(body)
        .unwrap()
}

fn xml_success() -> Response<String> {
    let body = format!(r#"<response success='true' code=''></response>"#);

    Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/xml; charset=utf-8")
        .body(body)
        .unwrap()
}

/// ================================================================
/// Command Handler
/// ================================================================

async fn usb_route(Path((vid, pid)): Path<(String, String)>, body: String) -> impl IntoResponse {
    match generate_escpos_from_epos_xml(&body) {
        Ok(esc) => match usb_print(&esc, &vid, &pid) {
            Ok(_) => xml_success(),
            Err(e) => xml_error("USB_ERROR", &e.to_string()),
        },
        Err(e) => xml_error("PARSE_ERROR", &e.to_string()),
    }
}

async fn ip_route(Path(ip): Path<String>, body: String) -> impl IntoResponse {
    match generate_escpos_from_epos_xml(&body) {
        Ok(esc) => match nw_print(&esc, &ip) {
            Ok(_) => xml_success(),
            Err(e) => xml_error("NETWORK_ERROR", &e.to_string()),
        },
        Err(e) => xml_error("PARSE_ERROR", &e.to_string()),
    }
}

#[derive(Serialize)]
struct PrinterResponse {
    status: String,
    message: Vec<Printer>,
}

async fn printer_list() -> impl IntoResponse {
    match list_epos_printers(true) {
        Ok(printers) => Json(PrinterResponse {
            status: "success".to_string(),
            message: printers,
        })
        .into_response(),

        Err(_e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(PrinterResponse {
                status: "error".to_string(),
                message: vec![],
            }),
        )
            .into_response(),
    }
}

/// ================================================================
/// Main Entry
/// ================================================================

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().init();

    let cors = CorsLayer::new()
        .allow_origin(Any) // Allow all origins
        .allow_methods(Any) // Allow GET, POST, etc.
        .allow_headers(Any);

    let app = Router::new()
        .route(
            "/vid/:vid/pid/:pid/cgi-bin/epos/service.cgi",
            post(usb_route),
        )
        .route("/ip/:ip/cgi-bin/epos/service.cgi", post(ip_route))
        .route("/success/cgi-bin/epos/service.cgi", post(|| async { xml_success() }))
        .route("/printer-list", get(printer_list))
        .route("/", get(|| async { "Odoo printer manager is running...!" }))
        .layer(TraceLayer::new_for_http())
        .layer(cors);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8089));
    log(&format!("Server running on {}", addr));

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}
