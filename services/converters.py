import os
import subprocess
from abc import ABC, abstractmethod

from pdf2docx import Converter

from services.file_reader import DocxReader


class FileConverter(ABC):

    @abstractmethod
    def func_covert(self, scr_file: str, dst_file: str) -> bool:
        pass


class PDF2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str):
        cv = Converter(scr_file)
        cv.convert(dst_file, start=0, end=None)
        cv.close()


class PDF2TXT(FileConverter):
    def func_covert(self, scr_file: str, dst_file: str):
        try:
            # Запускаем команду pdftotext
            result = subprocess.run(['pdftotext', '-enc', 'UTF-8', scr_file, dst_file], check=True, text=True,
                                    capture_output=True)
            # print(result.stdout)  # Выводим извлеченный текст
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при извлечении текста: {e}")
        except FileNotFoundError:
            print("Не удалось найти исполняемый файл pdftotext. Убедитесь, что xpdf установлен и путь добавлен в PATH.")
        return result.stdout


class DOCX2TXT(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str):
        data_str = DocxReader(method=1).file_read(scr_file)
        with open(dst_file, 'w', encoding='utf-8') as f_write:
            f_write.write(data_str)


class DOC2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:
        #name_file = scr_file[scr_file.rfind("\\") + 1:]
        name_file = os.path.basename(scr_file)
        converted_doc_path = f'./temp/{name_file}x'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')  # ./temp

        output_file_docx = DOCX2TXT().func_covert(converted_doc_path, f'{converted_doc_path[:-4]}txt')

        return output_file_docx


class ODT2DOCX(FileConverter):
    def func_covert(self, scr_file: str, dst_file: str) -> str:
        name_file = os.path.basename(scr_file)
        print(name_file)
        converted_doc_path = f'./temp/{name_file[:-3]}docx'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')

        output_file_docx = DOCX2TXT().func_covert(converted_doc_path, f'{converted_doc_path[:-4]}txt')
        return output_file_docx


class PPTX2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:
        name_file = scr_file[scr_file.rfind("/") + 1:]

        if not scr_file[-3:] == "ppt":
            converted_pdf_path = f'./temp/{name_file[:-4]}pdf'
            converted_doc_path = f'./temp/{name_file[:-4]}txt'
        else:
            converted_pdf_path = f'./temp/{name_file[:-3]}pdf'
            converted_doc_path = f'./temp/{name_file[:-3]}txt'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')

        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to pdf "{scr_file}" --outdir "{dst_file}"')

        # output_file_docx = PDF2DOCX().func_covert(converted_pdf_path, converted_doc_path)
        output_file_docx = PDF2TXT().func_covert(converted_pdf_path, converted_doc_path)
        return output_file_docx


class RTF2DOCX(FileConverter):

    def func_covert(self, scr_file: str, dst_file: str) -> str:

        #name_file = scr_file[scr_file.rfind("\\") + 1:]

        name_file = os.path.basename(scr_file)

        converted_doc_path = f'./temp/{name_file[:-3]}docx'

        if not os.path.isdir('./temp'):
            os.mkdir('./temp')
        if not os.path.exists(converted_doc_path):
            os.system(f'soffice --headless --convert-to docx "{scr_file}" --outdir "{dst_file}"')

        output_file_docx = DOCX2TXT().func_covert(converted_doc_path, f'{converted_doc_path[:-4]}txt')

        return output_file_docx
