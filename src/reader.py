import os
from media import Section


class SectionReader:
    _errors = []

    def __init__(self, dir_path: str) -> None:
        self.sections = self._read_sections(dir_path)

        self._is_parameters_duplicated()
        self._is_parameters_exsit()
        self._rasie_if_errors()

    def get_sections(self) -> list[Section]:
        return self.sections

    def _read_sections(self, dir_path) -> list[Section]:
        sections: list[Section] = []

        for section_dir in os.listdir(dir_path):
            section_path = os.path.join(dir_path, section_dir)

            if not os.path.isdir(section_path):
                continue

            sections.append(Section(section_path))

        return sections

    def _is_parameters_exsit(self, sections: list[Section]) -> bool:
        exsit = True

        for section in sections:
            if section.parameters:
                continue

            error_mes = "yaml parameter file not found in %s" % section.dir_path
            self._errors.append(error_mes)
            exsit = False

        return exsit

    def _is_parameters_duplicated(self, sections: list[Section]) -> bool:
        duplicated = False

        for section in sections:
            if not section.parameters.uploaded:
                continue

            error_mes = "%s %s has been uploaded before" % (
                section.parameters.perch_mount_name,
                section.parameters.str_check_date,
            )
            self._errors.append(error_mes)
            duplicated = True

        return duplicated

    def _rasie_if_errors(self):
        if self._errors:
            raise SystemError("upload failed.\n%s" % "\n".join(self._errors))
