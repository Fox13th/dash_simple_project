from abc import ABC, abstractmethod

from docx import Document


class FileReader(ABC):

    @abstractmethod
    def file_read(self, file: str):
        pass


class DocxReader(FileReader):

    def file_read(self, file_name: str):
        docx = Document(file_name)

        for paragraph in docx.paragraphs:
            print(paragraph.text)

        for table in docx.tables:
            for row in table.rows:
                for cell in row.cells:
                    print(cell)