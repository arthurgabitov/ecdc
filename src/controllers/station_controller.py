from src.models.station import Station
from config import Config
import time
import json
import os
import flet as ft

STATE_FILE = "timers_state.json"

class StationController:
    def __init__(self):
        self.config = Config()
        self.app_settings = self.config.get_app_settings()
        self.stations_count = self.app_settings["stations_count"]

        self.stations = {
            i + 1: Station(id=i + 1, spots=self._generate_spots(i + 1))
            for i in range(self.stations_count)
        }
        self.users = {}
        self.load_states()  # Загружаем состояния при старте

    def _generate_spots(self, station_id):
        spots_count = self.app_settings["spots"]
        return {
            (station_id * 100 + j + 1): {
                "status": "idle",
                "timer": 0,  # Это будет elapsed_time в секундах
                "wo_number": None,
                "running": False,
                "start_time": 0  # Время начала для активного таймера
            }
            for j in range(spots_count)
        }

    def get_stations(self):
        return list(self.stations.keys())

    def get_station_by_id(self, station_id):
        return self.stations.get(station_id)

    def get_spots_count(self):
        return sum(len(station.spots) for station in self.stations.values())

    def get_spot_data(self, station_id, spot_id):
        station = self.get_station_by_id(station_id)
        return station.spots.get(spot_id) if station else None

    def update_spot_status(self, station_id, spot_id, status, timer=None, wo_number=None):
        station = self.get_station_by_id(station_id)
        if station and spot_id in station.spots:
            spot = station.spots[spot_id]
            spot.update({
                "status": status,
                "timer": timer if timer is not None else spot["timer"],
                "wo_number": wo_number if wo_number is not None else spot["wo_number"],
            })
            self.save_states()

    # Методы для управления таймером
    def start_timer(self, station_id, spot_id):
        spot = self.get_spot_data(station_id, spot_id)
        if spot and not spot["running"]:
            spot["running"] = True
            spot["start_time"] = time.time()
            self.save_states()

    def pause_timer(self, station_id, spot_id):
        spot = self.get_spot_data(station_id, spot_id)
        if spot and spot["running"]:
            spot["running"] = False
            spot["timer"] += time.time() - spot["start_time"]
            spot["start_time"] = 0
            self.save_states()

    def stop_timer(self, station_id, spot_id):
        spot = self.get_spot_data(station_id, spot_id)
        if spot:
            if spot["running"]:
                spot["timer"] += time.time() - spot["start_time"]
            spot["running"] = False
            spot["start_time"] = 0
            spot["timer"] = 0  # Сбрасываем время
            self.save_states()

    def get_timer_value(self, station_id, spot_id):
        spot = self.get_spot_data(station_id, spot_id)
        if spot:
            if spot["running"]:
                return spot["timer"] + (time.time() - spot["start_time"])
            return spot["timer"]
        return 0

    # Сохранение и загрузка состояния
    def load_states(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                states = json.load(f)
                for station_id, station_data in states.items():
                    station = self.get_station_by_id(int(station_id))
                    if station:
                        for spot_id, spot_data in station_data["spots"].items():
                            station.spots[int(spot_id)].update(spot_data)

    def save_states(self):
        states = {
            str(station_id): {"spots": station.spots}
            for station_id, station in self.stations.items()
        }
        with open(STATE_FILE, "w") as f:
            json.dump(states, f)