import os

from models.file import File
from models.ownership import Ownership
from models.version import Version
from utils.proglang import guess_programing_language

def save_file_if_not_found(session, file_path):
    file = session.query(File, Ownership) \
        .join(Ownership, File.file_id == Ownership.file_id) \
        .filter(Ownership.version_id == Version.version_id) \
        .filter(File.path == file_path).first()
    if not file:
        # Guess the programming language
        extension = os.path.splitext(file_path)[-1]
        lang = guess_programing_language(extension)
        file = File(path=file_path, language=lang)
        session.add(file)
        session.commit()
    return file
