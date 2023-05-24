from config import firebase_config
from lyrics_update import LyricsUpdate
from inout import FireBase
from datetime import datetime
from os import listdir
from os.path import isfile, join
import os
import shutil
import sox


class InsertNewAnnotationIntoDB_WoDwdmr:

    def __init__(self, genre_image_path,
                 song_name, language, category, thumbnail_path, singer, lyricist, composer, producer,
                 annotator_ID, lyrics_json_path, genre, tempo, scale, multiscale_audio_path, daw_project_path, daw_name):
        self.fb = FireBase(firebase_config)
        self.genre_image_path = genre_image_path
        self.song_name = song_name
        self.language = language
        self.category = category
        self.thumbnail_path = thumbnail_path
        self.singer = singer
        self.lyricist = lyricist
        self.composer = composer
        self.producer = producer
        self.annotator_ID = annotator_ID
        self.lyrics_json_path = lyrics_json_path
        self.genre = genre
        self.tempo = tempo
        self.scale = scale
        self.tempo_list = [int(tempo) + i for i in range(-10, 11, 5) if i != 0]
        self.tempo_list.insert(0, int(tempo))
        self.multiscale_audio_path = multiscale_audio_path
        self.daw_project_path = daw_project_path
        self.daw_name = daw_name
        self.lyrics_utils = LyricsUpdate(annotator_ID)
        self.temp_tempo_changed_audio_file = "Annotator_Temp\\" + annotator_ID + "\\temp_audio.mp3"
        if not os.path.exists("Annotator_Temp\\" + annotator_ID):
            os.makedirs("Annotator_Temp\\" + annotator_ID)

    def remove_temp_files(self):
        if os.name == 'nt':
            shutil.rmtree("Annotator_Temp\\" + self.annotator_ID, ignore_errors=True)
        else:
            shutil.rmtree("Annotator_Temp/" + self.annotator_ID, ignore_errors=True)

    def route(self):
        self.insert_new_language()
        self.insert_new_category()
        self.insert_new_BGM_filter()
        self.insert_new_tempo()
        project_file_location_storage = self.upload_project_file(self.daw_project_path, self.song_name,
                                                                 self.genre, self.tempo, self.scale)
        song_id = ''
        scale_vs_audio_file = self.read_all_scale_audio_files()
        version_no = 0
        for scale in scale_vs_audio_file.keys():
            if ".mp3" not in scale:
                continue
            original_audio_file = scale_vs_audio_file[scale]
            scale = scale.split(".")[0]
            original_tempo = int(self.tempo)
            for tempo in self.tempo_list:
                # create transformer
                tfm = sox.Transformer()
                tempo_factor = tempo / original_tempo
                tfm.tempo(tempo_factor)
                tfm.build_file(original_audio_file, self.temp_tempo_changed_audio_file)

                song_id, is_Existing = self.get_song_id()
                annotation_id = self.insert_new_annotation_DB(song_id, is_Existing, self.temp_tempo_changed_audio_file,
                                                              scale, str(tempo), self.genre, project_file_location_storage,
                                                              self.daw_name, version_no)
                version_no = version_no + 1
                self.insert_new_song_genre_list(song_id)
                self.insert_new_song_tempo_list(song_id)
                self.insert_new_song_scale_list(song_id)
                self.insert_new_genre_tempo_list(song_id)


        self.remove_temp_files()
        return song_id

    def read_all_scale_audio_files(self):
        audio_file_names_vs_path_dict = {f:join(self.multiscale_audio_path, f) for f in listdir(self.multiscale_audio_path) if
                             isfile(join(self.multiscale_audio_path, f))}
        return audio_file_names_vs_path_dict

    def insert_new_genre_tempo_list(self, song_id):
            self.fb.db.child("Song_Genre_With_Tempo").child(song_id).child(self.genre).child(
                self.tempo).set("")

    def upload_audio_file(self, local_audio_file_path, song_id, annotated_song_id_version_id, genre, tempo, scale):
        audio_name = "_".join([song_id, annotated_song_id_version_id, genre, str(tempo), scale])
        audio_path_mp3 = "Audio/Background/" + audio_name + ".mp3"
        self.fb.storage.child(audio_path_mp3).put(local_audio_file_path)
        return audio_path_mp3

    def upload_project_file(self, project_path, song_name, genre, tempo, scale):
        file_name = "_".join([song_name, genre, str(tempo), scale])
        file_ext = project_path.split(".")[-1]
        file_full_location_storage = "DawProjects/" + file_name + "." + file_ext
        self.fb.storage.child(file_full_location_storage).put(project_path)
        return file_full_location_storage

    def insert_new_annotation_DB(self, song_id, is_Song_Existing, local_audio_file, scale, tempo, genre,
                                 project_file_location_storage, daw_name, version_no):

        is_genre_existing = False
        if is_Song_Existing is True:
            existing_song_annotation = self.fb.db.child("Annotated_Song").order_by_child("master_song_id").equal_to(song_id).get()
            highest_annotation_no = 0
            lyrics_in_db_in_exact_user_tempo_genre_flag = False

            db_tempo = None
            db_lyrics_path = None

            for annotation in existing_song_annotation:
                annotation_val = annotation.val()
                annotation_id = annotation_val["annotated_song_id"]
                annotation_id_no = int(annotation_id.split("_")[3])
                if annotation_id_no > highest_annotation_no:
                    highest_annotation_no = annotation_id_no

                if lyrics_in_db_in_exact_user_tempo_genre_flag is False:
                    db_tempo = int(annotation_val["master_tempo"])
                    db_genre = annotation_val["master_genre"]
                    if db_genre == genre:
                        is_genre_existing = True
                        new_annotation_no = annotation_id_no
                    if db_tempo is int(tempo) and db_genre == genre:
                        lyrics_in_db_in_exact_user_tempo_genre_flag = True
                        db_lyrics_path = annotation_val["lyrics_with_timeline_file_location"]

            if not is_genre_existing:
                new_annotation_no = highest_annotation_no + 1

            new_song_annotation_id = song_id + "_annotation_" + str(new_annotation_no)

            if lyrics_in_db_in_exact_user_tempo_genre_flag is True:
                new_lyrics_file = db_lyrics_path
            else:
                # self.tempo is the root tempo in which manual lyrics file is provided
                # tempo is the current tempo
                new_lyrics_file, new_lyrics = self.lyrics_utils.store_updated_lyrics_from_local(self.lyrics_json_path, self.tempo, tempo, song_id, self.song_name, genre)
        else:
            new_song_annotation_id = song_id + "_annotation_1"
            new_lyrics_file = "Lyrics/" + "_".join([song_id, self.song_name, self.tempo, self.genre]) + ".json"
            self.fb.storage.child(new_lyrics_file).put(self.lyrics_json_path)

        aud_storage_path = self.upload_audio_file(local_audio_file, song_id, new_song_annotation_id + "_v_" + str(version_no), self.genre,
                               tempo, scale)


        now = datetime.now()
        data = {"annotated_song_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                "annotated_song_file_path": aud_storage_path,
                "annotated_song_id": new_song_annotation_id,
                "annotated_song_id_version_id": new_song_annotation_id + "_v_" + str(version_no),
                "annotated_song_status": "active",
                "lyrics_with_timeline_file_location": new_lyrics_file,
                "master_annotator_id": self.annotator_ID,
                "master_genre": genre,
                "master_scale": scale,
                "master_song_id": song_id,
                "master_song_id_genre_scale_tempo": "_".join([song_id, genre, scale, str(tempo)]),
                "master_song_id_scale_tempo": "_".join([song_id, scale, str(tempo)]),
                "master_song_id_genre_version": "_".join([song_id, genre, "v_" + str(version_no)]),
                "master_tempo": tempo,
                "version_id": "v_" + str(version_no),
                "project_file_location_storage": project_file_location_storage,
                "daw_name": daw_name}
        self.fb.db.child("Annotated_Song").child(new_song_annotation_id + "_v_" + str(version_no)).set(data)
        return new_song_annotation_id





    def get_song_id(self):
        song_id = self.get_existing_song_ID()
        if song_id is not None:
            return song_id, True
        song_id = self.insert_new_song_DB()
        self.check_required_input_new_song()
        return song_id, False

    def get_existing_song_ID(self):
        existing_song = self.fb.db.child("Song_Master").order_by_child("song_name").equal_to(self.song_name).get()
        if len(existing_song.val()) > 0:
            existing_song_val = existing_song[0].val()
            existing_song_id = existing_song_val["song_id"]
            return existing_song_id
        return None

    def check_required_input_new_song(self):
        if self.category == "":
            print("MISSING: Category for new song")
        if self.language == "":
            print("MISSING: Language for new song")
        if self.song_name == "":
            print("MISSING: Song Name for new song")
        if self.thumbnail_path == "":
            print("MISSING: Thumbnail for new song")


    def insert_new_song_DB(self):
        existing_all_songs = self.fb.db.child("Song_Master").get()
        highest_song_id_no = 0
        for song in existing_all_songs:
            song_val = song.val()
            song_id = song_val["song_id"]
            song_id_no = int(song_id.split("_")[1])
            if song_id_no > highest_song_id_no:
                highest_song_id_no = song_id_no
        new_song_id_no = highest_song_id_no + 1
        new_song_id = "song_" + str(new_song_id_no)

        new_thumbnail_path = "Image/Song/Thumbnail/" + self.song_name
        self.fb.storage.child(new_thumbnail_path).put(self.thumbnail_path)

        self.check_required_input_new_song()

        now = datetime.now()
        data = {"master_song_category": self.category,
                "master_song_language": self.language,
                "song_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                "song_id": new_song_id,
                "song_name": self.song_name,
                "song_original_genre": self.genre,
                "song_original_scale": self.scale,
                "song_original_tempo": self.tempo,
                "song_status": "active",
                "song_thumbnail_file_location": new_thumbnail_path,
                "singer": self.singer,
                "lyricist": self.lyricist,
                "composer": self.composer,
                "producer": self.producer}
        self.fb.db.child("Song_Master").child(new_song_id).set(data)
        return new_song_id

    def insert_new_BGM_filter(self):
        this_BGM_filter = self.fb.db.child("BGM_Filter_Master").order_by_child("genre_name").equal_to(self.genre).get()
        if len(this_BGM_filter.val()) == 0:
            all_BGM_filter = self.fb.db.child("BGM_Filter_Master").get()
            max_frontend_seq = 0
            for filter in all_BGM_filter:
                filter_val = filter.val()
                frontend_seq = int(filter_val["frontend_appearance_seq_no"])
                if frontend_seq > max_frontend_seq:
                    max_frontend_seq = frontend_seq
            new_frontend_seq = max_frontend_seq + 1

            new_genre_image_path = "Image/Filter/BGM/" + self.genre
            self.fb.storage.child(new_genre_image_path).put(self.genre_image_path)

            now = datetime.now()
            data = {"frontend_appearance_seq_no": str(new_frontend_seq),
                    "genre_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                    "genre_image_file_path": new_genre_image_path,
                    "genre_name": self.genre,
                    "genre_status": "active"}
            self.fb.db.child("BGM_Filter_Master").child(self.genre).set(data)

    def insert_new_language(self):
        this_language = self.fb.db.child("Language_Master").order_by_child("language_name").equal_to(self.language).get()
        if len(this_language.val()) == 0:
            now = datetime.now()
            data = {"language_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                    "language_name": self.language,
                    "language_status": "active"}
            self.fb.db.child("Language_Master").child(self.language).set(data)

    def insert_new_category(self):
        this_category = self.fb.db.child("Song_Category_Master").order_by_child("category_name").equal_to(self.category).get()
        if len(this_category.val()) == 0:
            now = datetime.now()
            data = {"category_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                    "category_name": self.category,
                    "category_status": "active"}
            self.fb.db.child("Song_Category_Master").child(self.category).set(data)

    def insert_new_tempo(self):
        this_tempo = self.fb.db.child("Tempo_Master").order_by_child("tempo_no").equal_to(
            self.tempo).get()
        if len(this_tempo.val()) == 0:
            now = datetime.now()
            data = {"tempo_created_on": now.strftime("%d/%m/%Y %H:%M:%S"),
                    "tempo_no": self.tempo,
                    "tempo_status": "active"}
            self.fb.db.child("Tempo_Master").child(self.tempo).set(data)


    def insert_new_song_genre_list(self, song_id):
        this_genre_in_genre_list = self.fb.db.child("Song_Genre_List").child(song_id).get()
        if this_genre_in_genre_list.val() == None:
            data = {self.genre: {"genre_name": self.genre}}
            self.fb.db.child("Song_Genre_List").child(song_id).set(data)
        elif len(this_genre_in_genre_list.val()) == 0:
            data = {self.genre: {"genre_name": self.genre}}
            self.fb.db.child("Song_Genre_List").child(song_id).set(data)
        else:
            data = {"genre_name": self.genre}
            self.fb.db.child("Song_Genre_List").child(song_id).child(self.genre).set(data)


    def insert_new_song_tempo_list(self, song_id):
        this_tempo_in_tempo_list = self.fb.db.child("Song_Tempo_List").child(song_id).get()
        if this_tempo_in_tempo_list.val() == None:
            data = {self.tempo: {"tempo_no": self.tempo}}
            self.fb.db.child("Song_Tempo_List").child(song_id).set(data)
        elif len(this_tempo_in_tempo_list.val()) == 0:
            data = {self.tempo: {"tempo_no": self.tempo}}
            self.fb.db.child("Song_Tempo_List").child(song_id).set(data)
        else:
            data = {"tempo_no": self.tempo}
            self.fb.db.child("Song_Tempo_List").child(song_id).child(self.tempo).set(data)



    def insert_new_song_scale_list(self, song_id):
        this_scale_in_scale_list = self.fb.db.child("Song_Scale_List").child(song_id).get()
        if this_scale_in_scale_list.val() == None:
            data = {self.scale: {"scale_name": self.scale}}
            self.fb.db.child("Song_Scale_List").child(song_id).set(data)
        elif len(this_scale_in_scale_list.val()) == 0:
            data = {self.scale: {"scale_name": self.scale}}
            self.fb.db.child("Song_Scale_List").child(song_id).set(data)
        else:
            data = {"scale_name": self.scale}
            self.fb.db.child("Song_Scale_List").child(song_id).child(self.scale).set(data)


