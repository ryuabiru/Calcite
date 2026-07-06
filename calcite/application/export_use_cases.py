from __future__ import annotations


class SaveTextUseCase:
    def execute(self, file_path: str, text: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
