class Station:
    def __init__(self, id, name="Station", status="Offline", spots=None):
        self.id = id  
        self.name = f"{name} {id}" 
        self.status = status
        # Инициализируем spots, если они переданы, иначе пустой словарь
        self.spots = spots if spots is not None else {}

    def update_status(self, new_status):
        self.status = new_status

    def __str__(self):
        return f"{self.name}: {self.status}"