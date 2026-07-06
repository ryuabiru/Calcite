from __future__ import annotations

from ..services.project_service import ProjectState, read_project_archive, write_project_archive


class SaveProjectUseCase:
    def execute(self, file_path: str, state: ProjectState) -> None:
        write_project_archive(file_path, state)


class OpenProjectUseCase:
    def execute(self, file_path: str) -> ProjectState:
        return read_project_archive(file_path)
