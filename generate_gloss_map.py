import os
import json

def create_gloss_map(base_dir, output_file):
     print(f"Search meta.json in: {base_dir}")

     # 1. สร้าง Dictionary ก้อนใหญ่เตรียมเอาไว้
     master_dict = {
          "gloss_map":{}
     }

     count_word = 0

     # 2. ใช้ os.walk เดินหาไฟล์ meta.json ไม่ต้องใช้ os.listdir เพื่อลูปซ้อน
     for root, dirs, files in os.walk(base_dir):
          if "meta.json" in files:
               meta_path = os.path.join(root, "meta.json")

               # ดึงชื่อคำศัพท์ออกมาจาก Path
               # ตัวอย่าง root: "MOTION_DICT/ก/เกิน" -> os.path.basename จะได้ "เกิน"
               word_name = os.path.basename(root)

               try:
                    # 3. เปิดอ่านไฟล์ meta.json ของคำภาษามือไทยแต่ละคำ
                    with open(meta_path, 'r', encoding='utf-8') as reader:
                         meta_content = json.load(reader)
                    
                    # 4. นำข้อมูล meta.json ที่อ่านมาได้ มาใส่ใน Dictionary ก้อนใหญ่ โดยใช้ชื่อคำภาษามือไทยเป็น key
                    master_dict["gloss_map"][word_name] = meta_content
                    count_word += 1
               except Exception as e:
                    print(f"Error to reading meta.json at path: {meta_path}: {e}")
     # 5. เมื่อวนลูปครบทุกไฟล์แล้ว นำ Dictionary ก้อนใหญ่มาเซฟเป็นไฟล์ gloss_map.json
     print(f"Saving meta.json from {count_word} words into {output_file}")

     try:
          with open(output_file, 'w', encoding='utf-8') as writer:
               json.dump(master_dict, writer, ensure_ascii=False, indent=4)
          print(f"gloss.json saved at successfully at path: {output_file}")
     except Exception as e:
          print(f"There is an error to save gloss_map.json | error: {e}")

if __name__ == "__main__":
     base_dir = r"C:\AB-BiMaGOOD\CS_PROJECT\Database\MOTION_DICT"
     output_file = "gloss_map.json"
     create_gloss_map(base_dir, output_file)