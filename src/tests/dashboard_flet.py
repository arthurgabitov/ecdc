import flet as ft
import requests
import re
import os

BASE_URL = "http://luechecdc98.fanuc.local:8443"
REST_URL = f"{BASE_URL}/rest"

class ECDCClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.user = None
        self.users = []
    def login(self, sso_obj, password):
        root_url = f"{BASE_URL}/"
        pre = self.session.get(root_url)
        match = re.search(r"id=\"setupAppVars\"[^>]*data-csrftoken='([^']+)'", pre.text)
        csrf_token = match.group(1) if match else None
        self.csrf_token = csrf_token
        pre_users = self.session.get(f"{REST_URL}/users")
        headers = {}
        if csrf_token:
            headers['x-csrf-token'] = csrf_token
        payload = dict(sso_obj)
        payload['password'] = password
        resp = self.session.post(f"{REST_URL}/login", json=payload, headers=headers)
        if resp.status_code == 200:
            self.user = resp.json()
            post_login = self.session.get(root_url)
            match2 = re.search(r"id=\"setupAppVars\"[^>]*data-csrftoken='([^']+)'", post_login.text)
            new_csrf_token = match2.group(1) if match2 else None
            if new_csrf_token:
                self.csrf_token = new_csrf_token
            return True
        else:
            return False
    def get_users(self):
        resp = self.session.get(f"{REST_URL}/users")
        if resp.status_code == 200:
            self.users = resp.json()
            return self.users
        else:
            return []
    def get_work_orders(self, sso):
        resp = self.session.get(f"{REST_URL}/works", params={"sso": sso})
        if resp.status_code == 200:
            return resp.json()
        else:
            return []
    def update_status(self, payload):
        url = f"{REST_URL}/operator-status"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*'
        }
        if hasattr(self, 'csrf_token') and self.csrf_token:
            headers['x-csrf-token'] = self.csrf_token
        resp = self.session.put(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return True
        resp.raise_for_status()
        return False
    def get_station_status(self, station):
        url = f"{REST_URL}/station"
        params = {"station": str(station)}
        resp = self.session.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {}

def main(page: ft.Page):
    page.title = "ECDC Dashboard (Flet)"
    client = ECDCClient()
    def show_login():
        users = client.get_users()
        sso_options = [f"{u['sso']} ({u['role']})" for u in users]
        try:
            current_user = os.getlogin()
        except Exception:
            current_user = os.environ.get("USERNAME", "")
        default_idx = 0
        for idx, u in enumerate(users):
            if u['sso'].lower() == current_user.lower():
                default_idx = idx
                break
        sso_dd = ft.Dropdown(options=[ft.dropdown.Option(opt) for opt in sso_options], width=300, value=sso_options[default_idx] if sso_options else None)
        agree_chk = ft.Checkbox(label="Agree to Terms", value=True)
        login_btn = ft.ElevatedButton("Login")
        msg = ft.Text(visible=False)
        def do_login(e):
            selected_value = sso_dd.value
            if not selected_value or selected_value not in sso_options:
                msg.value = "Select user"
                msg.visible = True
                page.update()
                return
            idx = sso_options.index(selected_value)
            user = users[idx]
            sso_obj = {"sso": user['sso'], "role": user['role'], "agree": 1}
            password = "" if user['sso'] == "FXX_USER" else "FanucECDC22!"
            if not agree_chk.value:
                msg.value = "You must agree to the terms."
                msg.visible = True
                page.update()
                return
            if client.login(sso_obj, password):
                show_dashboard(selected_value)
            else:
                msg.value = "Login failed"
                msg.visible = True
                page.update()
        login_btn.on_click = do_login
        page.clean()
        page.add(
            ft.Column([
                ft.Text("ECDC Dashboard Login", size=24),
                sso_dd,
                agree_chk,
                login_btn,
                msg
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()
        if sso_dd.value and agree_chk.value:
            do_login(None)
    def show_dashboard(selected_user=None):
        users = client.get_users()
        user_options = [f"{u['sso']} ({u['role']})" for u in users]
        default_idx = 0
        if selected_user and selected_user in user_options:
            default_idx = user_options.index(selected_user)
        user_dd = ft.Dropdown(options=[ft.dropdown.Option(opt) for opt in user_options], width=300, value=user_options[default_idx] if user_options else None)
        station_options = [ft.dropdown.Option(str(i)) for i in range(1, 31)]
        station_inp = ft.Dropdown(label="Station", options=station_options, value="25", width=100)
        status_btn = ft.ElevatedButton("Load Station Status")
        change_status_btn = ft.ElevatedButton("Change Status")
        snackbar_text = ft.Text(visible=False)
        dialog_container = ft.Container(visible=False)
        def show_snackbar(message):
            snackbar_text.value = message
            snackbar_text.visible = True
            page.update()
            import threading
            def hide():
                import time
                time.sleep(2)
                snackbar_text.visible = False
                page.update()
            threading.Thread(target=hide, daemon=True).start()
        def change_status(e):
            rows = table.rows or []
            if not rows:
                msg.value = "No spot data for the selected station"
                msg.visible = True
                page.update()
                return
            spots = []
            for row in rows:
                cell = row.cells[1].content
                spot_val = getattr(cell, 'value', None)
                if spot_val:
                    spots.append(spot_val)
            if not spots:
                msg.value = "No spots available"
                msg.visible = True
                page.update()
                return
            spot_dd = ft.Dropdown(label="Spot", options=[ft.dropdown.Option(str(s)) for s in spots], width=150)
            status_inp = ft.TextField(label="New Status", width=150)
            dialog_msg = ft.Text(visible=False)
            def on_submit(ev):
                spot = spot_dd.value
                new_status = status_inp.value
                if not spot or not new_status or not new_status.isdigit():
                    dialog_msg.value = "Enter valid spot and status"
                    dialog_msg.visible = True
                    page.update()
                    return
                wo = None
                for row in rows:
                    cell = row.cells[1].content
                    spot_val = getattr(cell, 'value', None)
                    if spot_val == spot:
                        wo = {
                            'station': getattr(row.cells[0].content, 'value', None),
                            'spot': getattr(row.cells[1].content, 'value', None),
                            'status': getattr(row.cells[2].content, 'value', None),
                            'enumber': getattr(row.cells[3].content, 'value', None),
                            'work_order': getattr(row.cells[4].content, 'value', None)
                        }
                        break
                if not wo:
                    dialog_msg.value = f"Spot {spot} not found"
                    dialog_msg.visible = True
                    page.update()
                    return
                spot_int = 0
                try:
                    spot_int = int(wo.get('spot', 0) or 0)
                except Exception:
                    spot_int = 0
                payload = {
                    "type": 0,
                    "station": str(wo.get('station', station_inp.value or "25")),
                    "spot": spot_int,
                    "status": str(new_status),
                    "enumber": str(wo.get('enumber', '')),
                    "work_order": str(wo.get('work_order', '')),
                    "device": 1,
                    "device_model": "N/A",
                    "priority": 0,
                    "comment": None,
                    "enumbernew": None
                }
                if client.update_status(payload):
                    dialog_container.visible = False
                    page.update()
                    show_snackbar(f"Status for spot {spot} updated.")
                    load_station_status(None)
                else:
                    dialog_msg.value = f"Failed to update status for spot {spot}."
                    dialog_msg.visible = True
                    page.update()
            def on_cancel(ev):
                dialog_container.visible = False
                page.update()
            dialog_container.content = ft.Card(
                ft.Container(
                    ft.Column([
                        ft.Text("Change Status", size=20),
                        spot_dd,
                        status_inp,
                        dialog_msg,
                        ft.Row([
                            ft.ElevatedButton("OK", on_click=on_submit),
                            ft.ElevatedButton("Cancel", on_click=on_cancel)
                        ])
                    ], tight=True),
                    padding=20,
                    bgcolor="white",
                    border_radius=10,
                    alignment=ft.alignment.center,
                    width=350
                )
            )
            dialog_container.visible = True
            page.update()
        change_status_btn.on_click = change_status
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("station")),
                ft.DataColumn(ft.Text("spot")),
                ft.DataColumn(ft.Text("status")),
                ft.DataColumn(ft.Text("enumber")),
                ft.DataColumn(ft.Text("work_order")),
            ],
            rows=[]
        )
        msg = ft.Text(visible=False)
        def load_station_status(e):
            station = station_inp.value or ""
            station = station.strip() if isinstance(station, str) else ""
            if not station.isdigit():
                msg.value = "Enter a valid station number"
                msg.visible = True
                page.update()
                return
            status_data = client.get_station_status(int(station))
            table.rows = []
            for spot, info in status_data.items():
                if info:
                    table.rows.append(ft.DataRow([
                        ft.DataCell(ft.Text(str(info.get('station', station)))),
                        ft.DataCell(ft.Text(str(info.get('spot', spot)))),
                        ft.DataCell(ft.Text(str(info.get('status', '')))),
                        ft.DataCell(ft.Text(str(info.get('enumber', '')))),
                        ft.DataCell(ft.Text(str(info.get('work_order', '')))),
                    ]))
                else:
                    table.rows.append(ft.DataRow([
                        ft.DataCell(ft.Text(str(station))),
                        ft.DataCell(ft.Text(str(spot))),
                        ft.DataCell(ft.Text('')),
                        ft.DataCell(ft.Text('')),
                        ft.DataCell(ft.Text('')),
                    ]))
            msg.visible = False
            page.update()
        status_btn.on_click = load_station_status
        page.clean()
        page.add(
            ft.Stack([
                ft.Column([
                    ft.Text("Dashboard", size=24),
                    ft.Row([user_dd, station_inp, status_btn, change_status_btn]),
                    table,
                    msg,
                    snackbar_text
                ]),
                dialog_container
            ])
        )
        page.update()
    show_login()
ft.app(target=main)