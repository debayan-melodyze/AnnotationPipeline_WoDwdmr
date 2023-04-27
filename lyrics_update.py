import json
from config import firebase_config
from io import FireBase

class LyricsUpdate:
    def __init__(self, annotator_id):
        self.annotator_id = annotator_id
        self.temp_lyrics_path = "Annotator_Temp\\" + annotator_id + "\\temp_lyrics.json"
        self.fb = FireBase(firebase_config)

    # Read lyrics in original tempo from local path
    # Create new lyrics for new tempo - update lyrics
    # Store updated lyrics into firebase storage
    def store_updated_lyrics_from_local(self, original_lyrics_path, user_tempo, song_id, song_name):
        lyrics = self.read_lyrics_from_local(original_lyrics_path)
        updated_lyrics = lyrics
        new_lyrics_path = self.insert_lyrics_into_storage(updated_lyrics, song_id, song_name, user_tempo)
        return new_lyrics_path, updated_lyrics

    # Read lyrics in original tempo from firebase storage
    # Create new lyrics for new tempo - update lyrics
    # Store updated lyrics into firebase storage
    def store_updated_lyrics_from_storage(self, original_lyrics_path, original_tempo, user_tempo, song_id, song_name):
        lyrics = self.read_lyrics_from_storage(original_lyrics_path)
        updated_lyrics = self.update_lyrics(lyrics, original_tempo, user_tempo)
        new_lyrics_path = self.insert_lyrics_into_storage(updated_lyrics, song_id, song_name, user_tempo)
        return new_lyrics_path, updated_lyrics

    def read_lyrics_from_local(self, original_lyrics_path):
        with open(original_lyrics_path, 'rb') as handle:
            lyrics = json.load(handle)
        return lyrics

    def read_lyrics_from_storage(self, original_lyrics_path):
        self.fb.storage.child(original_lyrics_path).download(original_lyrics_path, self.temp_lyrics_path)
        with open(self.temp_lyrics_path, 'rb') as handle:
            lyrics = json.load(handle)
        return lyrics

    def insert_lyrics_into_storage(self, updated_lyrics, song_id, song_name, user_tempo):
        file_name = "_".join([song_id, song_name, str(user_tempo)]) + ".json"
        file_path = "Lyrics/" + file_name
        with open(self.temp_lyrics_path, "w") as handle:
            json.dump(updated_lyrics, handle)
        self.fb.storage.child(file_path).put(self.temp_lyrics_path)
        return file_path

    def update_lyrics(self, lyrics, original_tempo, user_tempo):
        updated_lyrics = lyrics

        factor = float(original_tempo) / float(user_tempo)
        for index, line in enumerate(lyrics["lyrics"]["data"]):
            updated_start_time = self.convert_time_to_seconds(lyrics["lyrics"]["data"][index]["start_time"])*factor
            updated_end_time = self.convert_time_to_seconds(lyrics["lyrics"]["data"][index]["end_time"])*factor
            updated_lyrics["lyrics"]["data"][index]["start_time"] = self.convert_seconds_to_time(updated_start_time)
            updated_lyrics["lyrics"]["data"][index]["end_time"] = self.convert_seconds_to_time(updated_end_time)
        updated_lyrics["tempo"] = user_tempo

        return updated_lyrics

    def convert_time_to_seconds(self, time):
        return float(time.split(":")[0])*60 + float(time.split(":")[1])

    def convert_seconds_to_time(self, seconds):
        seconds = int(round(seconds))
        return str(seconds // 60) + ":" + str(seconds % 60)


