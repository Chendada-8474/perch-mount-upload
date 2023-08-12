import os
import tqdm
import json
import shutil
import easygui
import requests
import urllib.parse
import src.media as sm
import configs.config as config


def read_sections() -> list[sm.Section]:
    parent_dir = easygui.diropenbox(msg="請選擇要上傳的資料夾。")

    sections: list[sm.Section] = []

    for section_dir in os.listdir(parent_dir):
        section_path = os.path.join(parent_dir, section_dir)

        if not os.path.isdir(section_path):
            continue

        sections.append(sm.Section(section_path))

    section_errors = []
    for section in sections:
        if not section.parameters:
            error_mes = "yaml parameter file not found in %s" % section.dir_path
            section_errors.append(error_mes)
        if section.parameters.uploaded:
            error_mes = "%s %s has been uploaded before" % (
                section.parameters.perch_mount_name,
                section.parameters.str_check_date,
            )
            section_errors.append(error_mes)

    if section_errors:
        raise SystemError("upload failed.\n%s" % "\n".join(section_errors))

    for section in sections:
        # read media in target dir
        section.read_media()

        # mkdir for section in destination
        section.make_des_dir()

        # init des path
        for medium in section.media:
            medium.init_des_path(parent_dir=section.section_dir)

    return sections


def post_section(section: sm.Section) -> int:
    section_url = urllib.parse.urljoin(config.HOST, "/api/section")
    operators_url = urllib.parse.urljoin(config.HOST, "/api/section/%s/operators")
    headers = {"Content-type": "application/json", "Accept": "text/plain"}
    data = {
        "perch_mount": section.parameters.perch_mount_id,
        "mount_type": section.parameters.mount_type,
        "camera": section.parameters.camera,
        "start_time": section.str_start_time,
        "end_time": section.str_end_time,
        "check_date": section.parameters.str_check_date,
        "valid": section.parameters.valid,
        "note": section.parameters.note,
    }

    res = requests.post(section_url, data=json.dumps(data), headers=headers)
    section_id = json.loads(res.text)["section_id"]

    operators = {"operators": section.parameters.operators}
    res = requests.post(
        operators_url % section_id, data=json.dumps(operators), headers=headers
    )

    return section_id


def save_task(section_id: int, section: sm.Section):
    task_path = os.path.join(
        config.TASK_TARGET_DIR,
        "%s_%s.json"
        % (section.parameters.perch_mount_name, section.parameters.str_check_date),
    )

    with open(task_path, "w", encoding="utf-8") as f:
        json.dump(section.json(section_id), f, ensure_ascii=False, indent=4)


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

        # post new section to database by api
        new_section_id = post_section(section)

        # save task file for schedule detector
        save_task(new_section_id, section)

        # update yaml uploaded as True
        section.parameters.tag_uploaded()

        print("%s 上傳成功！" % section_name)

    print("所有上傳作業已結束")


if __name__ == "__main__":
    main()
