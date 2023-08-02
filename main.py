from new_annotation import InsertNewAnnotationIntoDB_WoDwdmr


class NewAnnotation():
    def insert_annotation_offline(self):
        genre_image_path = ""
        song_name = "Kesariya"
        language = "hindi"
        category = "evergreen"
        thumbnail_path = "C:\\Users\\91983\\Downloads\\kesariya.jpg"
        singer = "Arijit Singh"
        lyricist = ""
        composer = ""
        producer = ""
        annotator_ID = "arghyadeep0001"
        lyrics_json_path = "D:\\Annotations\\Ready to upload songs\\Kesariya Piano\\piano_94.json"
        genre = "piano"
        tempo = "94"
        daw_scale = "C"

        # Please note file names should be scale names only
        # Scale list: A, A_sharp, B, C, C_sharp, D, D_sharp, E, F, F_sharp, G, G_sharp
        # File names : A.mp3, A_sharp.mp3, ...
        multiscale_audio_path = "D:\\Annotations\\Ready to upload songs\\Kesariya Piano\\Kesariya_Piano_90_C"
        daw_project_path = "D:\\Annotations\\Ready to upload songs\\Kesariya Piano\\Kesariya_Piano_90_C.logicx.zip"
        # Possible values : "logic", "fl_studio", "cubase", ...
        daw_name = "logic"

        obj = InsertNewAnnotationIntoDB_WoDwdmr(genre_image_path,
                 song_name, language, category, thumbnail_path, singer, lyricist, composer, producer,
                 annotator_ID, lyrics_json_path, genre, tempo, daw_scale, multiscale_audio_path, daw_project_path, daw_name)

        song_id = obj.route()

def main():
    obj = NewAnnotation()
    obj.insert_annotation_offline()

if __name__ == '__main__':
    main()