// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

pub fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}
