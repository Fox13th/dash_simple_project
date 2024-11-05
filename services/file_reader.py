from abc import ABC, abstractmethod

from docx import Document


class FileReader(ABC):

    @abstractmethod
    def file_read(self, file: str):
        pass


class DocxReader(FileReader):

    def file_read(self, file_name: str):
        docx = Document(file_name)
        docs_str = ''

        for i in range(len(docx.paragraphs)):
            if i < len(docx.paragraphs) - 1:
                docs_str += docx.paragraphs[i].text + '\n'
            else:
                docs_str += docx.paragraphs[i].text

        for table in docx.tables:
            for row in table.rows:
                for cell in row.cells:
                    docs_str += cell.text + '\n'
        return docs_str


class TXTReader(FileReader):

    def file_read(self, file: str):
        with open(file, 'r', encoding='utf-8') as f_read:
            lines = f_read.readlines()

        data_str = ''
        for data in lines:
            data_str += data
        return data_str
