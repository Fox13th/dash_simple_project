import fasttext

from core import config

settings = config.get_settings()


class LangDetect:
    def __init__(self):
        self.model = fasttext.load_model(settings.lang_model)

    def detection(self, text: str):
        prediction = self.model.predict(text)
        return {'language': prediction[0][0][9:], 'confidence': prediction[1][0]}
