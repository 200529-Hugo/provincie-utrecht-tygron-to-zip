from pathlib import Path

from ..models import ValidationResult
from ..validation import validate_archive, validate_dossier_directory


class ValidationService:
    def validate_archive(self, archive: Path) -> ValidationResult:
        return ValidationResult.from_dict(validate_archive(archive))

    def validate_directory(
        self,
        directory: Path,
        check_manifest: bool = True,
    ) -> ValidationResult:
        return ValidationResult.from_dict(
            validate_dossier_directory(directory, check_manifest=check_manifest)
        )
