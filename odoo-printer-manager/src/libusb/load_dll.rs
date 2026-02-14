#[cfg(target_os = "windows")]
pub fn add_libusb_dll_directory() {
    use std::ffi::OsStr;
    use std::iter::once;
    use std::os::windows::ffi::OsStrExt;

    extern "system" {
        fn SetDllDirectoryW(lpPathName: *const u16) -> i32;
    }

    // Detect EXE architecture at compile time
    let arch_dir = if cfg!(target_pointer_width = "64") {
        "x64"
    } else {
        "x86"
    };

    let dll_dir = std::env::current_exe()
        .unwrap()
        .parent()
        .unwrap()
        .join("libusb")
        .join(arch_dir);

    let wide: Vec<u16> = OsStr::new(&dll_dir)
        .encode_wide()
        .chain(once(0))
        .collect();

    unsafe {
        if SetDllDirectoryW(wide.as_ptr()) == 0 {
            eprintln!("[ERROR] Failed to set DLL directory");
        } else {
            eprintln!("[INFO] Using libusb DLL from {:?}", dll_dir);
        }
    }
}
