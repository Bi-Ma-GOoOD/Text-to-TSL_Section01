import cv2
import mediapipe as mp
import json
import os
from pathlib import Path

# ---------------------------------------------------------
# ฟังก์ชันดึงพิกัดร่างกายเพื่อจัดเตรียมลง JSON
# ---------------------------------------------------------
def extract_pose_landmarks(landmarks_obj):
    if not landmarks_obj:
        return []
    data = []
    for idx, plm in enumerate(landmarks_obj.landmark):
        if idx <= 24:
            if (plm.visibility >= 0.1):
                landmarks = {
                    "landmark_location": idx,
                    "x": plm.x,
                    "y": plm.y,
                    "z": plm.z,
                    "visibility": plm.visibility
                }
            else:
                landmarks = {
                    "landmark_location": idx,
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "visibility": plm.visibility
                }
            data.append(landmarks)
            
    return data

# ---------------------------------------------------------
# ฟังก์ชันดึงพิกัดมือเพื่อจัดเตรียมลง JSON
# ---------------------------------------------------------
def extract_hands_landmarks(landmarks_obj):
    if not landmarks_obj:
        return []
    data = []
    for idx, hlm in enumerate(landmarks_obj.landmark):
        landmarks = {
            "landmark_location": idx,
            "x": hlm.x,
            "y": hlm.y,
            "z": hlm.z
        }
        data.append(landmarks)
    
    return data

# ---------------------------------------------------------
# ฟังก์ชันการแปลงคลิปวิดีโอเป็นข้อมูลการเคลื่อนไหวของพิกัดร่างกาย และมือ
# ---------------------------------------------------------
def process_sign_language_video(input_video, motion_path):
    # output_json_path = os.path.join(base_path, "motion.json")
    # print(f"base_path has value: {base_path}")
    # print(f"destination directory of json file at {output_json_path}")
    # return 1

    if not os.path.exists(input_video):
        print(f"Error: not found original input video at {input_video}")
        return

    cap = cv2.VideoCapture(input_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    json_data = {
        "clip_fps": fps,
        "total_frames": total_frames,
        "video_width": width,
        "video_height": height,
        "motion_data" : []
    }

    mp_holistic = mp.solutions.holistic

    with mp_holistic.Holistic(
        min_detection_confidence = 0.5,
        min_tracking_confidence = 0.5,
        model_complexity = 1) as holistic:

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(frame_rgb)

            pose_data = extract_pose_landmarks(results.pose_landmarks)
            left_hand_data = extract_hands_landmarks(results.left_hand_landmarks)
            right_hand_data = extract_hands_landmarks(results.right_hand_landmarks)

            frame_data = {
                "frame": frame_idx,
                "Image_Coordinates-(normalized_landmark)" : {
                    "pose": pose_data,
                    "left_hand": left_hand_data,
                    "right_hand": right_hand_data
                }
            }

            json_data["motion_data"].append(frame_data)
            frame_idx += 1

    cap.release()

    # สร้างไฟล์ motion.json ลงในโฟลเดอร์ของคำนั้นๆ
    with open(motion_path, "w", encoding="utf-8") as writer:
        json.dump(json_data, writer, indent=4)
    
    # print(f"{word_name} has motion.json that saved at {output_json_path}")


if __name__ == "__main__":
    print("Executed processor.py file directly.")