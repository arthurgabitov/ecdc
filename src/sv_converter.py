import flet as ft
import os
import subprocess

KCONVARS_PATH = r"C:\Users\94500062\station-app\ecdc\src\Utils\WinOLPC\bin\kconvars.exe"


def main(page: ft.Page):
    page.title = "Fanuc .sv/.vr Converter"
    page.window_width = 500
    page.window_height = 250
    page.bgcolor = "#F7F7FA"

    result_text = ft.Text(value="", selectable=True)

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
            command = [KCONVARS_PATH, file_path, out_path]
            proc = subprocess.run(command, capture_output=True, text=True)
            va_in_input_dir = out_path
            va_in_kconvars_dir = os.path.join(os.path.dirname(KCONVARS_PATH), os.path.basename(out_path))
            if os.path.exists(va_in_input_dir):
                result_text.value = f"Done! Output: {va_in_input_dir}"
                # Open file after creation
                os.startfile(va_in_input_dir)
            elif os.path.exists(va_in_kconvars_dir):
                result_text.value = f"Done! Output: {va_in_kconvars_dir}"
                os.startfile(va_in_kconvars_dir)
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
            ft.Text("Fanuc .sv/.vr to .txt converter", size=18, weight=ft.FontWeight.BOLD),
            pick_btn,
            result_text
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
