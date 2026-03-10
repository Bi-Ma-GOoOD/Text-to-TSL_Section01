from condition_two import reading_json_file

def main():
    print("Welcome to Text-to-Thai_Sign_Language-Section01")
    print("What do you want to do?")
    print("[1] Processing Sign Language Video from clip video in your computer into motion.json file.")
    print("[2] Loading Sign Language video from URL and processing the video into motion.json file.")
    print("[3] Overlay video from motion.json and overlay stick figure on sign language video.")

    choice = input("Enter you choice in number: ")
    
    if (choice == "1"):
        print("Condition 1 working in progress.")
    elif (choice == "2"):
        input_path = input("Insert your input link_word_tsl.json path: ")
        reading_json_file(input_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[System Error] {e}")
