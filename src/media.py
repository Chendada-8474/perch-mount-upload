import os
import sys
import yaml
import tqdm
from PIL import Image
from ffmpeg import probe
from dateutil.parser import parse
from datetime import datetime
from shortuuid import uuid
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import configs.config as config


class Parameter:
    def __init__(self, path: str) -> None:
        self.path = path
        self._dict = self._read(path)
        self._setattrs(self._dict)

    def _read(self, path):
        with open(path, "r", encoding="utf-8") as f:
            parameter = yaml.load(f, Loader=yaml.Loader)
        return parameter

    def _setattrs(self, parameter: dict):
        for k, v in parameter.items():
            setattr(self, k, v)

    def tag_uploaded(self):
        self._dict["uploaded"] = True
        with open(self.path, "w", encoding="utf-8") as f:
            parameter = yaml.dump(self._dict, f)

    def json(self) -> dict:
        return {
            "perch_mount": self.perch_mount_id,
            "perch_mount_name": self.perch_mount_name,
            "project": self.project,
            "mount_type": self.mount_type,
            "camera": self.camera,
            "check_date": self.str_check_date,
            "operators": self.operators,
            "valid": self.valid,
            "note": self.note,
        }

    @property
    def str_check_date(self):
        return datetime.strftime(self.check_date, "%Y-%m-%d")

    @property
    def str_start_time(self):
        if "start_time" in self._dict:
            return datetime.strftime(self.start_time, "%Y-%m-%d %H:%M:%S")


class Medium:
    des_path = None
    medium_datetime = None

    def __init__(self, path: str) -> None:
        self.medium_id = uuid()
        self.ori_path = path

    def init_des_path(self, parent_dir: str = None, perch_mount_id=""):
        self.des_path = os.path.join(parent_dir, self._new_basename(perch_mount_id))

    def json(self) -> dict:
        return {
            "medium_id": self.medium_id,
            "medium_datetime": self.str_medium_datetime,
            "path": self.des_path,
        }

    @property
    def str_medium_datetime(self):
        return datetime.strftime(self.medium_datetime, "%Y-%m-%d %H:%M:%S")

    @property
    def _str_datetime_for_filename(self):
        return datetime.strftime(self.medium_datetime, "%Y%m%d_%H%M%S")

    @property
    def ori_basename(self):
        return os.path.basename(self.ori_path)

    def _new_basename(self, perch_mount_id):
        _, ext = os.path.splitext(self.ori_basename)
        return "%s_%s_%s%s" % (
            perch_mount_id,
            self._str_datetime_for_filename,
            self.medium_id[:8],
            ext,
        )


class PMImage(Medium):
    def __init__(self, path: str) -> None:
        self.medium_datetime = self._get_datetime(path)
        super().__init__(path)

    def _get_datetime(self, path: str):
        dt = Image.open(path)._getexif()[36867]
        return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S")


class PMVideo(Medium):
    def __init__(self, path: str) -> None:
        self.medium_datetime = self._get_datetime(path)
        super().__init__(path)

    def _get_datetime(self, path: str):
        dt = probe(path)["streams"][0]["tags"]["creation_time"]
        dt = parse(dt).replace(tzinfo=None)
        return dt


class Section:
    section_dir = None

    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.parameters = self._read_parameter()
        self.media: list[Medium] = []

    def read_media(self):
        print(
            "reading information %s %s"
            % (self.parameters.perch_mount_name, self.parameters.check_date),
        )
        for path in tqdm.tqdm(self._all_paths(self.dir_path)):
            medium_type = self.medium_type(path)

            try:
                if medium_type == "image":
                    self.media.append(PMImage(path))
                elif medium_type == "video":
                    self.media.append(PMVideo(path))
            except Exception as e:
                print(e)

    def _read_parameter(self):
        for path in self._all_paths(self.dir_path):
            ext = os.path.splitext(path)[1]
            if ext == ".yaml":
                return Parameter(path)

    def medium_type(self, file_name) -> str:
        ext = os.path.splitext(file_name)[1][1:].lower()

        if ext in config.IMAGE_EXTENSIONS:
            return "image"
        elif ext in config.VIDEO_EXTENSIONS:
            return "video"

    def _all_paths(self, dir_path) -> list[str]:
        paths = []
        for subdir, _, files in os.walk(dir_path):
            for file in files:
                paths.append(os.path.join(subdir, file))
        return paths

    def make_des_dir(self):
        des_dir = os.path.join(
            config.MEDIA_ROOT,
            self.parameters.project,
            self.parameters.perch_mount_name,
            self.parameters.str_check_date,
        )
        self.section_dir = des_dir
        Path(des_dir).mkdir(parents=True, exist_ok=True)

    def shift_media_datetime(self):
        if not self.parameters.start_time:
            return

        time_diff = self.parameters.start_time - self.start_time
        for medium in self.media:
            medium.medium_datetime += time_diff

    def json(self) -> dict:
        return {
            "section": self.parameters.json(),
            "media": [medium.json() for medium in self.media],
        }

    @property
    def start_time(self) -> datetime:
        return min(medium.medium_datetime for medium in self.media)

    @property
    def end_time(self) -> datetime:
        return max(medium.medium_datetime for medium in self.media)

    @property
    def str_start_time(self) -> str:
        return datetime.strftime(self.start_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_end_time(self) -> str:
        return datetime.strftime(self.end_time, "%Y-%m-%d %H:%M:%S")

    @property
    def str_start_date(self) -> str:
        return datetime.strftime(self.start_time, "%Y-%m-%d")

    @property
    def str_end_date(self) -> str:
        return datetime.strftime(self.end_time, "%Y-%m-%d")


def read_images(dir_path: str) -> Section:
    return Section(dir_path)


if __name__ == "__main__":
    section = Section("D:/coding/dataset/perch-mount/NCYU/test/rcd625/")
    section.read_media()
    print(section.json(11))
