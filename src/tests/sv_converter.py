import flet as ft
import os
import subprocess
import sys


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KCONVARS_PATH = os.path.join(BASE_DIR, 'utils', 'WinOLPC', 'bin', 'kconvars.exe')


def main(page: ft.Page):
    page.title = "Fanuc .sv/.vr Converter"
    page.window.width = 350
    page.window.height = 250
    page.bgcolor = "#F7F7FA"

    result_text = ft.Text(value="", selectable=True, color="black")

    def pick_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            result_text.value = "No file selected."
            page.update()
            return
        file_path = e.files[0].path
        # Convert extension to .sv (lowercase)
        base, ext = os.path.splitext(file_path)
        if ext.upper() == '.SV':
            new_file_path = base + '.sv'
            try:
                os.rename(file_path, new_file_path)
                file_path = new_file_path
            except Exception as ex:
                result_text.value = f"Rename error: {ex}"
                page.update()
                return
        if not file_path.lower().endswith('.sv'):
            result_text.value = "Error: Please select a file with .sv extension."
            page.update()
            return
        out_path = os.path.splitext(file_path)[0] + ".txt"
        try:
            
            print(f"DEBUG: Проверка наличия kconvars.exe по пути: {KCONVARS_PATH}")
            print(f"DEBUG: os.path.isfile(KCONVARS_PATH) = {os.path.isfile(KCONVARS_PATH)}")
            if not os.path.isfile(KCONVARS_PATH):
                result_text.value = f"Error: kconvars.exe not found!\nExpected path: {KCONVARS_PATH}"
                page.update()
                return
            command = [KCONVARS_PATH, file_path, out_path]
            
            result_text.value = f"KCONVARS_PATH: {KCONVARS_PATH}\nfile_path: {file_path}\nout_path: {out_path}\ncommand: {command}"
            page.update()
            
            # Формируем portable PATH только из реально используемых папок Fanuc
            portable_dirs = [
                os.path.join(BASE_DIR, "utils", "WinOLPC", "bin"),
                os.path.join(BASE_DIR, "utils", "ROBOGUIDE", "bin"),
                os.path.join(BASE_DIR, "utils", "Shared", "Utilities"),
            ]
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join(portable_dirs) + os.pathsep + env.get("PATH", "")
            print(f"DEBUG: PATH перед запуском: {env['PATH']}")
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(KCONVARS_PATH),
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            
            if os.path.exists(out_path):
                result_text.value = f"Done! Output: {out_path}"
                os.startfile(out_path)
            else:
                
                alt_out_path = os.path.join(os.path.dirname(KCONVARS_PATH), os.path.basename(out_path))
                if os.path.exists(alt_out_path):
                    result_text.value = f"Done! Output: {alt_out_path}"
                    os.startfile(alt_out_path)
                else:
                    result_text.value = f"Error: {proc.stderr or proc.stdout or 'Failed to create .txt file.'}"
        except Exception as ex:
            result_text.value = f"Execution error: {ex}"
        page.update()

    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    pick_btn = ft.ElevatedButton(
        "Select sysmast.sv file",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
    )

    page.add(
        ft.Column([
            ft.Text("Fanuc .sv/.vr to .txt converter", size=18, weight=ft.FontWeight.BOLD, color="black"),
            pick_btn,
            result_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
