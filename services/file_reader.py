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

                return list_docs_str

    def colontituls_read(self, file_name: str):
        docx = Document(file_name)

        headers = []
        footers = []

        for section in docx.sections:

            for paragraph in section.header.paragraphs:
                headers.append(paragraph.text)

            for paragraph in section.footer.paragraphs:
                footers.append(paragraph.text)

        return headers, footers

    def table_read(self, file_name: str):
        docx = Document(file_name)

        list_table_data = []

        for i_table in range(len(docx.tables)):
            for i_row in range(len(docx.tables[i_table].rows)):
                for i_cell in range(len(docx.tables[i_table].rows[i_row].cells)):
                    text_cell = docx.tables[i_table].rows[i_row].cells[i_cell].text
                    t_cell = text_cell.split('\n')
                    for i in range(len(t_cell)):
                        list_table_data.append(f'table:{i_table}row:{i_row}cell:{i_cell}index:{i}text:{t_cell[i]}')
        return list_table_data


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
