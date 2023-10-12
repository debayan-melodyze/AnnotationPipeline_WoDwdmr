import pyrebase

class FireBase:
    def __init__(self, firebase_config):
        self.db_config = pyrebase.initialize_app(firebase_config)
        self.auth = self.db_config.auth()
        self.db = self.db_config.database()
        self.storage = self.db_config.storage()

    def read_from_db(self, firebase_db_path):
        return self.db.child(firebase_db_path).get()

    def write_to_db(self):
        return None

    def read_from_storage(self, firebase_storage_path, local_path):
        self.storage.child(firebase_storage_path.download(firebase_storage_path, local_path))

    def write_to_storage(self):
        return None