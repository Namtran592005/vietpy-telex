import tkinter as tk
from tkinter import messagebox, ttk
import keyboard
import threading
import platform
import sys
import os
import json
from pystray import Icon as PyTrayIcon, MenuItem as PyTrayMenuItem
from PIL import Image, ImageTk # pip install Pillow

# --- Cấu hình mặc định ---
if platform.system() == "Windows":
    base_config_dir = os.getenv('APPDATA', os.path.expanduser('~')) 
    CONFIG_DIR = os.path.join(base_config_dir, 'VietPyTelex')
elif platform.system() == "Darwin": # macOS
    CONFIG_DIR = os.path.join(os.path.expanduser("~/Library/Application Support"), 'VietPyTelex')
else: # Linux và các OS khác
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", 'VietPyTelex')

os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "enabled": True,
    "auto_start": False,
}

# --- Biến toàn cục để quản lý trạng thái ---
config = DEFAULT_CONFIG.copy()
is_telex_enabled = False
keyboard_hook = None
root = None
status_label = None
tray_icon = None

current_word_buffer = ""

# --- Hàm tải và lưu cấu hình ---
def load_config():
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
            print("Config loaded successfully.")
        except json.JSONDecodeError:
            print("Error decoding config file. Using default config.")
        except Exception as e:
            print(f"An error occurred loading config: {e}. Using default config.")
    else:
        print("Config file not found. Using default config.")

def save_config():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        print("Config saved successfully.")
    except Exception as e:
        print(f"Error saving config: {e}")

# --- Logic gõ Telex Đầy Đủ và Tinh chỉnh ---

# Bảng chuyển đổi ký tự (đã thêm đủ mũ/móc/dấu thanh)
CHAR_MAP = {
    'a': {'s': 'á', 'f': 'à', 'r': 'ả', 'x': 'ã', 'j': 'ạ', 'w': 'ă', 'aa': 'â'},
    'ă': {'s': 'ắ', 'f': 'ằ', 'r': 'ẳ', 'x': 'ẵ', 'j': 'ặ'},
    'â': {'s': 'ấ', 'f': 'ầ', 'r': 'ẩ', 'x': 'ẫ', 'j': 'ậ'},
    'e': {'s': 'é', 'f': 'è', 'r': 'ẻ', 'x': 'ẽ', 'j': 'ẹ', 'ee': 'ê'},
    'ê': {'s': 'ế', 'f': 'ề', 'r': 'ể', 'x': 'ễ', 'j': 'ệ'},
    'i': {'s': 'í', 'f': 'ì', 'r': 'ỉ', 'x': 'ĩ', 'j': 'ị'},
    'o': {'s': 'ó', 'f': 'ò', 'r': 'ỏ', 'x': 'õ', 'j': 'ọ', 'w': 'ơ', 'oo': 'ô'},
    'ơ': {'s': 'ớ', 'f': 'ờ', 'r': 'ở', 'x': 'ỡ', 'j': 'ợ'},
    'ô': {'s': 'ố', 'f': 'ồ', 'r': 'ổ', 'x': 'ỗ', 'j': 'ộ'},
    'u': {'s': 'ú', 'f': 'ù', 'r': 'ủ', 'x': 'ũ', 'j': 'ụ', 'w': 'ư'},
    'ư': {'s': 'ứ', 'f': 'ừ', 'r': 'ử', 'x': 'ữ', 'j': 'ự'},
    'y': {'s': 'ý', 'f': 'ỳ', 'r': 'ỷ', 'x': 'ỹ', 'j': 'ỵ'},
    'd': {'d': 'đ'},
    
    # Bổ sung các chuyển đổi đặc biệt cho nguyên âm đôi/ba và dấu
    # Quy tắc: {vần_gốc: {kí_tự_telex: vần_có_dấu}}
    # Dấu thường đặt vào nguyên âm chính
    'uo': {'w': 'ươ', 's': 'uố', 'f': 'uồ', 'r': 'uổ', 'x': 'uỗ', 'j': 'uộ'},
    'ua': {'s': 'uá', 'f': 'uà', 'r': 'uả', 'x': 'uã', 'j': 'uạ'},
    'ia': {'s': 'iá', 'f': 'ià', 'r': 'iả', 'x': 'iã', 'j': 'iạ'},
    'ie': {'s': 'ié', 'f': 'iè', 'r': 'iẻ', 'x': 'iẽ', 'j': 'iẹ'},
    'uy': {'s': 'úy', 'f': 'ùy', 'r': 'ủy', 'x': 'ũy', 'j': 'ụy'},
    'ao': {'s': 'áo', 'f': 'ào', 'r': 'ảo', 'x': 'ão', 'j': 'ạo'},
    'oe': {'s': 'óe', 'f': 'òe', 'r': 'ỏe', 'x': 'õe', 'j': 'ọe'},
    'ai': {'s': 'ái', 'f': 'ài', 'r': 'ải', 'x': 'ãi', 'j': 'ại'},
    'oi': {'s': 'ói', 'f': 'òi', 'r': 'ỏi', 'x': 'õi', 'j': 'ọi'},
    'ui': {'s': 'úi', 'f': 'ùi', 'r': 'ủi', 'x': 'ũi', 'j': 'ụi'},
    'eo': {'s': 'éo', 'f': 'èo', 'r': 'ẻo', 'x': 'ẽo', 'j': 'ẹo'},
    'eu': {'s': 'éu', 'f': 'èu', 'r': 'ẻu', 'x': 'ẽu', 'j': 'ẹu'},
    'au': {'s': 'áu', 'f': 'àu', 'r': 'ảu', 'x': 'ãu', 'j': 'ạu'},
    'ay': {'s': 'áy', 'f': 'ày', 'r': 'ảy', 'x': 'ãy', 'j': 'ạy'},
    'iu': {'s': 'íu', 'f': 'ìu', 'r': 'ỉu', 'x': 'ĩu', 'j': 'ịu'},
    # Vần 3 ký tự (dấu thường rơi vào ký tự cuối cùng của vần)
    'uyê': {'s': 'uyế', 'f': 'uyề', 'r': 'uyể', 'x': 'uyễ', 'j': 'uyệ'},
    'oai': {'s': 'oái', 'f': 'oài', 'r': 'oải', 'x': 'oãi', 'j': 'oại'},
    'uay': {'s': 'uáy', 'f': 'uày', 'r': 'uảy', 'x': 'uãy', 'j': 'uạy'},
}

# Bảng bỏ dấu từng bước và bỏ dấu mũ/móc
# Key: Ký tự có dấu
# Value: (Ký tự sau khi bỏ dấu thanh, Ký tự sau khi bỏ dấu mũ/móc)
UNACCENT_FULL_MAP = {
    # Nguyên âm không dấu (dùng để bỏ dấu thanh -> không dấu)
    'a': (None, None), 'e': (None, None), 'i': (None, None), 'o': (None, None), 'u': (None, None), 'y': (None, None),
    'd': (None, None), # Cho 'đ'

    # Dấu sắc
    'á': ('a', None), 'ắ': ('ă', 'a'), 'ấ': ('â', 'a'), 'é': ('e', None), 'ế': ('ê', 'e'), 
    'í': ('i', None), 'ó': ('o', None), 'ớ': ('ơ', 'o'), 'ố': ('ô', 'o'), 
    'ú': ('u', None), 'ứ': ('ư', 'u'), 'ý': ('y', None),

    # Dấu huyền
    'à': ('a', None), 'ằ': ('ă', 'a'), 'ầ': ('â', 'a'), 'è': ('e', None), 'ề': ('ê', 'e'),
    'ì': ('i', None), 'ò': ('o', None), 'ờ': ('ơ', 'o'), 'ồ': ('ô', 'o'),
    'ù': ('u', None), 'ừ': ('ư', 'u'), 'ỳ': ('y', None),

    # Dấu hỏi
    'ả': ('a', None), 'ẳ': ('ă', 'a'), 'ẩ': ('â', 'a'), 'ẻ': ('e', None), 'ể': ('ê', 'e'),
    'ỉ': ('i', None), 'ỏ': ('o', None), 'ở': ('ơ', 'o'), 'ổ': ('ô', 'o'),
    'ủ': ('u', None), 'ử': ('ư', 'u'), 'ỷ': ('y', None),

    # Dấu ngã
    'ã': ('a', None), 'ẵ': ('ă', 'a'), 'ẫ': ('â', 'a'), 'ẽ': ('e', None), 'ễ': ('ê', 'e'),
    'ĩ': ('i', None), 'õ': ('o', None), 'ỡ': ('ơ', 'o'), 'ỗ': ('ô', 'o'),
    'ũ': ('u', None), 'ữ': ('ư', 'u'), 'ỹ': ('y', None),

    # Dấu nặng
    'ạ': ('a', None), 'ặ': ('ă', 'a'), 'ậ': ('â', 'a'), 'ẹ': ('e', None), 'ệ': ('ê', 'e'),
    'ị': ('i', None), 'ọ': ('o', None), 'ợ': ('ơ', 'o'), 'ộ': ('ô', 'o'),
    'ụ': ('u', None), 'ự': ('ư', 'u'), 'ỵ': ('y', None),

    # Ký tự có mũ/móc nhưng không có dấu thanh
    'ă': (None, 'a'), 'â': (None, 'a'), 'ê': (None, 'e'), 'ô': (None, 'o'), 'ơ': (None, 'o'), 'ư': (None, 'u'),
    'đ': (None, 'd')
}

ACCENT_MARKS = ['s', 'f', 'r', 'x', 'j']
SPECIAL_CHAR_RULES = ['w'] # 'w' cho ă, ơ, ư

# Các nguyên âm được sắp xếp theo thứ tự ưu tiên (ưu tiên hơn để đặt dấu)
VOWELS_PRIORITY = "ăâêôơưaeyiou" 

# Hàm tìm vị trí nguyên âm chính để đặt dấu
def find_accent_position(word):
    word_lower = word.lower()
    
    # Quy tắc 1: Ưu tiên các nguyên âm có mũ/móc (â, ê, ô, ă, ơ, ư)
    # Duyệt từ phải sang trái để lấy vị trí cuối cùng nếu có nhiều
    for i in range(len(word_lower) - 1, -1, -1):
        if word_lower[i] in "âêôăơư":
            return i

    # Quy tắc 2: Xử lý các vần (nguyên âm đôi/ba) và vị trí đặt dấu
    # Danh sách các vần và vị trí tương đối của dấu (từ 0)
    # Sắp xếp từ dài nhất đến ngắn nhất để tránh bắt nhầm vần con
    vowel_clusters_rules = [
        ("uyê", 2), ("uya", 2), ("oai", 2), ("uay", 2), # Vần 3 ký tự (dấu trên ký tự thứ 3)
        
        ("ươ", 1), ("uô", 1), # Vần 2 ký tự (dấu trên ký tự thứ 2)
        ("ai", 1), ("ao", 1), ("au", 1), ("ay", 1), 
        ("eo", 1), ("eu", 1), ("ia", 1), ("ie", 1), 
        ("iu", 1), ("oe", 1), ("oi", 1), ("ua", 1), 
        ("ue", 1), ("ui", 1), ("uo", 1), ("uy", 1) # ưu tiên y/i cuối
    ]
    
    # Duyệt qua từ từ phải sang trái để tìm vần phù hợp
    for i in range(len(word_lower) - 1, -1, -1):
        for cluster_rule, relative_pos in vowel_clusters_rules:
            cluster_len = len(cluster_rule)
            if i >= cluster_len - 1: # Đảm bảo có đủ ký tự cho vần
                sub_word = word_lower[i - (cluster_len - 1) : i + 1]
                if sub_word == cluster_rule:
                    return (i - (cluster_len - 1)) + relative_pos

    # Quy tắc 3: Nếu không tìm thấy các trường hợp trên, tìm nguyên âm cuối cùng theo VOWELS_PRIORITY
    for i in range(len(word_lower) - 1, -1, -1):
        if word_lower[i] in VOWELS_PRIORITY:
            return i
            
    return -1 # Không tìm thấy nguyên âm

def apply_telex_rule_to_char(char_to_convert_or_cluster, rule_char):
    """Áp dụng quy tắc Telex cho một ký tự hoặc một vần."""
    lower_target = char_to_convert_or_cluster.lower()
    
    if lower_target in CHAR_MAP:
        mapping = CHAR_MAP[lower_target]
        if rule_char in mapping:
            result = mapping[rule_char]
            # Giữ nguyên hoa/thường của ký tự ĐẦU TIÊN trong chuỗi gốc
            return result.upper() if char_to_convert_or_cluster[0].isupper() else result
    return None

def unaccent_char_step_by_step(char_with_accent, is_first_z=True):
    """
    Bỏ dấu của một ký tự theo từng bước.
    is_first_z=True: bỏ dấu thanh.
    is_first_z=False: bỏ dấu mũ/móc.
    """
    lower_char = char_with_accent.lower()
    if lower_char in UNACCENT_FULL_MAP:
        accent_removed, hat_removed = UNACCENT_FULL_MAP[lower_char]
        
        if is_first_z: # Lần nhấn 'z' đầu tiên
            if accent_removed is not None: # Nếu có dấu thanh để bỏ
                return accent_removed.upper() if char_with_accent.isupper() else accent_removed
            elif hat_removed is not None: # Nếu không có dấu thanh nhưng có dấu mũ/móc (vd: 'ă', 'â', 'ê', v.v.)
                return hat_removed.upper() if char_with_accent.isupper() else hat_removed
        else: # Lần nhấn 'z' thứ hai
            if hat_removed is not None: # Ưu tiên bỏ dấu mũ/móc
                return hat_removed.upper() if char_with_accent.isupper() else hat_removed
            
    return char_with_accent # Trả về nguyên nếu không có dấu để bỏ

def apply_word_telex(word_in):
    """
    Áp dụng quy tắc Telex cho một từ.
    Trả về từ đã chuyển đổi hoặc None nếu không có gì thay đổi.
    """
    if not word_in:
        return None

    last_char = word_in[-1].lower()
    
    # 1. Xử lý "dd" -> "đ"
    if last_char == 'd' and len(word_in) >= 2 and word_in[-2].lower() == 'd':
        return word_in[:-2] + apply_telex_rule_to_char('d', 'd')

    # 2. Xử lý bỏ dấu "z"
    if last_char == 'z' and len(word_in) >= 2:
        target_word_base = word_in[:-1] 
        
        any_char_has_accent_mark = False
        for c in target_word_base:
            if c.lower() in UNACCENT_FULL_MAP and UNACCENT_FULL_MAP[c.lower()][0] is not None:
                any_char_has_accent_mark = True
                break
        
        unaccented_word_chars = []
        for c in target_word_base:
            unaccented_word_chars.append(unaccent_char_step_by_step(c, is_first_z=any_char_has_accent_mark))
        
        return "".join(unaccented_word_chars)

    # 3. Xử lý dấu thanh (s, f, r, x, j) và 'w'
    if last_char in ACCENT_MARKS or last_char == 'w':
        word_base = word_in[:-1]
        rule_char = last_char

        if not word_base:
            return None

        accent_pos = find_accent_position(word_base)

        if accent_pos != -1:
            # Lấy ký tự hoặc vần tại vị trí dấu
            char_or_cluster_to_accent = word_base[accent_pos] # Mặc định là ký tự đơn
            
            # Cố gắng tìm vần (cluster) bao gồm accent_pos để áp dụng rule cho vần đó
            found_cluster_start = -1
            found_cluster_len = 0
            
            # Ưu tiên tìm vần dài hơn
            for clus_len in [3, 2]:
                # Kiểm tra xem có vần nào kết thúc tại accent_pos hoặc bắt đầu gần đó không
                start_check_idx = max(0, accent_pos - clus_len + 1)
                for start_idx in range(start_check_idx, accent_pos + 1):
                    temp_cluster = word_base[start_idx : start_idx + clus_len].lower()
                    if temp_cluster in CHAR_MAP: # Nếu có rule cho vần này
                        found_cluster_start = start_idx
                        found_cluster_len = clus_len
                        char_or_cluster_to_accent = word_base[found_cluster_start : found_cluster_start + found_cluster_len]
                        break
                if found_cluster_start != -1:
                    break

            new_transformed_segment = apply_telex_rule_to_char(char_or_cluster_to_accent, rule_char)

            if new_transformed_segment:
                if found_cluster_start != -1:
                    return word_base[:found_cluster_start] + new_transformed_segment + word_base[found_cluster_start + found_cluster_len:]
                else: # Xử lý ký tự đơn
                    return word_base[:accent_pos] + new_transformed_segment + word_base[accent_pos+1:]
    
    # 4. Xử lý chữ cái kép đặc biệt (aa -> â, ee -> ê, oo -> ô)
    if len(word_in) >= 2 and word_in[-1].lower() == word_in[-2].lower() and word_in[-1].lower() in ['a', 'e', 'o']:
        double_char_rule = word_in[-2:].lower()
        
        if double_char_rule[0] in CHAR_MAP and double_char_rule in CHAR_MAP[double_char_rule[0]]:
            converted_char = CHAR_MAP[double_char_rule[0]][double_char_rule]
            return word_in[:-2] + (converted_char.upper() if word_in[-2].isupper() else converted_char)

    return None

# --- Bộ xử lý phím toàn cục ---
def process_keyboard_event(e):
    global current_word_buffer

    if not is_telex_enabled:
        return

    key_name = e.name 

    # Xử lý các phím đặc biệt (ngắt từ)
    if key_name in ['space', 'enter', 'tab']:
        if current_word_buffer:
            transformed_word = apply_word_telex(current_word_buffer)
            if transformed_word:
                for _ in range(len(current_word_buffer)):
                    keyboard.send('backspace')
                keyboard.write(transformed_word)
            current_word_buffer = "" # Reset buffer
            
            keyboard.send(key_name) 
            return
        current_word_buffer = ""
        keyboard.send(key_name)
        return

    elif key_name == 'backspace':
        if current_word_buffer:
            current_word_buffer = current_word_buffer[:-1]
        return 

    # Xử lý phím mũi tên và các phím điều khiển khác
    if len(key_name) > 1:
        current_word_buffer = "" 
        return 

    # Nếu là ký tự gõ thông thường (chữ cái, số, dấu câu)
    char = key_name 
    
    current_word_buffer += char

    transformed_word = apply_word_telex(current_word_buffer)
    if transformed_word:
        for _ in range(len(current_word_buffer)):
            keyboard.send('backspace')
        keyboard.write(transformed_word)
        current_word_buffer = transformed_word
    # Nếu không chuyển đổi, ký tự đã được thêm vào buffer và được gõ bình thường bởi hệ thống.

# --- Quản lý lắng nghe bàn phím ---
def start_keyboard_listener():
    global keyboard_hook
    if keyboard_hook is None:
        print("Starting keyboard listener...")
        keyboard_hook = keyboard.on_press(lambda e: process_keyboard_event(e))
        print("Keyboard listener started.")

def stop_keyboard_listener():
    global keyboard_hook
    if keyboard_hook:
        print("Stopping keyboard listener...")
        keyboard.unhook(keyboard_hook)
        keyboard_hook = None
        print("Keyboard listener stopped.")

def set_telex_state(enabled):
    global is_telex_enabled, config
    
    if is_telex_enabled == enabled:
        return

    is_telex_enabled = enabled
    config["enabled"] = enabled
    save_config()

    if root and status_label:
        if enabled:
            status_label.config(text="Trạng thái: Đang bật", style="Green.TLabel")
            start_keyboard_listener()
        else:
            status_label.config(text="Trạng thái: Đang tắt", style="Red.TLabel")
            stop_keyboard_listener()
    
    update_tray_menu()

# --- Giao diện người dùng (Tkinter) ---
def create_main_window():
    global root, status_label
    root = tk.Tk()
    root.title("VietPy Telex")
    root.geometry("280x180")
    root.resizable(False, False)

    style = ttk.Style()
    style.configure("Green.TLabel", foreground="green")
    style.configure("Red.TLabel", foreground="red")
    style.configure("TLabel", font=("Arial", 14))

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill="both", expand=True)

    status_label = ttk.Label(main_frame, text="")
    status_label.pack(pady=20)

    toggle_button = ttk.Button(main_frame, text="Bật/Tắt gõ tiếng Việt", command=lambda: set_telex_state(not is_telex_enabled))
    toggle_button.pack(pady=5)

    tray_button = ttk.Button(main_frame, text="Thu nhỏ xuống khay", command=lambda: root.withdraw() if root else None)
    tray_button.pack(pady=5)

    def on_closing():
        if root and messagebox.askokcancel("Thoát VietPy Telex", "Bạn có muốn thoát hoàn toàn VietPy Telex không?"):
            stop_keyboard_listener()
            if tray_icon:
                tray_icon.stop()
            if root:
                root.destroy()
            sys.exit(0)

    if root:
        root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Quản lý Icon khay hệ thống (pystray) ---
def setup_tray_icon():
    global tray_icon

    image = Image.new('RGB', (64, 64), (0, 100, 255))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    draw.text((10, 5), "V", font=font, fill=(255, 255, 255))

    menu_items = (
        PyTrayMenuItem('Mở cửa sổ chính', lambda: root.deiconify() if root else None),
        PyTrayMenuItem(
            'Bật gõ tiếng Việt', 
            lambda icon, item: set_telex_state(True), 
            checked=lambda item: is_telex_enabled,
            radio=True
        ),
        PyTrayMenuItem(
            'Tắt gõ tiếng Việt', 
            lambda icon, item: set_telex_state(False), 
            checked=lambda item: not is_telex_enabled,
            radio=True
        ),
        PyTrayMenuItem('Thoát', lambda: root.quit() if root else None)
    )
    
    tray_icon = PyTrayIcon("VietPy Telex", image, "VietPy Telex", menu_items)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def update_tray_menu():
    pass

# --- Hàm chính ---
def main():
    load_config()
    create_main_window()
    set_telex_state(config["enabled"])
    setup_tray_icon()
    
    if root:
        root.mainloop()

if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("Cảnh báo: Không chạy với quyền quản trị. Gõ tiếng Việt có thể không hoạt động chính xác ở một số ứng dụng.")
        except Exception as e:
            print(f"Lỗi khi kiểm tra quyền admin: {e}")

    main()