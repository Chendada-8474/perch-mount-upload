import os
from src.media import Section


class SectionReader:
    _errors = []

    def __init__(self, dir_path: str) -> None:
        self.sections = self._read_sections(dir_path)

        self._check_parameters(self.sections)
        # self._rasie_if_errors()
        self._init_childrens()

    def get_sections(self) -> list[Section]:
        return self.sections

    def _check_parameters(self, sections: list[Section]):
        if not self._is_all_parameters_exsit(sections):
            raise FileNotFoundError("upload failed.\n%s" % "\n".join(self._errors))

        if self._is_any_parameters_duplicated(sections):
            raise SystemError("upload failed.\n%s" % "\n".join(self._errors))

    def _read_sections(self, dir_path) -> list[Section]:
        sections: list[Section] = []

        for section_dir in os.listdir(dir_path):
            section_path = os.path.join(dir_path, section_dir)

            if not os.path.isdir(section_path):
                continue

            sections.append(Section(section_path))

        return sections

    def _is_all_parameters_exsit(self, sections: list[Section]) -> bool:
        exsit = True

        for section in sections:
            if section.parameters:
                continue

            error_mes = "yaml parameter file not found in %s" % section.dir_path
            self._errors.append(error_mes)
            exsit = False

        return exsit

    def _is_any_parameters_duplicated(self, sections: list[Section]) -> bool:
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

    def _init_childrens(self):
        for section in self.sections:
            # read media in target dir
            section.read_media()

            # mkdir for section in destination
            section.init_des_dir()
            section.init_nas_dir()

            # init des path
            for medium in section.media:
                medium.init_des_path(
                    parent_dir=section.des_dir,
                    perch_mount_id=section.parameters.perch_mount_id,
                )
                medium.init_nas_path(
                    parent_dir=section.nas_dir,
                    perch_mount_id=section.parameters.perch_mount_id,
                )
