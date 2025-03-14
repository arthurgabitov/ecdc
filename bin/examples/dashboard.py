import os
import unicodedata
import tkinter as tk
from tkinter import ttk, messagebox, StringVar, Toplevel
import time
import threading
import re
import shutil
from pathlib import Path

class CombinedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Station Timer & SW Tool")
        self.root.configure(bg="#2C2F33", padx=10, pady=10)  # Уменьшенные отступы

        self.timers = []
        self.running_timer = None
        self.colors = {
            'stopped': '#3A3F44',  # Тёмно-серый
            'running': '#2E8B57',  # Морской зелёный
            'paused': '#DAA520',   # Золотистый
            'finished': '#4A4E54'  # Средний серый
        }
        self.source_dir = r"\\LUECHFS101\Shared\European_Customisation\ECDC-Customised Robot SW Order File"
        self.bom_base_dir = r"\\fanuc\FS\Corporate\Products\Data_Sheets_MD"  # Базовая директория для файлов BOM
        self.drive_var = StringVar(self.root)

        self.setup_interface()

        self.running = True
        self.update_thread = threading.Thread(target=self.update_timers_thread, daemon=True)
        self.update_thread.start()
        
        self.auto_update_drives()
        self.root.after(1000, self.auto_update_drives)

    def setup_interface(self):
        self.root.grid_rowconfigure(0, weight=1, minsize=40)  # Уменьшенная минимальная высота
        for i in range(3): self.root.grid_rowconfigure(i + 1, weight=1, minsize=90)  # Уменьшенные ячейки
        self.root.grid_rowconfigure(4, weight=0)  # Строка для версии
        self.root.grid_rowconfigure(5, weight=0)  # Новая строка для Orderfil
        self.root.grid_rowconfigure(6, weight=0)  # Строка для кнопок
        for j in range(2): self.root.grid_columnconfigure(j, weight=3, minsize=200)  # Фиксированная минимальная ширина

        # Настройка стиля кнопок
        style = ttk.Style()
        style.theme_use('clam')
        # Стиль для обычных кнопок
        style.configure("Dark.TButton", background="#50555C", foreground="#E0E0E0", font=("Arial", 9, "bold"),
                        bordercolor="#40444B", relief="raised", padding=4)
        style.map("Dark.TButton", background=[('active', '#60656C')])
        # Стиль для кнопки Reset (красный фон)
        style.configure("Red.TButton", background="#FF4040", foreground="#E0E0E0", font=("Arial", 9, "bold"),
                        bordercolor="#40444B", relief="raised", padding=4)
        style.map("Red.TButton", background=[('active', '#FF6060')])  # Более светлый красный при нажатии
        # Стиль для Combobox
        style.configure("Dark.TCombobox", fieldbackground="#40444B", foreground="#E0E0E0", font=("Arial", 9),
                        background="#40444B")

        # Ячейки (3 строки по 2 ячейки)
        for i in range(3):
            for j in range(2):
                index = i * 2 + j  # Spot 1–6
                frame = tk.Frame(self.root, bg=self.colors['stopped'], bd=2, relief="ridge", highlightbackground="#40444B", highlightthickness=1)
                frame.grid(row=i + 1, column=j, padx=10, pady=5, sticky="nsew")
                frame.grid_columnconfigure(0, weight=1, minsize=140)
                frame.grid_columnconfigure(1, weight=1, minsize=140)
                for r in range(7): frame.grid_rowconfigure(r, weight=1, minsize=15)

                station_label = tk.Label(frame, text=f"Spot {index + 1}", font=("Arial", 11, "bold"), fg="#E0E0E0",
                                        bg=self.colors['stopped'], wraplength=350)
                station_label.grid(row=0, column=0, columnspan=2, pady=4, sticky="nsew")

                wo_label = tk.Label(frame, text="WO", font=("Arial", 9), fg="#E0E0E0",
                                   bg=self.colors['stopped'])
                wo_label.grid(row=1, column=0, padx=4, pady=4, sticky="e")
                wo_entry = tk.Entry(frame, width=14, bg="#40444B", fg="#E0E0E0", insertbackground="#E0E0E0", font=("Arial", 9))
                wo_entry.grid(row=1, column=1, padx=4, pady=4, sticky="w")
                wo_entry.bind("<Return>", lambda event, idx=index: self.check_wo_number(idx))

                timer_label = tk.Label(frame, text="00:00", font=("Arial", 16, "bold"), fg="#E0E0E0",
                                       bg=self.colors['stopped'], width=13, anchor="center")
                timer_label.grid(row=2, column=0, columnspan=2, pady=6, sticky="nsew")

                ttk.Button(frame, text="Start", command=lambda t=index: self.start_timer(t), width=9, style="Dark.TButton").grid(row=3, column=0, columnspan=2, pady=2)
                button_frame = tk.Frame(frame, bg=self.colors['stopped'])
                button_frame.grid(row=4, column=0, columnspan=2, pady=8, sticky="nsew")
                button_frame.grid_columnconfigure(0, weight=1)
                button_frame.grid_columnconfigure(1, weight=1)
                ttk.Button(button_frame, text="Pause", command=lambda t=index: self.pause_timer(t), width=9, style="Dark.TButton").grid(row=0, column=0, padx=4, sticky="ew")
                ttk.Button(button_frame, text="Stop", command=lambda t=index: self.stop_timer(t), width=9, style="Dark.TButton").grid(row=0, column=1, padx=4, sticky="ew")

                sw_frame = tk.Frame(frame, bg=self.colors['stopped'])
                sw_frame.grid(row=5, column=0, columnspan=2, pady=3, sticky="nsew")
                sw_frame.grid_columnconfigure(0, weight=1)
                sw_frame.grid_columnconfigure(1, weight=1)
                sw_frame.grid_columnconfigure(2, weight=1)
                sw_frame.grid_columnconfigure(3, weight=1)

                # Фрейм для кнопок Reset и Find BOM
                reset_bom_frame = tk.Frame(frame, bg=self.colors['stopped'])
                reset_bom_frame.grid(row=6, column=0, columnspan=2, pady=8, sticky="nsew")
                reset_bom_frame.grid_columnconfigure(0, weight=1, minsize=140)
                reset_bom_frame.grid_columnconfigure(1, weight=1, minsize=140)

                # Кнопка Reset с новым стилем (красный фон)
                ttk.Button(reset_bom_frame, text="Reset", command=lambda t=index: self.reset_timer(t), width=9, style="Red.TButton").grid(row=0, column=0, padx=4, sticky="ew")

                self.timers.append({
                    "frame": frame, "label": timer_label, "button_frame": button_frame,
                    "station_label": station_label, "wo_entry": wo_entry, "wo_label": wo_label,
                    "create_sw_btn": None, "find_bom_btn": None, "aoa_folder_btn": None, "drive_combo": None, "sw_frame": sw_frame,
                    "reset_bom_frame": reset_bom_frame,
                    "start_time": None, "elapsed_time": 0, "running": False, "state": "stopped",
                    "wo_number": None, "e_number": None
                })

        # Версия USB
        self.version_label = tk.Label(self.root, text="SW version on disk: Checking...", font=("Arial", 9), fg="#E0E0E0", bg="#2C2F33")
        self.version_label.grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")

        # Новая строка для Orderfil on USB
        self.orderfil_label = tk.Label(self.root, text="Orderfil on USB: Not Found", font=("Arial", 9), fg="#E0E0E0", bg="#2C2F33")
        self.orderfil_label.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")

        # Панель с кнопками внизу
        button_frame = tk.Frame(self.root, bg="#2C2F33")
        button_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Move backups from USB", command=self.backup_usb_folders, width=22, style="Dark.TButton").pack(side=tk.LEFT, padx=6)

    def get_bom_directory(self, e_number):
        """Определяет базовую директорию для BOM файла на основе диапазона E-номера."""
        e_num = int(e_number[1:])
        range_start = (e_num // 1000) * 1000
        range_end = range_start + 999
        range_dir = f"E{range_start:06d}-E{range_end:06d}"
        base_directory = os.path.join(self.bom_base_dir, range_dir)
        dt_directory = os.path.join(base_directory, "DT")
        return dt_directory, base_directory

    def create_aoa_folder(self, index):
        """Создаёт папку на USB в формате WO_номер_E-номер."""
        timer = self.timers[index]
        wo_number = timer.get("wo_number")
        e_number = timer.get("e_number")
        selected_drive = self.drive_var.get()

        if not wo_number or not e_number:
            messagebox.showerror("Error", f"WO number or E-number missing for Spot {index + 1}.")
            return
        
        if not selected_drive:
            messagebox.showerror("Error", "Please select a USB drive.")
            return

        # Формируем имя папки в формате WO_номер_E-номер
        folder_name = f"{wo_number}_{e_number}"
        folder_path = os.path.join(selected_drive, folder_name)

        try:
            os.makedirs(folder_path, exist_ok=True)
            messagebox.showinfo("Success", f"AOA folder created: {folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create AOA folder: {str(e)}")

    def find_bom(self, index):
        """Ищет и открывает BOM файл на основе E-номера."""
        timer = self.timers[index]
        e_number = timer.get("e_number")
        
        if not e_number:
            messagebox.showerror("Error", f"No E-number found for Spot {index + 1}. Please enter a valid WO number first.")
            return
        
        # Получаем обе директории: с DT и без DT
        dt_directory, base_directory = self.get_bom_directory(e_number)
        
        # Сначала проверяем директорию с DT
        bom_file = None
        if os.path.exists(dt_directory):
            for file in os.listdir(dt_directory):
                e_number_with_hyphen = f"E-{e_number[1:]}"
                e_number_without_hyphen = e_number
                if (e_number_with_hyphen in file or e_number_without_hyphen in file) and file.endswith('.xls'):
                    bom_file = os.path.join(dt_directory, file)
                    break
            if bom_file:
                try:
                    os.startfile(bom_file)  # Для Windows
                    return
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open BOM file: {str(e)}")
                    return
            else:
                messagebox.showerror("Error", f"No BOM file found for E-number {e_number} in {dt_directory}.")
                return
        
        # Если DT не существует, ищем в базовой директории
        if not os.path.exists(base_directory):
            messagebox.showerror("Error", f"Directory {base_directory} does not exist.")
            return
        
        for file in os.listdir(base_directory):
            e_number_with_hyphen = f"E-{e_number[1:]}"
            e_number_without_hyphen = e_number
            if (e_number_with_hyphen in file or e_number_without_hyphen in file) and file.endswith('.xls'):
                bom_file = os.path.join(base_directory, file)
                break
        
        if bom_file:
            try:
                os.startfile(bom_file)  # Для Windows
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open BOM file: {str(e)}")
        else:
            messagebox.showerror("Error", f"No BOM file found for E-number {e_number} in {base_directory}.")

    def get_orderfil_e_number(self, selected_drive):
        """Извлекает E-номер из файла orderfil.dat на USB."""
        if not selected_drive:
            return None

        possible_paths = [
            os.path.join(selected_drive, "orderfil.dat"),  # Для V8 и V9
            os.path.join(selected_drive, "config", "p1", "orderfil.dat")  # Для V10
        ]

        for orderfil_path in possible_paths:
            if os.path.isfile(orderfil_path):
                try:
                    with open(orderfil_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        e_number_match = re.search(r'E\d{6}', content)
                        if e_number_match:
                            return e_number_match.group(0)
                except Exception as e:
                    print(f"Error reading orderfil.dat: {str(e)}")
                    return None
        return None

    def backup_usb_folders(self):
        drives = self.get_available_drives()
        if not drives:
            messagebox.showerror("Error", "USB not detected")
            return

        desktop = Path.home() / "Desktop"
        backup_dir = desktop / "backup"
        backup_dir.mkdir(exist_ok=True)

        status_window = Toplevel(self.root)
        status_window.title("Backup Status")
        status_window.configure(bg="#2C2F33")
        status_text = tk.Text(status_window, height=8, width=45, bg="#40444B", fg="#E0E0E0", font=("Arial", 9))
        status_text.pack(padx=6, pady=6)

        pattern = re.compile(r'^\d{8}_E\d{6}$')
        moved_folders = 0

        try:
            for drive in drives:
                status_text.insert(tk.END, f"Scanning {drive}...\n")
                status_text.see(tk.END)
                status_window.update()
                for folder_name in os.listdir(drive):
                    folder_path = os.path.join(drive, folder_name)
                    if os.path.isdir(folder_path) and pattern.match(folder_name):
                        dest_path = os.path.join(backup_dir, folder_name)
                        status_text.insert(tk.END, f"Moving {folder_name}...\n")
                        status_text.see(tk.END)
                        status_window.update()
                        shutil.move(folder_path, dest_path)
                        status_text.insert(tk.END, f"Successfully moved {folder_name} to {dest_path}\n")
                        status_text.see(tk.END)
                        status_window.update()
                        moved_folders += 1
            if moved_folders > 0:
                status_text.insert(tk.END, f"\nMoved {moved_folders} folders to Desktop/backup successfully.\n")
                status_text.see(tk.END)
            else:
                status_text.insert(tk.END, "\nNo matching folders found on any USB drives.\n")
                status_text.see(tk.END)
        except Exception as e:
            status_text.insert(tk.END, f"\nFailed to move folders: {str(e)}\n")
            status_text.see(tk.END)
        finally:
            status_window.update()

    def check_wo_number(self, index):
        timer = self.timers[index]
        wo_number = timer["wo_entry"].get().strip()
        if not wo_number or not wo_number.isdigit() or len(wo_number) != 8:
            messagebox.showerror("Error", f"Spot {index + 1}: Please enter a valid 8-digit WO number.")
            return

        timer["wo_number"] = wo_number
        e_number, robot_model = self.find_e_number(wo_number)
        if e_number:
            timer["e_number"] = e_number
            timer["station_label"].config(text=f"Spot {index + 1} - {e_number} - {robot_model}")
            if not timer["create_sw_btn"] and not timer["drive_combo"] and not timer["find_bom_btn"] and not timer["aoa_folder_btn"]:
                timer["drive_combo"] = ttk.Combobox(timer["sw_frame"], textvariable=self.drive_var, state="readonly", width=9,
                                                    style="Dark.TCombobox")
                timer["drive_combo"].grid(row=0, column=0, padx=4, sticky="ew")
                timer["drive_combo"].bind("<<ComboboxSelected>>", lambda event: self.on_drive_change())
                drives = self.get_available_drives()
                timer["drive_combo"]["values"] = drives
                if drives and (not self.drive_var.get() or self.drive_var.get() in drives):
                    self.drive_var.set(drives[0])

                timer["create_sw_btn"] = ttk.Button(timer["sw_frame"], text="Create SW",
                                                    command=lambda t=index: self.create_sw_for_timer(t), width=9,
                                                    style="Dark.TButton")
                timer["create_sw_btn"].grid(row=0, column=1, padx=4, sticky="ew")

                timer["aoa_folder_btn"] = ttk.Button(timer["sw_frame"], text="AOA Folder",
                                                     command=lambda t=index: self.create_aoa_folder(t), width=9,
                                                     style="Dark.TButton")
                timer["aoa_folder_btn"].grid(row=0, column=2, padx=4, sticky="ew")

                timer["find_bom_btn"] = ttk.Button(timer["reset_bom_frame"], text="Find DT",
                                                   command=lambda t=index: self.find_bom(t), width=9,
                                                   style="Dark.TButton")
                timer["find_bom_btn"].grid(row=0, column=1, padx=4, sticky="ew")
        else:
            messagebox.showerror("Error", f"Spot {index + 1}: No file found for WO {wo_number}.")

    def find_e_number(self, wo_number):
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if wo_number in file and file.endswith('.dat'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith('!STARTING CONFIGURATION : IND.ROBOT'):
                                    e_number_match = re.search(r'E\d{6}', file)
                                    e_number = e_number_match.group(0) if e_number_match else None
                                    robot_model = line.replace('!STARTING CONFIGURATION : IND.ROBOT', '').strip()
                                    return e_number, robot_model
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
        return None, ""

    def create_sw_for_timer(self, index):
        timer = self.timers[index]
        selected_drive = self.drive_var.get()
        if not selected_drive:
            messagebox.showerror("Error", "Please select a USB drive.")
            return
        dest_file_path = self.check_version_file(selected_drive)
        if dest_file_path and timer["wo_number"]:
            self.find_and_copy_file(self.source_dir, dest_file_path, timer["wo_number"])

    def update_timers_thread(self):
        while self.running:
            for index, timer in enumerate(self.timers):
                if timer["running"]:
                    current_time = time.time()
                    elapsed = int(current_time - timer["start_time"] + timer["elapsed_time"])
                    minutes = elapsed // 60
                    seconds = elapsed % 60
                    self.root.after(0, lambda i=index, m=minutes, s=seconds: self.update_display(i, m, s))
            time.sleep(0.1)

    def update_display(self, index, minutes, seconds):
        timer = self.timers[index]
        timer["label"].config(text=f"{minutes:02}:{seconds:02}")
        timer["frame"].config(bg=self.colors['running'])
        timer["station_label"].config(bg=self.colors['running'])
        timer["wo_label"].config(bg=self.colors['running'])
        timer["button_frame"].config(bg=self.colors['running'])
        timer["sw_frame"].config(bg=self.colors['running'])
        timer["reset_bom_frame"].config(bg=self.colors['running'])

    def start_timer(self, index):
        timer = self.timers[index]
        if not timer["running"]:
            timer["running"] = True
            timer["start_time"] = time.time()
            timer["state"] = "running"
            timer["frame"].config(bg=self.colors['running'])
            timer["station_label"].config(bg=self.colors['running'])
            timer["wo_label"].config(bg=self.colors['running'])
            timer["label"].config(bg=self.colors['running'])
            timer["button_frame"].config(bg=self.colors['running'])
            timer["sw_frame"].config(bg=self.colors['running'])
            timer["reset_bom_frame"].config(bg=self.colors['running'])

    def pause_timer(self, index):
        timer = self.timers[index]
        if timer["running"]:
            timer["running"] = False
            current_time = time.time()
            timer["elapsed_time"] += current_time - timer["start_time"]
            timer["start_time"] = None
            minutes = int(timer["elapsed_time"] // 60)
            seconds = int(timer["elapsed_time"] % 60)
            timer["label"].config(text=f"{minutes:02d}:{seconds:02d}")
            timer["state"] = "paused"
            timer["frame"].config(bg=self.colors['paused'])
            timer["station_label"].config(bg=self.colors['paused'])
            timer["wo_label"].config(bg=self.colors['paused'])
            timer["label"].config(bg=self.colors['paused'])
            timer["button_frame"].config(bg=self.colors['paused'])
            timer["sw_frame"].config(bg=self.colors['paused'])
            timer["reset_bom_frame"].config(bg=self.colors['paused'])

    def stop_timer(self, index):
        timer = self.timers[index]
        if timer["running"]:
            current_time = time.time()
            timer["elapsed_time"] += current_time - timer["start_time"]
        timer["running"] = False
        timer["start_time"] = None
        hours_decimal = timer["elapsed_time"] / 3600
        timer["label"].config(text=f"Labor time: {hours_decimal:.2f} h")
        timer["state"] = "finished"
        timer["frame"].config(bg=self.colors['finished'])
        timer["station_label"].config(bg=self.colors['finished'])
        timer["wo_label"].config(bg=self.colors['finished'])
        timer["label"].config(bg=self.colors['finished'])
        timer["button_frame"].config(bg=self.colors['finished'])
        timer["sw_frame"].config(bg=self.colors['finished'])
        timer["reset_bom_frame"].config(bg=self.colors['finished'])

    def reset_timer(self, index):
        timer = self.timers[index]
        timer["running"] = False
        timer["start_time"] = None
        timer["elapsed_time"] = 0
        timer["label"].config(text="00:00")
        timer["state"] = "stopped"
        timer["frame"].config(bg=self.colors['stopped'])
        timer["station_label"].config(bg=self.colors['stopped'])
        timer["wo_label"].config(bg=self.colors['stopped'])
        timer["label"].config(bg=self.colors['stopped'])
        timer["button_frame"].config(bg=self.colors['stopped'])
        timer["sw_frame"].config(bg=self.colors['stopped'])
        timer["reset_bom_frame"].config(bg=self.colors['stopped'])
        timer["wo_entry"].delete(0, tk.END)
        if timer["create_sw_btn"]:
            timer["create_sw_btn"].grid_forget()
            timer["create_sw_btn"] = None
        if timer["find_bom_btn"]:
            timer["find_bom_btn"].grid_forget()
            timer["find_bom_btn"] = None
        if timer["aoa_folder_btn"]:
            timer["aoa_folder_btn"].grid_forget()
            timer["aoa_folder_btn"] = None
        if timer["drive_combo"]:
            timer["drive_combo"].grid_forget()
            timer["drive_combo"] = None
        timer["wo_number"] = None
        timer["e_number"] = None
        timer["station_label"].config(text=f"Spot {index + 1}")

    def normalize_filename(self, filename):
        return unicodedata.normalize('NFC', filename)

    def find_and_copy_file(self, source_dir, dest_file_path, search_term):
        found = False
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if search_term in file and file.endswith('.dat'):
                    source_file_path = os.path.join(root, file)
                    try:
                        with open(source_file_path, 'rb') as source_file:
                            content = source_file.read()
                        decoded_content = content.decode('utf-8', errors='replace')
                        with open(dest_file_path, 'w', encoding='utf-8') as dest_file:
                            dest_file.write(decoded_content)
                        messagebox.showinfo("Result", f"The contents of '{file}' have been copied to '{dest_file_path}'.")
                        found = True
                        break
                    except Exception as e:
                        messagebox.showerror("Error", f"Ошибка при копировании файла {file}:\n{e}")
                        return
            if found:
                break
        if not found:
            messagebox.showerror("Error", "No file with the specified combination was found.")

    def get_available_drives(self):
        return [f"{letter}:\\" for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{letter}:\\") and letter not in ['C', 'J']]

    def check_version_file(self, selected_drive):
        if not selected_drive:
            return None
        version_file_path = os.path.join(selected_drive, "version.txt")
        if os.path.isfile(version_file_path):
            try:
                with open(version_file_path, "r", encoding="utf-8") as file:
                    content = file.read().strip()
                if "V8" in content or "V9" in content:
                    self.version_label.config(text=f"SW version on disk {selected_drive} - {content}")
                    return os.path.join(selected_drive, "orderfil.dat")
                elif "V10" in content:
                    self.version_label.config(text=f"SW version on disk {selected_drive} - {content}")
                    dest_path = os.path.join(selected_drive, "config", "p1", "orderfil.dat")
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    return dest_path
                else:
                    self.version_label.config(text=f"SW version on disk {selected_drive}: Unknown ({content})")
                    return None
            except Exception as e:
                messagebox.showerror("Error", f"Error reading file: {version_file_path}\n{e}")
                return None
        else:
            self.version_label.config(text=f"SW version on disk {selected_drive}: Not Found")
            return None

    def on_drive_change(self):
        self.check_version_file(self.drive_var.get())

    def auto_update_drives(self):
        drives = self.get_available_drives()
        if not drives:
            self.version_label.config(text="No USB detected")
            self.orderfil_label.config(text="Orderfil on USB: No USB detected")
            for timer in self.timers:
                if timer["drive_combo"]:
                    timer["drive_combo"].config(state="disabled")
                    timer["drive_combo"]["values"] = []
        else:
            for timer in self.timers:
                if timer["drive_combo"]:
                    timer["drive_combo"].config(state="normal")
                    timer["drive_combo"]["values"] = drives
                    if not self.drive_var.get() or self.drive_var.get() not in drives:
                        self.drive_var.set(drives[0])
            current_drive = self.drive_var.get() if self.drive_var.get() in drives else drives[0] if drives else None
            if current_drive:
                self.check_version_file(current_drive)
                e_number = self.get_orderfil_e_number(current_drive)
                if e_number:
                    self.orderfil_label.config(text=f"Orderfil on USB - {e_number}")
                else:
                    self.orderfil_label.config(text="Orderfil on USB: Not Found")
            else:
                self.orderfil_label.config(text="Orderfil on USB: No USB detected")
        self.root.after(1000, self.auto_update_drives)

    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Dark.TButton", background="#50555C", foreground="#E0E0E0", font=("Arial", 9, "bold"), 
                    bordercolor="#40444B", relief="raised", padding=4)
    style.map("Dark.TButton", background=[('active', '#60656C')])
    style.configure("Dark.TCombobox", fieldbackground="#40444B", foreground="#E0E0E0", font=("Arial", 9), 
                    background="#40444B")
    app = CombinedApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()