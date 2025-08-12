# --- vietpy_telex_gui_fixed_v6.py ---
# Sửa lỗi đặt dấu thanh sai vị trí trên các cụm nguyên âm (VD: lại, nghĩa).
# Run: python vietpy_telex_gui_fixed_v6.py

import sys
import os
import json
import platform
import keyboard
import winsound
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSystemTrayIcon, QMenu, QFileDialog,
    QMessageBox, QCheckBox, QDialog, QGridLayout, QRadioButton, QGroupBox
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QFont, QCloseEvent, QPainter, QColor, QActionGroup
from PyQt6.QtCore import Qt, QCoreApplication
from typing import Optional
from shutil import copy2

# --- Cấu hình mặc định (GIỮ NGUYÊN) ---
if platform.system() == "Windows":
    base_config_dir = os.getenv('APPDATA', os.path.expanduser('~'))
    CONFIG_DIR = os.path.join(base_config_dir, 'VietPyTelex')
elif platform.system() == "Darwin": # macOS
    CONFIG_DIR = os.path.join(os.path.expanduser("~/Library/Application Support"), 'VietPyTelex')
else: # Linux và các OS khác
    CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", 'VietPyTelex')
os.makedirs(CONFIG_DIR, exist_ok=True)
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
os.makedirs(SOUNDS_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG = { 
    "enabled": False, 
    "auto_start": False, 
    "hotkey": "ctrl_shift", 
    "theme": "light", 
    "silent_start": False,
    "sound_enabled": True,
    "sound_file": "default.wav",
    "custom_sound_file": ""
}

# --- Biến toàn cục (GIỮ NGUYÊN) ---
config = DEFAULT_CONFIG.copy()
is_telex_enabled = False
keyboard_hook = None
current_word_buffer = ""
active_hotkey_hook = None

# --- Hàm tải và lưu cấu hình (GIỮ NGUYÊN) ---
def load_config():
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: config.update(json.load(f))
        except (json.JSONDecodeError, IOError) as e: print(f"Error loading config: {e}. Using default.")
    else: print("Config file not found. Using default config.")

def save_config():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False, indent=4)
    except IOError as e: print(f"Error saving config: {e}")

# --- Telex core (CẬP NHẬT) ---

# CHAR_MAP, TONE_REMOVE_MAP, HAT_REMOVE_MAP, ACCENT_MARKS (GIỮ NGUYÊN)
CHAR_MAP = {
    'a': {'s': 'á', 'f': 'à', 'r': 'ả', 'x': 'ã', 'j': 'ạ', 'w': 'ă', 'aa': 'â'}, 'ă': {'s': 'ắ', 'f': 'ằ', 'r': 'ẳ', 'x': 'ẵ', 'j': 'ặ'},
    'â': {'s': 'ấ', 'f': 'ầ', 'r': 'ẩ', 'x': 'ẫ', 'j': 'ậ'}, 'e': {'s': 'é', 'f': 'è', 'r': 'ẻ', 'x': 'ẽ', 'j': 'ẹ', 'ee': 'ê'},
    'ê': {'s': 'ế', 'f': 'ề', 'r': 'ể', 'x': 'ễ', 'j': 'ệ'}, 'i': {'s': 'í', 'f': 'ì', 'r': 'ỉ', 'x': 'ĩ', 'j': 'ị'},
    'o': {'s': 'ó', 'f': 'ò', 'r': 'ỏ', 'x': 'õ', 'j': 'ọ', 'w': 'ơ', 'oo': 'ô'}, 'ơ': {'s': 'ớ', 'f': 'ờ', 'r': 'ở', 'x': 'ỡ', 'j': 'ợ'},
    'ô': {'s': 'ố', 'f': 'ồ', 'r': 'ổ', 'x': 'ỗ', 'j': 'ộ'}, 'u': {'s': 'ú', 'f': 'ù', 'r': 'ủ', 'x': 'ũ', 'j': 'ụ', 'w': 'ư'},
    'ư': {'s': 'ứ', 'f': 'ừ', 'r': 'ử', 'x': 'ữ', 'j': 'ự'}, 'y': {'s': 'ý', 'f': 'ỳ', 'r': 'ỷ', 'x': 'ỹ', 'j': 'ỵ'},
    'd': {'d': 'đ'}, 'uo': {'w': 'ươ'}, 'ia': {'w': 'ưa'}, 'uy': {'s': 'úy', 'f': 'ùy', 'r': 'ủy', 'x': 'ũy', 'j': 'ụy'},
    'uyê': {'s': 'uyế', 'f': 'uyề', 'r': 'uyể', 'x': 'uyễ', 'j': 'uyệ'}, 'oai': {'s': 'oái', 'f': 'oài', 'r': 'oải', 'x': 'oãi', 'j': 'oại'},
    'uay': {'s': 'uáy', 'f': 'uày', 'r': 'uảy', 'x': 'uãy', 'j': 'uạy'},
}
TONE_REMOVE_MAP = {
    'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a', 'ắ': 'ă', 'ằ': 'ă', 'ẳ': 'ă', 'ẵ': 'ă', 'ặ': 'ă',
    'ấ': 'â', 'ầ': 'â', 'ẩ': 'â', 'ẫ': 'â', 'ậ': 'â', 'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'ế': 'ê', 'ề': 'ê', 'ể': 'ê', 'ễ': 'ê', 'ệ': 'ê', 'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o', 'ớ': 'ơ', 'ờ': 'ơ', 'ở': 'ơ', 'ỡ': 'ơ', 'ợ': 'ơ',
    'ố': 'ô', 'ồ': 'ô', 'ổ': 'ô', 'ỗ': 'ô', 'ộ': 'ô', 'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ứ': 'ư', 'ừ': 'ư', 'ử': 'ư', 'ữ': 'ư', 'ự': 'ư', 'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
}
HAT_REMOVE_MAP = {'ă': 'a', 'â': 'a', 'ê': 'e', 'ô': 'o', 'ơ': 'o', 'ư': 'u', 'đ': 'd'}
ACCENT_MARKS = ['s', 'f', 'r', 'x', 'j']

# === CÁC HẰNG SỐ MỚI ĐỂ XÁC ĐỊNH VỊ TRÍ ĐẶT DẤU CHUẨN ===
VOWELS_WITH_HAT_OR_HOOK = "ăâêôơư"
VOWELS_PLAIN = "aeiouy"

# Danh sách các cụm nguyên âm và vị trí ưu tiên đặt dấu (index tương đối từ đầu cụm)
# Sắp xếp từ dài nhất đến ngắn nhất để đảm bảo `uyê` được xử lý trước `yê`.
VOWEL_CLUSTERS_ACCENT_PRIORITY = [
    # Cụm 3 chữ
    ("uyê", 2),  # khuy**ế**n
    ("oai", 1),  # h**oà**i
    ("uay", 1),  # kh**uấ**y
    ("oay", 1),  # x**oá**y
    ("iêu", 1),  # h**iế**u
    ("yêu", 1),  # **yế**u
    ("ươi", 2),  # t**ưởi**
    ("uôi", 2),  # c**uối**
    ("ươu", 2),  # h**ượu**

    # Cụm 2 chữ (quan trọng nhất để sửa lỗi)
    ("qu", -1),  # 'qu' là một cụm phụ âm-nguyên âm đặc biệt, dấu luôn đặt ở nguyên âm sau nó
    ("gi", -1),  # Tương tự 'qu', dấu đặt ở nguyên âm sau 'i'
    
    ("ia", 0),   # ngh**ĩ**a
    ("yê", 1),   # y**ế**n
    ("iê", 1),   # t**iế**ng
    ("ua", 0),   # m**ú**a
    ("uô", 1),   # m**uố**n
    ("ưa", 0),   # m**ư**a
    ("ươ", 1),   # m**ướ**n
    
    ("ai", 0),   # l**ạ**i
    ("ao", 0),   # l**à**o
    ("au", 0),   # s**á**u
    ("ay", 0),   # g**ầ**y
    
    ("ei", 0),   # (ít dùng)
    ("eo", 0),   # k**é**o
    ("eu", 0),   # tr**é**o
    
    ("oi", 0),   # t**ô**i
    ("oa", 0),   # h**ò**a
    ("oe", 0),   # l**o**e
    ("oy", 0),   # (ít dùng)
    
    ("ui", 0),   # t**ú**i
    ("uy", 1),   # q**uý**nh
    ("uu", 0),   # (ít dùng)
    
    ("iu", 0),   # r**ì**u
]

# === HÀM find_main_vowel_position ĐÃ ĐƯỢC VIẾT LẠI HOÀN TOÀN ===
# === HÀM find_main_vowel_position ĐÃ ĐƯỢC NÂNG CẤP LẦN CUỐI ===
def find_main_vowel_position(word: str) -> int:
    """
    Tìm vị trí của nguyên âm chính để đặt dấu thanh, tuân thủ quy tắc âm tiết đóng/mở.
    """
    word_lower = word.lower()
    
    # 1. Ưu tiên cao nhất: các nguyên âm có mũ/móc (ă, â, ê, ô, ơ, ư)
    for i in range(len(word_lower) - 1, -1, -1):
        if word_lower[i] in VOWELS_WITH_HAT_OR_HOOK:
            return i
            
    # 2. Xử lý các cụm nguyên âm, có xét đến âm tiết đóng/mở
    found_cluster_pos = -1
    best_match_pos = -1

    for cluster, default_relative_pos in VOWEL_CLUSTERS_ACCENT_PRIORITY:
        pos = word_lower.rfind(cluster)
        if pos != -1:
            # Quy tắc đặc biệt cho cụm 'gi' và 'qu'
            if default_relative_pos == -1: # Dấu hiệu cho 'gi' và 'qu'
                # Tìm nguyên âm ngay sau 'gi' hoặc 'qu'
                start_search = pos + len(cluster)
                for i in range(start_search, len(word_lower)):
                    if word_lower[i] in VOWELS_WITH_HAT_OR_HOOK + VOWELS_PLAIN:
                        # Phân tích phần còn lại của từ để đặt dấu chính xác
                        sub_word_analysis = word_lower[i:]
                        sub_pos = find_main_vowel_position(sub_word_analysis)
                        return i + sub_pos if sub_pos != -1 else i
                continue # Nếu không có nguyên âm nào sau, bỏ qua

            # === LOGIC MỚI: XỬ LÝ ÂM TIẾT ĐÓNG/MỞ ===
            cluster_len = len(cluster)
            
            # Kiểm tra xem có phụ âm đi theo sau cụm không
            is_closed_syllable = (pos + cluster_len < len(word_lower)) and \
                                 (word_lower[pos + cluster_len] not in VOWELS_PLAIN)

            # Quy tắc: Với nguyên âm đôi, nếu âm tiết đóng, dấu đặt ở nguyên âm thứ 2.
            # Áp dụng cho các cụm có `a,o,e,u` đứng đầu.
            if cluster_len == 2 and is_closed_syllable:
                 # Ghi đè quy tắc, đặt dấu vào ký tự thứ 2 (index 1)
                 best_match_pos = pos + 1
                 return best_match_pos

            # Nếu không, áp dụng quy tắc mặc định
            best_match_pos = pos + default_relative_pos
            return best_match_pos

    # 3. Trường hợp cuối cùng: tìm nguyên âm đơn cuối cùng
    for i in range(len(word_lower) - 1, -1, -1):
        if word_lower[i] in VOWELS_PLAIN:
            return i
            
    return -1

# Các hàm phụ trợ (GIỮ NGUYÊN)
def transform_char_case(original_char, transformed_char_base):
    if not original_char or not transformed_char_base: return transformed_char_base
    if original_char.isupper(): return transformed_char_base.upper()
    return transformed_char_base.lower()

def apply_telex_rule_to_char_or_cluster(target_segment, rule_char):
    lower_target = target_segment.lower()
    if lower_target in CHAR_MAP and rule_char in CHAR_MAP[lower_target]:
        result = CHAR_MAP[lower_target][rule_char]
        if target_segment.isupper() and len(target_segment) > 1: return result.upper()
        return transform_char_case(target_segment[0], result)
    return None

def _unaccent_char_logic(char_input):
    lower_char = char_input.lower()
    removed_tone_char = TONE_REMOVE_MAP.get(lower_char)
    if removed_tone_char and removed_tone_char != lower_char: return transform_char_case(char_input, removed_tone_char)
    removed_hat_char = HAT_REMOVE_MAP.get(lower_char)
    if removed_hat_char and removed_hat_char != lower_char: return transform_char_case(char_input, removed_hat_char)
    return char_input

def apply_unaccent_rule(word_in):
    main_vowel_pos = find_main_vowel_position(word_in)
    if main_vowel_pos == -1: return word_in
    original_char_at_pos = word_in[main_vowel_pos]
    transformed_char = _unaccent_char_logic(original_char_at_pos)
    if transformed_char == original_char_at_pos: return word_in
    return word_in[:main_vowel_pos] + transformed_char + word_in[main_vowel_pos+1:]

# Hàm apply_word_telex (GIỮ NGUYÊN - nó đã sử dụng find_main_vowel_position)
def apply_word_telex(word_in):
    if not word_in: return None
    last_char = word_in[-1].lower()
    word_base = word_in[:-1]
    if last_char == 'd' and len(word_in) >= 2 and word_in[-2].lower() == 'd':
        return word_in[:-2] + apply_telex_rule_to_char_or_cluster('d', 'd')
    if last_char == 'z':
        if not word_base: return None
        return apply_unaccent_rule(word_base)
    if last_char == 'w':
        if not word_base: return None
        for length in range(2, 0, -1):
            if len(word_base) >= length:
                segment_to_check = word_base[-length:]
                transformed = apply_telex_rule_to_char_or_cluster(segment_to_check, 'w')
                if transformed: return word_base[:-length] + transformed
        return None
    if last_char in ACCENT_MARKS:
        if not word_base: return None
        accent_pos = find_main_vowel_position(word_base)
        if accent_pos != -1:
            char_to_accent = word_base[accent_pos]
            for cluster_rule, _ in VOWEL_CLUSTERS_ACCENT_PRIORITY:
                 # Logic for handling full clusters like uyê is complex but find_main_vowel_position helps simplify
                 # Let's try to accent the single char first
                 pass
            transformed_char = apply_telex_rule_to_char_or_cluster(char_to_accent, last_char)
            if transformed_char:
                return word_base[:accent_pos] + transformed_char + word_base[accent_pos+1:]
    if len(word_in) >= 2 and word_in[-1].lower() == word_in[-2].lower():
        double_char = word_in[-1].lower()
        if double_char in ['a', 'e', 'o']:
            rule = double_char * 2
            transformed = apply_telex_rule_to_char_or_cluster(double_char, rule)
            if transformed: return word_in[:-2] + transform_char_case(word_in[-2], transformed)
    return None

# --- Keyboard handling và các phần còn lại (GIỮ NGUYÊN) ---
# ... (Toàn bộ phần code từ process_keyboard_event trở đi không thay đổi) ...
def process_keyboard_event(e):
    global current_word_buffer
    if not is_telex_enabled: return False
    if e.event_type != keyboard.KEY_DOWN: return False
    key_name = e.name
    if (keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt')) and len(key_name) == 1:
        current_word_buffer = "" 
        return False
    if key_name in ['space', 'enter', 'tab']:
        if current_word_buffer:
            # We don't do a final transform on word-break keys anymore. 
            # Transformations happen live.
            pass
        current_word_buffer = ""
        return False 
    elif key_name == 'backspace':
        if current_word_buffer:
            current_word_buffer = current_word_buffer[:-1]
        return False
    if len(key_name) > 1 and key_name not in ['space', 'enter', 'tab', 'backspace']:
        current_word_buffer = ""
        return False
    char = e.name
    current_word_buffer += char
    transformed_word = apply_word_telex(current_word_buffer)
    if transformed_word and transformed_word != current_word_buffer:
        keyboard.write('\b' * len(current_word_buffer))
        keyboard.write(transformed_word)
        current_word_buffer = transformed_word
        return True
    # Logic for re-applying accents
    elif len(current_word_buffer) > 1 and current_word_buffer[-1].lower() in ACCENT_MARKS:
        base = current_word_buffer[:-1]
        key = current_word_buffer[-1].lower()
        pos = find_main_vowel_position(base)
        if pos != -1:
            char_to_accent = base[pos]
            transformed_char = apply_telex_rule_to_char_or_cluster(char_to_accent, key)
            if transformed_char:
                new_word = base[:pos] + transformed_char + base[pos+1:]
                keyboard.write('\b' * len(current_word_buffer))
                keyboard.write(new_word)
                current_word_buffer = new_word
                return True
    return False

def start_keyboard_listener():
    global keyboard_hook, current_word_buffer
    if keyboard_hook is None:
        print("Starting keyboard listener...")
        current_word_buffer = ""
        keyboard_hook = keyboard.on_press(process_keyboard_event, suppress=False) 
        print("Keyboard listener started.")

def stop_keyboard_listener():
    global keyboard_hook
    if keyboard_hook:
        print("Stopping keyboard listener...")
        keyboard.unhook(keyboard_hook)
        keyboard_hook = None
        print("Keyboard listener stopped.")
        
# --- Các hàm và lớp GUI còn lại không thay đổi ---
def add_to_startup():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            script_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            startup_command = f'"{script_path}"'
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "VietPyTelex", 0, winreg.REG_SZ, startup_command)
            return True
        except (ImportError, OSError) as e:
            print(f"Error adding to startup: {e}")
    return False

def remove_from_startup():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.DeleteValue(reg_key, "VietPyTelex")
            return True
        except (ImportError, FileNotFoundError):
            return True
        except OSError as e:
            print(f"Error removing from startup: {e}")
    return False
    

class SettingsWindow(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt VietPy Telex")
        self.setFixedSize(400, 440)  # Tăng kích thước cửa sổ
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.init_ui()
        self.load_settings_ui()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        theme = config.get("theme", "light")
        if theme == "dark":
            self.setStyleSheet("""
                QDialog { 
                    background-color: #2b2b2b; 
                    color: #dcdcdc; 
                }
                QGroupBox { 
                    font-family: 'Segoe UI', Arial; 
                    font-size: 9pt; 
                    border: 1px solid #4a4a4a; 
                    border-radius: 4px; 
                    margin-top: 10px;
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    subcontrol-position: top left; 
                    padding: 0 4px; 
                    color: #a9b7c6;
                    background-color: #2b2b2b; /* Phải trùng với màu nền của QDialog */
                }
                QCheckBox, QRadioButton, QLabel { 
                    font-family: 'Segoe UI', Arial; 
                    font-size: 9pt; 
                    padding: 3px; 
                    color: #dcdcdc; 
                    background: transparent; 
                }
                QCheckBox::indicator, QRadioButton::indicator {
                    width: 16px; height: 16px;
                    background: #3c3f41; 
                    border: 1px solid #555;
                }
                QRadioButton::indicator {
                    border-radius: 8px; /* Nút radio hình tròn */
                }
                QCheckBox::indicator {
                    border-radius: 3px; /* Hộp kiểm bo góc nhẹ */
                }
                QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                    background: #4CAF50; /* Giữ màu xanh lá nhất quán với icon */
                    border: 1px solid #4CAF50;
                }
                QPushButton { 
                    background-color: #3c3f41; 
                    border: 1px solid #666; 
                    border-radius: 4px; 
                    padding: 1px 12px; 
                    min-width: 80px; 
                    font-size: 9pt; 
                    font-family: 'Segoe UI', Arial; 
                    color: #dcdcdc; 
                }
                QPushButton:hover { 
                    background-color: #4e5254; 
                    border-color: #777;
                }
                QPushButton:pressed { 
                    background-color: #313335; 
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f0f0f0; }
                QGroupBox { font-family: "Segoe UI", Arial; font-size: 9pt; border: 1px solid #c0c0c0; border-radius: 4px; margin-top: 10px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; color: #333; }
                QCheckBox, QRadioButton, QLabel { font-family: "Segoe UI", Arial; font-size: 9pt; padding: 3px; color: #222; }
                QPushButton { background-color: #e1e1e1; border: 1px solid #b0b0b0; border-radius: 4px; padding: 6px 12px; min-width: 80px; font-size: 9pt; font-family: "Segoe UI", Arial; }
                QPushButton:hover { background-color: #e9e9e9; }
                QPushButton:pressed { background-color: #d1d1d1; }
            """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(8)
        # Startup group
        startup_group = QGroupBox("Khởi động")
        startup_layout = QVBoxLayout(startup_group)
        startup_layout.setSpacing(4)
        startup_layout.setContentsMargins(10, 8, 10, 8)
        self.auto_start_checkbox = QCheckBox("Khởi động cùng hệ thống")
        if platform.system() != "Windows":
            self.auto_start_checkbox.setDisabled(True)
            self.auto_start_checkbox.setText("Khởi động cùng hệ thống (chỉ hỗ trợ Windows)")
        self.auto_start_checkbox.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        startup_layout.addWidget(self.auto_start_checkbox)
        self.silent_start_checkbox = QCheckBox("Khởi động im lặng (ẩn cửa sổ)")
        if platform.system() != "Windows":
            self.silent_start_checkbox.setDisabled(True)
        self.silent_start_checkbox.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        startup_layout.addWidget(self.silent_start_checkbox)
        main_layout.addWidget(startup_group)
        # Hotkey group
        hotkey_group = QGroupBox("Phím chuyển")
        hotkey_layout = QVBoxLayout(hotkey_group)
        hotkey_layout.setSpacing(4)
        hotkey_layout.setContentsMargins(10, 8, 10, 8)
        self.ctrl_shift_radio = QRadioButton("CTRL + SHIFT")
        self.alt_z_radio = QRadioButton("ALT + Z")
        self.ctrl_shift_radio.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        self.alt_z_radio.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        hotkey_layout.addWidget(self.ctrl_shift_radio)
        hotkey_layout.addWidget(self.alt_z_radio)
        main_layout.addWidget(hotkey_group)
        # Theme group
        theme_group = QGroupBox("Giao diện")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(4)
        theme_layout.setContentsMargins(10, 8, 10, 8)
        self.theme_light_radio = QRadioButton("Sáng (Light)")
        self.theme_dark_radio = QRadioButton("Tối (Dark)")
        self.theme_light_radio.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        self.theme_dark_radio.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        theme_layout.addWidget(self.theme_light_radio)
        theme_layout.addWidget(self.theme_dark_radio)
        main_layout.addWidget(theme_group)
        
        # Nhóm cài đặt âm thanh
        sound_group = QGroupBox("Âm thanh")
        sound_layout = QVBoxLayout(sound_group)
        sound_layout.setSpacing(4)
        sound_layout.setContentsMargins(10, 9, 10, 9)
        
        self.sound_enabled_checkbox = QCheckBox("Bật âm thanh khi chuyển đổi")
        self.sound_enabled_checkbox.setStyleSheet("padding-left:2px; margin-bottom:2px;")
        sound_layout.addWidget(self.sound_enabled_checkbox)
        
        sound_file_layout = QHBoxLayout()
        self.sound_path_label = QLabel("Không có file âm thanh")
        self.sound_path_label.setStyleSheet("color: #666; font-style: italic;")
        sound_file_layout.addWidget(self.sound_path_label)
        
        self.browse_sound_button = QPushButton("Chọn file...")
        self.browse_sound_button.clicked.connect(self.browse_sound_file)
        sound_file_layout.addWidget(self.browse_sound_button)
        sound_layout.addLayout(sound_file_layout)
        
        self.reset_sound_button = QPushButton("Về mặc định")
        self.reset_sound_button.clicked.connect(self.reset_sound_file)
        self.reset_sound_button.setStyleSheet("padding: 3px 8px; min-width: 60px;")
        sound_layout.addWidget(self.reset_sound_button)
        
        main_layout.addWidget(sound_group)
        main_layout.addStretch(1)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        save_button = QPushButton("Lưu và Đóng")
        save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def load_settings_ui(self):
        self.auto_start_checkbox.setChecked(config.get("auto_start", False))
        self.silent_start_checkbox.setChecked(config.get("silent_start", False))
        self.ctrl_shift_radio.setChecked(config.get("hotkey", "ctrl_shift") == "ctrl_shift")
        self.alt_z_radio.setChecked(config.get("hotkey", "ctrl_shift") == "alt_z")
        theme = config.get("theme", "light")
        self.theme_light_radio.setChecked(theme == "light")
        self.theme_dark_radio.setChecked(theme == "dark")
        self.sound_enabled_checkbox.setChecked(config.get("sound_enabled", True))
        custom_sound = config.get("custom_sound_file", "")
        if custom_sound:
            self.sound_path_label.setText(os.path.basename(custom_sound))
        else:
            self.sound_path_label.setText(config.get("sound_file", "default.wav"))
            
    def browse_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file âm thanh",
            os.path.expanduser("~"),
            "File âm thanh (*.wav);;Tất cả file (*.*)"
        )
        if file_path:
            try:
                # Copy file vào thư mục sounds với tên mới
                sound_file_name = f"custom_{os.path.basename(file_path)}"
                new_path = os.path.join(SOUNDS_DIR, sound_file_name)
                copy2(file_path, new_path)
                config["custom_sound_file"] = new_path
                self.sound_path_label.setText(os.path.basename(file_path))
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể sử dụng file âm thanh: {str(e)}")
                
    def reset_sound_file(self):
        config["custom_sound_file"] = ""
        config["sound_file"] = "default.wav"
        self.sound_path_label.setText("default.wav")


    def save_and_close(self):
        new_hotkey = "alt_z" if self.alt_z_radio.isChecked() else "ctrl_shift"
        if config.get("hotkey") != new_hotkey:
            config["hotkey"] = new_hotkey
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, VietPyTelexApp):
                    widget.update_hotkey_listener()
                    break
        new_auto_start = self.auto_start_checkbox.isChecked()
        new_silent_start = self.silent_start_checkbox.isChecked()
        config["silent_start"] = new_silent_start
        
        # Âm thanh
        config["sound_enabled"] = self.sound_enabled_checkbox.isChecked()
        
        # Theme
        new_theme = "dark" if self.theme_dark_radio.isChecked() else "light"
        if config.get("theme") != new_theme:
            config["theme"] = new_theme
            for widget in QApplication.topLevelWidgets():
                # Chỉ gọi cho VietPyTelexApp hoặc SettingsWindow
                if isinstance(widget, (VietPyTelexApp, SettingsWindow)):
                    widget.apply_stylesheet()
        if platform.system() == "Windows":
            current_auto_start_status = is_in_startup()
            if new_auto_start != current_auto_start_status:
                if new_auto_start:
                    if add_to_startup():
                        config["auto_start"] = True
                    else:
                        QMessageBox.warning(self, "Lỗi khởi động", "Không thể thêm ứng dụng vào danh sách khởi động. Vui lòng thử lại với quyền Administrator.")
                        self.auto_start_checkbox.setChecked(False)
                        config["auto_start"] = False
                else:
                    if remove_from_startup():
                        config["auto_start"] = False
                    else:
                        QMessageBox.warning(self, "Lỗi khởi động", "Không thể gỡ ứng dụng khỏi danh sách khởi động.")
                        self.auto_start_checkbox.setChecked(True)
                        config["auto_start"] = True
            else:
                config["auto_start"] = new_auto_start
        save_config()
        self.accept()

    def closeEvent(self, a0: Optional[QCloseEvent]):
        self.save_and_close()
        if a0:
            a0.accept()

class VietPyTelexApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VietPy Telex")
        self.setFixedSize(380, 170)
        self.settings_window: Optional[SettingsWindow] = None
        self.app_icon_base = self.load_app_icon()
        self.icon_vietnamese = self.create_dynamic_icon('V', '#4CAF50')
        self.icon_english = self.create_dynamic_icon('E', '#D32F2F')
        load_config()  # Đảm bảo config đã load trước khi tạo UI
        self.init_ui()
        self.apply_stylesheet()  # Đảm bảo theme đúng ngay khi khởi tạo
        self.init_tray_icon()
        self.load_settings()
        self.update_hotkey_listener()

    def create_dynamic_icon(self, text: str, color_hex: str) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Segoe UI", 36, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(color_hex))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def load_app_icon(self) -> QIcon:
        icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), 'icon.png')
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        else:
            print("Warning: icon.png not found. Using dynamic icon.")
            return self.create_dynamic_icon('VN', '#00579c')

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setWindowIcon(self.app_icon_base)
        self.apply_stylesheet()
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setHorizontalSpacing(10)
        main_layout.setVerticalSpacing(5)
        control_group = QGroupBox("Điều khiển")
        control_layout = QVBoxLayout(control_group)
        # --- Trạng thái đẹp hơn: icon + text lớn ---
        status_row_layout = QHBoxLayout()
        status_row_layout.setSpacing(8)
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(32, 32)
        self.status_text_label = QLabel()
        self.status_text_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.status_text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        status_row_layout.addWidget(self.status_icon_label)
        status_row_layout.addWidget(self.status_text_label)
        status_row_layout.addStretch(1)
        self.english_radio = QRadioButton("Tiếng Anh (Tắt)")
        self.vietnamese_radio = QRadioButton("Tiếng Việt (Bật)")
        self.english_radio.toggled.connect(lambda checked: self.set_telex_state(False) if checked else None)
        self.vietnamese_radio.toggled.connect(lambda checked: self.set_telex_state(True) if checked else None)
        control_layout.addLayout(status_row_layout)
        control_layout.addWidget(self.vietnamese_radio)
        control_layout.addWidget(self.english_radio)
        control_layout.addStretch(1)
        main_layout.addWidget(control_group, 0, 0)
        right_button_layout = QVBoxLayout()
        right_button_layout.setSpacing(8)
        self.close_button = QPushButton("Đóng")
        self.close_button.setToolTip("Thu nhỏ xuống khay hệ thống")
        self.close_button.clicked.connect(self.hide_to_tray_and_show_info)
        self.settings_button = QPushButton("Cài đặt...")
        self.settings_button.clicked.connect(self.open_settings)
        self.exit_button = QPushButton("Kết thúc")
        self.exit_button.setToolTip("Thoát hoàn toàn ứng dụng")
        self.exit_button.clicked.connect(self.quit_app)
        right_button_layout.addWidget(self.close_button)
        right_button_layout.addWidget(self.settings_button)
        right_button_layout.addWidget(self.exit_button)
        right_button_layout.addStretch(1)
        main_layout.addLayout(right_button_layout, 0, 1)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)
        self.help_button = QPushButton("Hướng dẫn")
        self.help_button.clicked.connect(self.show_help_dialog)
        bottom_layout.addWidget(self.help_button)
        self.info_button = QPushButton("Thông tin")
        self.info_button.clicked.connect(self.show_about_dialog)
        bottom_layout.addWidget(self.info_button)
        bottom_layout.addStretch(1)
        self.default_button = QPushButton("Mặc định")
        self.default_button.clicked.connect(self.reset_to_default)
        bottom_layout.addWidget(self.default_button)
        main_layout.addLayout(bottom_layout, 1, 0, 1, 2)
        main_layout.setRowStretch(0, 1)
        main_layout.setColumnStretch(0, 1)

    def apply_stylesheet(self):
        theme = config.get("theme", "light")
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow, QDialog { background-color: #23272e; color: #eee; font-family: 'Segoe UI', Arial; font-size: 9pt; }
                QGroupBox { border: 1px solid #444; border-radius: 4px; margin-top: 1ex; color: #eee; }
                QGroupBox::title { color: #eee; }
                QLabel, QRadioButton, QCheckBox { color: #eee; }
                QPushButton { background-color: #353b45; border: 1px solid #555; border-radius: 4px; padding: 5px 10px; min-width: 75px; color: #eee; }
                QPushButton:hover { background-color: #3c4250; }
                QPushButton:pressed { background-color: #23272e; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QDialog { background-color: #f0f0f0; font-family: "Segoe UI", Arial; font-size: 9pt; }
                QGroupBox { border: 1px solid #c0c0c0; border-radius: 4px; margin-top: 1ex; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; color: #333; }
                QLabel, QRadioButton, QCheckBox { color: #333; }
                QPushButton { background-color: #e1e1e1; border: 1px solid #b0b0b0; border-radius: 4px; padding: 5px 10px; min-width: 75px; }
                QPushButton:hover { background-color: #e9e9e9; }
                QPushButton:pressed { background-color: #d1d1d1; }
            """)

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("VietPy Telex")
        tray_menu = QMenu()
        show_action = QAction("Mở VietPy Telex", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        self.toggle_action_group = QActionGroup(self)
        self.toggle_action_group.setExclusive(True)
        self.enable_action = QAction("Tiếng Việt", self)
        self.enable_action.setCheckable(True)
        self.enable_action.triggered.connect(lambda: self.set_telex_state(True))
        tray_menu.addAction(self.enable_action)
        self.toggle_action_group.addAction(self.enable_action)
        self.disable_action = QAction("Tiếng Anh", self)
        self.disable_action.setCheckable(True)
        self.disable_action.triggered.connect(lambda: self.set_telex_state(False))
        tray_menu.addAction(self.disable_action)
        self.toggle_action_group.addAction(self.disable_action)
        tray_menu.addSeparator()
        settings_action = QAction("Cài đặt...", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        tray_menu.addSeparator()
        exit_action = QAction("Thoát", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def load_settings(self):
        load_config()
        if platform.system() == "Windows":
            config["auto_start"] = is_in_startup()
        self.set_telex_state(config.get("enabled", False))

    def play_switch_sound(self):
        if not config.get("sound_enabled", True):
            return
        try:
            sound_file = config.get("custom_sound_file", "")
            if not sound_file or not os.path.exists(sound_file):
                sound_file = os.path.join(SOUNDS_DIR, config.get("sound_file", "default.wav"))
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Error playing sound: {e}")

    def set_telex_state(self, enabled: bool):
        global is_telex_enabled
        if is_telex_enabled == enabled:
            return
        is_telex_enabled = enabled
        config["enabled"] = enabled
        save_config()
        # Cập nhật trạng thái đẹp hơn: icon + text lớn, màu nổi bật
        if enabled:
            self.status_icon_label.setPixmap(self.icon_vietnamese.pixmap(32, 32))
            self.status_text_label.setText("<span style='color:#4CAF50;'>Đang bật</span>")
            self.tray_icon.setIcon(self.icon_vietnamese)
            self.tray_icon.setToolTip("VietPy Telex - Tiếng Việt")
            self.vietnamese_radio.setChecked(True)
            start_keyboard_listener()
        else:
            self.status_icon_label.setPixmap(self.icon_english.pixmap(32, 32))
            self.status_text_label.setText("<span style='color:#D32F2F;'>Đang tắt</span>")
            self.tray_icon.setIcon(self.icon_english)
            self.tray_icon.setToolTip("VietPy Telex - Tiếng Anh")
            self.english_radio.setChecked(True)
            stop_keyboard_listener()
        self.update_tray_menu_state()
        # Phát âm thanh khi chuyển đổi
        self.play_switch_sound()

    def update_tray_menu_state(self):
        self.enable_action.setChecked(is_telex_enabled)
        self.disable_action.setChecked(not is_telex_enabled)

    def hide_to_tray_and_show_info(self):
        self.hide()
        self.tray_icon.showMessage("VietPy Telex", "Ứng dụng đang chạy ở chế độ nền.", self.windowIcon(), 2000)

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        # Click trái: chuyển đổi nhanh chế độ Telex, DoubleClick: mở cửa sổ
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.set_telex_state(not is_telex_enabled)
            status = "Tiếng Việt" if is_telex_enabled else "Tiếng Anh"
            self.tray_icon.showMessage("VietPy Telex", f"Chế độ gõ: {status}", self.windowIcon(), 1000)
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def closeEvent(self, a0: Optional[QCloseEvent]):
        self.hide_to_tray_and_show_info()
        if a0:
            a0.ignore()

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow(self)
        # Luôn đồng bộ theme khi mở settings
        self.settings_window.apply_stylesheet()
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()

    def show_help_dialog(self):
        help_text = """
        <h3>VietPy Telex - Hướng dẫn sử dụng</h3>
        <p><b>1. Bật/Tắt gõ Telex:</b></p>
        <ul>
            <li>Sử dụng nút radio "Tiếng Việt" / "Tiếng Anh" trên cửa sổ chính.</li>
            <li>Chuột phải vào biểu tượng ở khay hệ thống và chọn chế độ.</li>
            <li>Sử dụng phím tắt để chuyển đổi nhanh.</li>
        </ul>
        <p><b>2. Phím tắt chuyển đổi:</b></p>
        <ul>
            <li>Mặc định: <b>Ctrl + Shift</b>.</li>
            <li>Bạn có thể đổi thành <b>Alt + Z</b> trong mục "Cài đặt...".</li>
        </ul>
        <p><b>3. Quy tắc gõ Telex:</b></p>
        <ul>
            <li><b>Dấu thanh:</b> s (sắc), f (huyền), r (hỏi), x (ngã), j (nặng).</li>
            <li><b>Dấu mũ/móc:</b> w (cho ă, ơ, ư), aa (â), ee (ê), oo (ô), dd (đ).</li>
            <li><b>Xóa dấu:</b> Gõ phím <b>z</b>. Lần đầu sẽ xóa dấu thanh, lần thứ hai sẽ xóa dấu mũ/móc.</li>
            <li><b>Đặt dấu:</b> Dấu thanh (s,f,r,x,j) có thể gõ ngay sau nguyên âm hoặc cuối từ.</li>
        </ul>
        <p><b>4. Chức năng các nút:</b></p>
        <ul>
            <li><b>Đóng</b> hoặc nút <b>[X]</b> trên cửa sổ: Thu nhỏ ứng dụng xuống khay hệ thống.</li>
            <li><b>Kết thúc:</b> Thoát hoàn toàn ứng dụng.</li>
            <li><b>Cài đặt:</b> Mở cửa sổ tùy chỉnh phím tắt và chế độ khởi động.</li>
            <li><b>Mặc định:</b> Khôi phục lại tất cả cài đặt gốc.</li>
        </ul>
        """
        QMessageBox.information(self, "Hướng dẫn", help_text)

    def show_about_dialog(self):
        about_text = """
        <div style="font-family:'Segoe UI',Arial,sans-serif; font-size:10pt;">
            <h2 style="color:#00579c; margin-bottom:2px;">VietPy Telex <span style="font-size:11pt; color:#4CAF50;">v1.0</span></h2>
            <p style="margin-top:0; margin-bottom:8px;">
            <i>Bộ gõ Tiếng Việt Telex nhẹ, hiện đại.</i>
            </p>
            <table style="margin-bottom:8px;">
            <tr>
                <td style="vertical-align:top;"><b>Công nghệ:</b></td>
                <td>
                Python · PyQt6 · keyboard<br>
                Đặt dấu đúng chuẩn, hỗ trợ khởi động cùng hệ thống, phím tắt chuyển đổi nhanh.<br>
                <span style="color:#888;">(Không thu thập dữ liệu, không quảng cáo)</span>
                </td>
            </tr>
            <tr>
                <td style="vertical-align:top;"><b>Tác giả:</b></td>
                <td>Nam Trần</td>
            </tr>
            <tr>
                <td><b>Email:</b></td>
                <td><a href="mailto:namtran5905@gmail.com">namtran5905@gmail.com</a></td>
            </tr>
            <tr>
                <td><b>GitHub:</b></td>
                <td><a href="https://github.com/namtran592005/vietpy-telex">github.com/namtran592005/vietpy-telex</a></td>
            </tr>
            </table>
            <div style="color:#666; font-size:9pt;">
            © 2025 Nam Trần. Phát hành theo giấy phép MIT.<br>
            <span style="font-size:8pt;">Nếu bạn thấy hữu ích, hãy tặng sao ⭐ trên GitHub!</span>
            </div>
        </div>
        """
        QMessageBox.about(self, "Thông tin", about_text)

    def reset_to_default(self):
        reply = QMessageBox.question(self, "Mặc định", "Bạn có chắc chắn muốn đặt lại tất cả cài đặt về mặc định không?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            global config
            config = DEFAULT_CONFIG.copy()
            if platform.system() == "Windows":
                if is_in_startup(): remove_from_startup()
                config["auto_start"] = False
            save_config()
            self.load_settings()
            self.update_hotkey_listener()
            if self.settings_window and self.settings_window.isVisible():
                self.settings_window.load_settings_ui()
            QMessageBox.information(self, "Mặc định", "Đã đặt lại cài đặt về mặc định.")

    def quit_app(self):
        stop_keyboard_listener()
        keyboard.unhook_all()
        self.tray_icon.hide()
        instance = QCoreApplication.instance()
        if instance: instance.quit()

    def update_hotkey_listener(self):
        global active_hotkey_hook
        if active_hotkey_hook:
            try: keyboard.remove_hotkey(active_hotkey_hook)
            except (KeyError, ValueError): pass
            active_hotkey_hook = None
        hotkey_combo = "alt+z" if config.get("hotkey") == "alt_z" else "ctrl+shift"
        active_hotkey_hook = keyboard.add_hotkey(
            hotkey_combo, lambda: self.hotkey_toggled_state(), suppress=True
        )
        print(f"Hotkey '{hotkey_combo}' registered.")

    def hotkey_toggled_state(self):
        self.set_telex_state(not is_telex_enabled)
        if self.isVisible():
            QApplication.alert(self)
        else:
            status = "Tiếng Việt" if is_telex_enabled else "Tiếng Anh"
            self.tray_icon.showMessage("VietPy Telex", f"Chế độ gõ: {status}", self.windowIcon(), 1000)

def is_in_startup():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_READ) as reg_key:
                value, _ = winreg.QueryValueEx(reg_key, "VietPyTelex")
                script_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
                return value.strip('"').lower() == script_path.lower()
        except (ImportError, FileNotFoundError): return False
        except OSError: return False
    return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    main_window = VietPyTelexApp()
    # Silent start logic
    silent = False
    if config.get("auto_start", False):
        # Nếu có tham số --show hoặc -s thì luôn hiện cửa sổ
        if not any(arg in sys.argv for arg in ['-s', '--show']):
            if config.get("silent_start", False):
                silent = True
    if silent:
        main_window.set_telex_state(config.get("enabled", True))
        # Không show window, chỉ chạy nền
    else:
        main_window.show()
    sys.exit(app.exec())