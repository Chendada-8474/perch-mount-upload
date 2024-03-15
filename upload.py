import os
import tqdm
import json
import shutil
import easygui
import src.media
from src.reader import SectionReader
import configs.config as config


def read_sections() -> list[src.media.Section]:
    parent_dir = easygui.diropenbox(msg="請選擇要上傳的資料夾。")

    reader = SectionReader(parent_dir)

    return reader.get_sections()


def save_task(section: src.media.Section):

    file_name = (
        "%s_%s.json"
        % (section.parameters.perch_mount_name, section.parameters.str_check_date),
    )

    task_path = os.path.join(config.TASK_TARGET_DIR, file_name)
    task_media_path = os.path.join(
        config.MEDIA_PENDING_STORAGE,
        section.parameters.project,
        section.parameters.perch_mount_name,
        section.parameters.str_check_date,
        file_name,
    )

    with open(task_path, "w", encoding="utf-8") as f:
        json.dump(section.json(), f, ensure_ascii=False, indent=4)
    with open(task_media_path, "w", encoding="utf-8") as f:
        json.dump(section.json(), f, ensure_ascii=False, indent=4)


def main():
    # read sections, and raise error when yaml not found in section dir

    sections = read_sections()

    for section in sections:
        section_name = "%s %s" % (
            section.parameters.perch_mount_name,
            section.parameters.str_check_date,
        )

        # shift media datetime if necessary
        section.shift_media_datetime()

        # move file to destinaation
        print("正在複製 %s 的檔案到 NAS 中：" % section_name)
        for medium in tqdm.tqdm(section.media):
            shutil.copy2(medium.ori_path, medium.des_path)

        # save task file for schedule detector
        save_task(section)

        # tag yaml uploaded as True
        section.parameters.tag_uploaded()

        print("%s 上傳成功！" % section_name)

    print("所有上傳作業已結束")


if __name__ == "__main__":
    main()
