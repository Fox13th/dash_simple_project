from docx import Document


def replace_paragraph_text(doc_path, old_text, new_text):
    # Открываем документ
    doc = Document(doc_path)

    # Проходим по всем абзацам в документе
    for paragraph in doc.paragraphs:
        if old_text in paragraph.text:
            # Создаем новый абзац для замены
            new_paragraph = doc.add_paragraph()
            # Проходим по всем "runs" в абзаце
            for run in paragraph.runs:
                # Если текст в "run" содержит старый текст, заменяем его
                if old_text in run.text:
                    # Заменяем текст и добавляем новый "run" с сохранением стиля
                    new_run = new_paragraph.add_run(run.text.replace(old_text, new_text))
                    new_run.bold = run.bold
                    new_run.italic = run.italic
                    new_run.underline = run.underline
                    new_run.font.size = run.font.size
                    new_run.font.name = run.font.name
                else:
                    # Если текст не содержит старый текст, просто копируем "run"
                    new_run = new_paragraph.add_run(run.text)
                    new_run.bold = run.bold
                    new_run.italic = run.italic
                    new_run.underline = run.underline
                    new_run.font.size = run.font.size
                    new_run.font.name = run.font.name

            # Удаляем старый абзац
            p = paragraph._element
            p.getparent().remove(p)

    # Сохраняем изменения в новом документе
    doc.save('updated_document.docx')


# Пример использования
replace_paragraph_text('your_document.docx', 'старый текст', 'новый текст')