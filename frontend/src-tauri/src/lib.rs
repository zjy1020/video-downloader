use std::sync::Mutex;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

struct SidecarState(Mutex<Option<CommandChild>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  let app = tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .plugin(tauri_plugin_dialog::init())
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
        Ok(cmd) => match cmd.spawn() {
          Ok((_rx, child)) => {
            log::info!("后端 sidecar 已启动");
            app.manage(SidecarState(Mutex::new(Some(child))));
          }
          Err(e) => log::warn!("后端 sidecar 启动失败 (开发模式?): {}", e),
        },
        Err(e) => log::warn!("后端 sidecar 二进制未找到: {}", e),
      }

      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application");

  app.run(|app_handle, event| {
    if let tauri::RunEvent::Exit = event {
      if let Some(state) = app_handle.try_state::<SidecarState>() {
        if let Ok(mut guard) = state.0.lock() {
          if let Some(child) = guard.take() {
            let _ = child.kill();
          }
        }
      }
    }
  });
}
