from abc import ABC, abstractmethod

from docx import Document


class FileReader(ABC):
    def __init__(self, method):
        self.method = method

    @abstractmethod
    def file_read(self, file: str):
        pass


class DocxReader(FileReader):

    def file_read(self, file_name: str):
        docx = Document(file_name)

        match self.method:
            case 1:
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
            case _:
                list_docs_str = []
                for paragraph in docx.paragraphs:
                    list_docs_str.append(paragraph)

                for table in docx.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            list_docs_str.append(cell.text)

                return list_docs_str


class TXTReader(FileReader):

    def file_read(self, file: str):
        with open(file, 'r', encoding='utf-8') as f_read:
            lines = f_read.readlines()
        match self.method:
            case 1:
                data_str = ''
                for data in lines:
                    data_str += data
                return data_str
            case _:
                return [line.replace('\n', '') for line in lines]
