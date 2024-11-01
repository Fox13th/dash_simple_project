from abc import ABC, abstractmethod

from pdf2docx import Converter


class FileConverter(ABC):

    @abstractmethod
    def func_covert(self, scr_file: str, dst_file: str):
        pass


class PDF2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str):
        cv = Converter(scr_file)
        cv.convert(dst_file, start=0, end=None)
        cv.close()
