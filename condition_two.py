import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

from processor import process_sign_language_video

def get_first_consonant(base_word):
    """
    ฟังก์ชันสำหรับหาพยัญชนะไทยตัวแรกในสตริง
    เพื่อข้ามพวกสระหน้า (เ, แ, โ, ใ, ไ)
    """
    char = ""
    for c in base_word:
        if c >= "ก" and c <= "ฮ":
            char = c
            break
    
    if (char != ""):
        return char
    else:
        return base_word[0].upper()

def get_word_path_from_motion_dict(word, context, motion_dict_path):
    maint_path = ""
    p = Path(motion_dict_path)

    if p.name.upper() != "MOTION_DICT":
        print(f"ERROR: system not found the address from: {motion_dict_path}, please dowload MOTION_DICT zip and extract it.")
        return "ERROR", f"system not found the address from: {motion_dict_path}, please dowload MOTION_DICT zip and extract it."
    else:
        main_path = motion_dict_path

    # ดึงอักษรตัวแรกของคำภาษามือไทยคำนั้นๆ
    first_char = get_first_consonant(word)

    # สร้างโฟลเดอร์ระดับคำศัพท์ ex. (CLIP_WORD_DICT/ก/เกิน)
    word_dir = os.path.join(main_path, first_char, word)
    os.makedirs(word_dir, exist_ok=True)

    # ดึงไฟล์ meta.json ออกมาเพื่อดูว่าคำนี้มีมาแล้วกี่บริบท / คำนี้พึ่งถูกสร้างครั้งแรก
    meta_path = os.path.join(word_dir, "meta.json")
    meta_data = {}

    # ถ้ามีไฟล์ meta.json แล้ว ให้อ่านข้อมูลขึ้นมา
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as reader:
            meta_data = json.load(reader)

    # เช็คว่าบริบทนี้มีอยู่แล้วในคำภาษามือไทยนั้นๆ แล้วหรือไม่
    for variant_key, key_context in meta_data.items():
        if key_context == context:
            print(f"SKIPPED: This context already have in this {word}, skip saving motion.json")
            return "SKIPPED", f"This context already have in this {word}, skip saving motion.json"

    # หาหมายเลขเวอร์ชันถัดไป (นับจำนวน key ใน json แล้ว + 1)
    next_variant_key_num = len(meta_data) + 1
    new_variant_key = f"v{next_variant_key_num}"

    # อัปเดตไฟล์ meta.json
    meta_data[new_variant_key] = context
    with open(meta_path, 'w', encoding='utf-8') as writer:
        json.dump(meta_data, writer, ensure_ascii=False, indent=4)

    # สร้างโฟลเดอร์เวอร์ชันย่อย (บริบท ใหม่ที่พึ่งถูกเพิ่มเข้ามา)
    variant_dir = os.path.join(word_dir, new_variant_key)
    os.makedirs(variant_dir, exist_ok=True)

    return "SUCCESS", variant_dir


def create_folder_in_clip_word_dict(word, context, store_video_path):
    main_path = ""
    p = Path(store_video_path)

    # ตรวจสอบว่า มีโฟลเดอร์ที่ชื่อว่า ClIP_WORD_DICT อยู่ในนี้ไหม เพราะระบบจะเก็บคลิปที่โหลดมาเอาไว้ในนี้
    if p.name.upper() != "CLIP_WORD_DICT-2": # ตอนทำเสร็จแล้ว เอา -2 ออกนะ
        # สร้างโฟลเดอร์หลัก
        main_path = os.path.join(store_video_path, "CLIP_WORD_DICT-2")
        os.makedirs(main_path, exist_ok=True)
    else:
        main_path = store_video_path

    # ดึงอักษรตัวแรกของคำภาษามือไทยคำนั้นๆ
    first_char = get_first_consonant(word)

    # สร้างโฟลเดอร์ระดับคำศัพท์ ex. (CLIP_WORD_DICT/ก/เกิน)
    word_dir = os.path.join(main_path, first_char, word)
    os.makedirs(word_dir, exist_ok=True)

    # ดึงไฟล์ meta.json ออกมาเพื่อดูว่าคำนี้มีมาแล้วกี่บริบท / คำนี้พึ่งถูกสร้างครั้งแรก
    meta_path = os.path.join(word_dir, "meta.json")
    meta_data = {}

    # ถ้ามีไฟล์ meta.json แล้ว ให้อ่านข้อมูลขึ้นมา
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as reader:
            meta_data = json.load(reader)

    # เช็คว่าบริบทนี้มีอยู่แล้วในคำภาษามือไทยนั้นๆ แล้วหรือไม่
    for variant_key, key_context in meta_data.items():
        if key_context == context:
            print(f"SKIPPED: This context already have in this {word}, skip dowload.")
            return "SKIPPED", f"This context already have in this {word}, skip dowload."

    # หาหมายเลขเวอร์ชันถัดไป (นับจำนวน key ใน json แล้ว + 1)
    next_variant_key_num = len(meta_data) + 1
    new_variant_key = f"v{next_variant_key_num}"

    # อัปเดตไฟล์ meta.json
    meta_data[new_variant_key] = context
    with open(meta_path, 'w', encoding='utf-8') as writer:
        json.dump(meta_data, writer, ensure_ascii=False, indent=4)

    # สร้างโฟลเดอร์เวอร์ชันย่อย (บริบท ใหม่ที่พึ่งถูกเพิ่มเข้ามา)
    variant_dir = os.path.join(word_dir, new_variant_key)
    os.makedirs(variant_dir, exist_ok=True)

    return "SUCCESS", variant_dir


def download_th_sl_video(word, context, word_url, store_video_path, motion_dict_path):
    # ------------------------------------------------
    # 1. โหลดหน้าเว็บและสร้างโครงสร้างของ Tree 
    # ------------------------------------------------
    reponse = requests.get(word_url, timeout = 15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    # ------------------------------------------------
    # 2. ดึงลิงก์วิดีโอของคำ
    # ------------------------------------------------
    video_tag = soup.find('video')
    if not video_tag:
        print("ERROR: video not found!")
        return "ERROR", "Video not found!"

    source_tag = video_tag.find('source', type="video/mp4")
    if not source_tag or 'src' not in source_tag.attrs:
        print(f"ERROR: .MP4 not found in {word_url}")
        return "ERROR", f".MP4 not found! in {word_url}"

    video_url = source_tag['src']

    # ------------------------------------------------
    # 3. จัดการโครงสร้าง File System และ meta.json
    # ------------------------------------------------
    
    # ตรวจสอบก่อนว่ามีคำ และ บริบท ของภาษามือไทยนี้หรือยังใน Motion_Dict
    status, msg = get_word_path_from_motion_dict(word, context, motion_dict_path)



    # todo: ละเอาไว้ก่อนแปปนึง เดี๋ยวงง
    status, msg = create_folder_in_clip_word_dict(word, context, store_video_path)
    if status == "SUCCESS":
        # ------------------------------------------------
        # 4. ดาวน์โหลดไฟล์ .mp4
        # ------------------------------------------------
        output_file_path = os.path.join(msg, "original.mp4")
        vid_response = requests.get(video_url, stream=True)
        vid_response.raise_for_status()

        with open(output_file_path, 'wb') as video:
            for chunk in vid_response.iter_content(chunk_size=8192):
                video.write(chunk)

        return "SUCCESS", output_file_path
    elif status == "SKIPPED" or status == "ERROR":
        return status, msg


def process_single_url(word, context, word_url, store_video_path, motion_dict_path):
    # ตรวจสอบว่าลิงก์ที่เข้ามาเป็นมี source ที่เรารองรับหรือไม่
    if "th-sl" in word_url:
        # ดาวน์โหลดคลิปก่อน
        print(f"Downloading step:")
        status, msg = download_th_sl_video(word, context, word_url, store_video_path, motion_dict_path)
        if status == "SUCCESS":
            path = os.path.split(msg)
            video_path = os.path.join(path[0], "orginal.mp4")
            print(f"Dowloading clip from {word_url} success, and clip saved at: {msg}")

            # เราทำอันนี้เพื่อดึง path ของ motion_dict มาก่อนว่าจริงๆแล้ว คำควรเซฟเอาไว้ตรงไหน แล้วพอรู้แล้ว ก็ส่ง path นั้นออกมา แล้วส่งต่อให้ process_sign... เลย
            print("Managing the location of the motion.json file in Motion_dict for save step:")
            status, msg = get_word_path_from_motion_dict(word, context, motion_dict_path)
            if status == "SUCCESS":
                print("Managing location success.")
                json_path = os.path.join(msg, "motion.json")

                print("Processing clip into motion.jon step")
                process_sign_language_video(video_path, json_path)
                # ตรวจสอบความปลอดภัย: เช็คว่าไฟล์ motion.json สร้างสำเร็จแล้วจริงๆ
                if os.path.exists(json_path):
                    return "SUCCESS", f"Processing video from {video_path} success and saved motion.json at {json_path}"
                else:
                    print(f"ERROR: clip from {word_url} can't processed video to motion.json")
                    return "ERROR", f"clip from {word_url} can't processed video to motion.json"
            else:
                return status, msg

        else:
            return status, msg
    elif "dic.ttrs" in word_url:
        return download_ttrs_video(word, context, word_url, store_video_path, motion_dict_path)
    elif "youtube" in word_url or "youtu.be" in word_url:
        return download_youtube_video(word, context, word_url, store_video_path, motion_dict_path)
    else:
        return "ERROR", f"This system not supported the source of this url: {word_url}"

def reading_json_file(input_json_path):

    # 1. ตรวจสอบว่า file ที่ใส่มามีจริงหรือไม่
    if not os.path.isfile(input_json_path):
        print(f"ERROR: Not found this file in {input_json_path}")
        return

    # 2. อ่านไฟล์ JSON
    try:
        with open(input_json_path, 'r', encoding='utf-8') as reader:
            data = json.load(reader)

        # 2.1 อ่าน Path ที่ผู้ใช้กรอกมา
        raw_temp_vid_path = data.get("temporary_save_clip_path_address", "")
        raw_motion_dict_path = data.get("motion_dict_path_address", "")
        
        # 2.2 เตรียมอ่านไฟล์ ในส่วนของ input_url_word_tsl
        if os.path.exists(raw_motion_dict_path):
            if not os.path.exists(raw_temp_vid_path):
                os.makedirs(raw_temp_vid_path, exist_ok=True)

            # current_dir = os.getcwd()
            # error_log = os.path.join(current_dir, "error_condition_two_log.txt")
            
            # with open(error_log, "w", encoding="utf-8") as err_log:
            #     err_log.write("- - - Error Log สำหรับการทำงานของ Condition ที่ 2 - - -\n")
            #     err_log.flush()
            word_list = data.get("input_url_word_tsl", [])

            success = 0
            skipped = 0
            error = 0

            for idx, word in enumerate(word_list, 1):
                try:
                    word_name = word.get("word_name").strip()
                    word_context = word.get("word_context").strip()
                    word_url = word.get("word_url").strip()

                    # ------------------------------------------------
                    # ตรวจสอบว่า ชื่อ บริบท และลิงก์ต้นตอของคำเป็นช่องว่างไหม 
                    # ------------------------------------------------
                    if word_name and word_context and word_url:
                        print(f"[{idx}/{len(word_list)}]")
                        status, msg = process_single_url(word_name, word_context, word_url, raw_temp_vid_path, raw_motion_dict_path)

                        if status == "SUCCESS":
                            print(f"{status}: {msg}")
                        elif status == "SKIPPED":
                            skipped += 1
                            print(f"{status}: {msg}")
                            # err_log.write(f"[{status}]: {msg}") เอานะอันนี้
                        elif status == "ERROR":
                            error += 1
                            print(f"{status}: {msg}")
                            # err_log.write(f"[{status}]: {msg}") เอานะอันนี้
                    else:
                        print(f"[{idx}/{len(word_list)}]")
                        print("ERROR: Please fill the value.")

                except Exception as e:
                    error += 1
                    # print(f"Have an error in  in [{variant_name}]. | Error: {e}")
                    # log.write(f"Path: {root} | Error: {e}\n")
        else:
            print("Error: please dowload MOTION_DICT before you use this operation.")
            return None

    except json.JSONDecodeError as e:
        print(f"Error: {e}")
        return None
        




if __name__ == "__main__":
    print("Running condition_two.py directly.")
    reading_json_file()