from pathlib import Path


class FileService:
    def __init__(self, export_dir: Path, docs_dir: Path):
        self.export_dir = export_dir
        self.docs_dir = docs_dir

    def archive(self, name: str) -> Path:
        path = self.export_dir / name
        if not path.is_file():
            raise FileNotFoundError(name)
        return path

    def manual(self, language: str) -> str:
        name = 'WERKINSTRUCTIE.en.md' if language == 'en' else 'WERKINSTRUCTIE.md'
        return (self.docs_dir / name).read_text(encoding='utf-8')
