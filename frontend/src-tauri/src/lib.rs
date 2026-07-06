use tauri_plugin_shell::ShellExt;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      let sidecar = app.shell().sidecar("python-backend");
      match sidecar {
        Ok(cmd) => {
          match cmd.spawn() {
            Ok((_rx, _child)) => log::info!("后端 sidecar 已启动"),
            Err(e) => log::warn!("后端 sidecar 启动失败 (开发模式?): {}", e),
          }
        }
        Err(e) => log::warn!("后端 sidecar 二进制未找到: {}", e),
      }

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
