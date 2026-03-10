import os
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import yt_dlp

from processor import process_sign_language_video

def running_process_sign_language_video(status, msg, word_url):
    if status == "SUCCESS":
        print(f"Dowloading clip from {word_url} success, and clip saved at: {msg['output_video_path']}")
        print("Processing clip into motion.jon step:")

        process_sign_language_video(msg['output_video_path'], msg['output_motion_path'])

        # ตรวจสอบความปลอดภัย: เช็คว่าไฟล์ motion.json สร้างสำเร็จแล้วจริงๆ
        if os.path.exists(msg['output_motion_path']):
            return "SUCCESS", f"Processing video from {msg['output_video_path']} success and saved motion.json at {msg['output_motion_path']}"
        else:
            # print(f"ERROR: clip from {word_url} can't processed video to motion.json")
            return "ERROR", f"clip from {word_url} can't processed video to motion.json"
    else:
        return status, msg

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

def create_folder_clip_word_dict(store_video_path):
    result_path = ""
    p = Path(store_video_path)

    if p.name.upper() != "CLIP_WORD_DICT":
        result_path = os.path.join(store_video_path, "CLIP_WORD_DICT")
        os.makedirs(result_path, exist_ok=True)
        return result_path
    else:
        result_path = store_video_path
        return result_path

def get_clip_path_from_motion_dict(word, context, motion_dict_path):
    sub_folder = {} # เอาไว้เก็บ first_char, word, variant and full_variant_path
    maint_path = ""
    p = Path(motion_dict_path)

    if p.name.upper() != "MOTION_DICT":
        # print(f"ERROR: system not found the address from: {motion_dict_path}, please dowload MOTION_DICT zip and extract it.")
        return "ERROR", f"system not found the address from: {motion_dict_path}, please dowload MOTION_DICT zip and extract it."
    else:
        main_path = motion_dict_path

    # ดึงอักษรตัวแรกของคำภาษามือไทยคำนั้นๆ
    first_char = get_first_consonant(word)
    sub_folder['first_char'] = first_char

    # สร้างโฟลเดอร์ระดับคำศัพท์ ex. (CLIP_WORD_DICT/ก/เกิน)
    word_dir = os.path.join(main_path, first_char, word)
    os.makedirs(word_dir, exist_ok=True)
    sub_folder['word'] = word

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
            # print(f"SKIPPED: This context already have in this {word}, skip saving motion.json")
            return "SKIPPED", f"This context already have in this {word}, skip saving motion.json"

    # หาหมายเลขเวอร์ชันถัดไป (นับจำนวน key ใน json แล้ว + 1)
    next_variant_key_num = len(meta_data) + 1
    new_variant_key = f"v{next_variant_key_num}"
    sub_folder['variant_key'] = new_variant_key

    # อัปเดตไฟล์ meta.json
    meta_data[new_variant_key] = context
    with open(meta_path, 'w', encoding='utf-8') as writer:
        json.dump(meta_data, writer, ensure_ascii=False, indent=4)

    # สร้างโฟลเดอร์เวอร์ชันย่อย (บริบท ใหม่ที่พึ่งถูกเพิ่มเข้ามา)
    variant_dir = os.path.join(word_dir, new_variant_key)
    os.makedirs(variant_dir, exist_ok=True)
    sub_folder['variant_dir'] = variant_dir

    return "SUCCESS", sub_folder

def download_youtube_video(word, context, word_url, store_video_path, motion_dict_path):
    status, msg = get_clip_path_from_motion_dict(word, context, motion_dict_path)
    if status == "SUCCESS":
        address_of_motion_and_video = {}
        # เก็บที่อยู่ของ motion.json ที่กำลังจะถูกสร้างใน mediapipe
        output_motion_path = os.path.join(msg['variant_dir'], "motion.json")
        address_of_motion_and_video['output_motion_path'] = output_motion_path

        main_clip_video_path = create_folder_clip_word_dict(store_video_path)
        output_video_path = os.path.join(main_clip_video_path, msg['first_char'], msg['word'], msg['variant_key'], "original.mp4")
        address_of_motion_and_video['output_video_path'] = output_video_path

        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        # ตั้งค่า yt-dlp 
        ydl_opts = {
            # บังคับให้โหลดเฉพาะวิดีโอ (ไม่เอาเสียง) และต้องเป็น .mp4 เท่านั้น
            'format': 'best[ext=mp4][vcodec^=avc1]',
            'outtmpl': output_video_path, # ชื่อไฟล์และที่อยู่ที่จะเซฟ
            'quiet': True, # ไม่ให้แสดง Progress bar ตอนโหลด
            'no_warnings': True,
            'overwrites': True # ถ้ามีไฟล์ original.mp4 ค้างอยู่ให้เขียนทับเลย
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([word_url])

            # ตรวจสอบว่าโหลดมาสำเร็จและมีไฟล์จริง
            if os.path.exists(output_video_path):
                return "SUCCESS", address_of_motion_and_video
            else:
                # print(f"ERROR: Dowload successed but not found the original.mp4 at {output_video_path}")
                return "ERROR" f"Dowload successed but not found the original.mp4 at {output_video_path}"

        except Exception as e:
            # print(f"ERROR: Somthing went wrong for loading clip Youtube: {e}")
            return "ERROR", f"URL: {word_url} | Error: somthing went wrong for loading clip Youtube:{e}"
    else:
        return status, msg

def download_ttrs_video(word, context, word_url, store_video_path, motion_dict_path):
    # 1. ดึง id จาก url ท้ายสุด
    video_id = word_url.split('/')[-1].strip()

    # 2. สร้างลิงก์ API
    api_url = f"https://apidic.ttrs.or.th/api/v1/sqrtube_get_by_id/{video_id}"

    try:
        # 3. ยิง request ไปขอข้อมูล JSON
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # 4. ดึงลิงก์วิดีโอ .mp4 (พยายามดึง 720p ก่อน ถ้าไม่มีเอาอันธรรมดา)
        # video_url = data.get("urlmp4_720") or data.get("url_mp4") or data.get("urlmp4_480")
        # แทนที่โค้ดดึง video_url เดิมด้วยบล็อกนี้
        possible_urls = [
            data.get("urlmp4_720"),
            data.get("urlmp4_480"),
            data.get("url_mp4"),
            data.get("url_download")
        ]

        vid_response = None
        
        # วนลูปทดสอบโหลดทีละลิงก์
        for p_url in possible_urls:
            if not p_url:
                continue
            try:
                temp_res = requests.get(p_url, stream=True, timeout=15)
                temp_res.raise_for_status() # ถ้าเจอ 404 โปรแกรมจะกระโดดไปที่ except HTTPError
                
                # ถ้าผ่านมาถึงบรรทัดนี้ได้ แปลว่าลิงก์นี้มีไฟล์อยู่จริง
                vid_response = temp_res
                break # หยุดลูปเลย ไม่ต้องลองลิงก์อื่นแล้ว
                
            except requests.exceptions.HTTPError:
                continue
                
        if not vid_response:
            return "ERROR", f"URL: {word_url} | Error: Not found any link url that can download (404 Not Found)."

        status, msg = get_clip_path_from_motion_dict(word, context, motion_dict_path)
        if status == "SUCCESS":
            address_of_motion_and_video = {}
            # เก็บที่อยู่ของ motion.json ที่กำลังจะถูกสร้างใน mediapipe
            output_motion_path = os.path.join(msg['variant_dir'], "motion.json")
            address_of_motion_and_video['output_motion_path'] = output_motion_path

            main_clip_video_path = create_folder_clip_word_dict(store_video_path)
            output_video_path = os.path.join(main_clip_video_path, msg['first_char'], msg['word'], msg['variant_key'], "original.mp4")
            address_of_motion_and_video['output_video_path'] = output_video_path

            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

            with open(output_video_path, 'wb') as video:
                for chunk in vid_response.iter_content(chunk_size=8192):
                    if chunk:
                        video.write(chunk)
                    
            return "SUCCESS", address_of_motion_and_video
        else:
            return status, msg
    except Exception as e:
        return "ERROR", f"URL: {word_url} | Error: {e}"

def download_th_sl_video(word, context, word_url, store_video_path, motion_dict_path):
    try:
        # ------------------------------------------------
        # 1. โหลดหน้าเว็บและสร้างโครงสร้างของ Tree 
        # ------------------------------------------------
        response = requests.get(word_url, timeout = 15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # ------------------------------------------------
        # 2. ดึงลิงก์วิดีโอของคำ
        # ------------------------------------------------
        video_tag = soup.find('video')
        if not video_tag:
            # print(f"ERROR: video not found! from {word_url}")
            return "ERROR", f"Video not found! from {word_url}"

        source_tag = video_tag.find('source', type="video/mp4")
        if not source_tag or 'src' not in source_tag.attrs:
            # print(f"ERROR: .MP4 not found this {word_url} in www.th-sl.com")
            return "ERROR", f".MP4 not found this {word_url} in www.th-sl.com"

        video_url = source_tag['src']

        # ------------------------------------------------
        # 3. จัดการโครงสร้าง File System และ meta.json
        # ------------------------------------------------
        # ตรวจสอบก่อนว่ามีคำ และ บริบท ของภาษามือไทยนี้หรือยังใน Motion_Dict
        status, msg = get_clip_path_from_motion_dict(word, context, motion_dict_path)
        if status == "SUCCESS":
            address_of_motion_and_video = {}
            # เก็บที่อยู่ของ motion.json ที่กำลังจะถูกสร้างใน mediapipe
            output_motion_path = os.path.join(msg['variant_dir'], "motion.json")
            address_of_motion_and_video['output_motion_path'] = output_motion_path

            # ------------------------------------------------
            # 4. ดาวน์โหลดไฟล์ .mp4
            # ------------------------------------------------
            # เก็บที่อยู่ของ original.mp4 ที่จะอยู่ใน CLIP_WORD_DICT
            main_clip_video_path = create_folder_clip_word_dict(store_video_path)
            output_video_path = os.path.join(main_clip_video_path, msg['first_char'], msg['word'], msg['variant_key'], "original.mp4")
            address_of_motion_and_video['output_video_path'] = output_video_path

            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

            vid_response = requests.get(video_url, stream=True)
            vid_response.raise_for_status()

            with open(output_video_path, 'wb') as video:
                for chunk in vid_response.iter_content(chunk_size=8192):
                    if chunk:
                        video.write(chunk)
                        

            return "SUCCESS", address_of_motion_and_video
        else:
            return status, msg
    except Exception as e:
        return "ERROR", f"URL: {word_url} | Error: {e}"

def process_single_url(word, context, word_url, store_video_path, motion_dict_path):
    # ตรวจสอบว่าลิงก์ที่เข้ามาเป็นมี source ที่เรารองรับหรือไม่
    if "th-sl" in word_url:
        # ดาวน์โหลดคลิปก่อน
        print(f"Downloading step:")
        status, msg = download_th_sl_video(word, context, word_url, store_video_path, motion_dict_path)
        return running_process_sign_language_video(status, msg, word_url)
    elif "dic.ttrs" in word_url:
        print(f"Downloading step:")
        status, msg = download_ttrs_video(word, context, word_url, store_video_path, motion_dict_path)
        return running_process_sign_language_video(status, msg, word_url)
    elif "youtube" in word_url or "youtu.be" in word_url:
        print(f"Downloading step:")
        status, msg = download_youtube_video(word, context, word_url, store_video_path, motion_dict_path)
        return running_process_sign_language_video(status, msg, word_url)
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

            current_dir = os.getcwd()
            error_log = os.path.join(current_dir, "error_condition_two_log.txt")
            
            with open(error_log, "w", encoding="utf-8") as err_log:
                err_log.write("- - - Error Log สำหรับการทำงานของ Condition ที่ 2 - - -\n")
                err_log.flush()


                word_list = data.get("input_url_word_tsl", [])

                success = 0
                skipped = 0
                error = 0

                print("= = = = = Starting Process = = = = =")

                for idx, word in enumerate(word_list, 1):
                    try:
                        word_name = word.get("word_name").strip()
                        word_context = word.get("word_context").strip()
                        word_url = word.get("word_url").strip()

                        # ------------------------------------------------
                        # ตรวจสอบว่า ชื่อ บริบท และลิงก์ต้นตอของคำเป็นช่องว่างไหม 
                        # ------------------------------------------------
                        if word_name and word_context and word_url:
                            print(f"[\nOrder: {idx}/{len(word_list)}\nWord Name: {word_name}\nWord Context: {word_context}\nURL: {word_url}\n] ")
                            status, msg = process_single_url(word_name, word_context, word_url, raw_temp_vid_path, raw_motion_dict_path)

                            if status == "SUCCESS":
                                success += 1
                                print(f"{status}: {msg}")
                            elif status == "SKIPPED":
                                skipped += 1
                                print(f"{status}: {msg}")
                                err_log.write(f"[{status}]: {msg}\n")
                                err_log.flush()
                            elif status == "ERROR":
                                error += 1
                                print(f"{status}: {msg}")
                                err_log.write(f"[{status}]: {msg}\n")
                                err_log.flush()
                        else:
                            print(f"[{idx}/{len(word_list)}]")
                            print("ERROR: Please fill the value.")
                            err_log.flush()

                    except Exception as e:
                        error += 1
                        print(f"Have an error in  in [{word_url}]. | Error: {e}")
                        log.write(f"URL: {word_url} | Error: {e}\n")

                print("- - - - - Summary - - - -")
                print(f"SUCCESS: {success} clips.")
                print(f"SKIPPED: {skipped} clips.")
                print(f"ERROR: {error} clips. error_condition_two_log.txt saved at {err_log}")
                print("= = = = = Ending Process = = = = =")
        else:
            print("Error: please dowload MOTION_DICT before you use this operation.")
            return None

    except json.JSONDecodeError as e:
        print(f"Error: {e}")
        return None
        
if __name__ == "__main__":
    print("Running condition_two.py directly.")
    reading_json_file()