import os
from abc import ABC, abstractmethod

from pdf2docx import Converter


class FileConverter(ABC):

    @abstractmethod
    def func_covert(self, scr_file: str, dst_file: str) -> bool:
        pass


class PDF2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str):
        cv = Converter(scr_file)
        cv.convert(dst_file, start=0, end=None)
        cv.close()


class DOC2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:
        name_file = scr_file[scr_file.rfind("\\") + 1:]
        converted_doc_path = f'./temp/{name_file}x'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')  # ./temp

        return converted_doc_path


class ODT2DOCX(FileConverter):
    def func_covert(self, scr_file: str, dst_file: str) -> str:
        name_file = scr_file[scr_file.rfind("\\") + 1:]
        converted_doc_path = f'./temp/{name_file[:-3]}docx'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')

        return converted_doc_path


class PPTX2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:
        name_file = scr_file[scr_file.rfind("/") + 1:]

        if not scr_file[-3:] == "ppt":
            converted_pdf_path = f'./temp/{name_file[:-4]}pdf'
            converted_doc_path = f'./temp/{name_file[:-4]}docx'
        else:
            converted_pdf_path = f'./temp/{name_file[:-3]}pdf'
            converted_doc_path = f'./temp/{name_file[:-3]}docx'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')

        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to pdf "{scr_file}" --outdir "{dst_file}"')

        output_file_docx = PDF2DOCX().func_covert(converted_pdf_path, converted_doc_path)
        return output_file_docx


class RTF2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:

        name_file = scr_file[scr_file.rfind("\\") + 1:]
        converted_doc_path = f'./temp/{name_file[:-3]}docx'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')

        return converted_doc_path
