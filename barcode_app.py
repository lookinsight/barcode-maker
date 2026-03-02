import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import os

ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue")

current_barcode_obj = None
current_barcode_data = ""

def generate_barcode():
    global current_barcode_obj, current_barcode_data
    
    data = entry.get()
    if not data:
        messagebox.showwarning("경고", "데이터를 입력해 주세요.")
        return
        
    try:
        # 1. 폰트 경로 설정
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        
        # 2. 바코드 설정
        code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        
        # 3. 바코드 생성 (텍스트와 바코드 간격 조정)
        my_barcode = code128(data, writer=writer)
        fp = io.BytesIO()
        
        # 💡 핵심 수정: 
        # module_height: 바코드 선의 세로 길이를 늘림 (기본 15 -> 18)
        # text_distance: 바코드와 숫자 사이의 간격을 대폭 늘림 (기본 1 -> 5)
        # font_size: 글자 크기를 적절하게 조절 (10)
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 10, 
            "text_distance": 5, # 숫자와 바코드 사이의 거리를 벌림
            "module_height": 18.0, # 바코드 선 자체를 좀 더 길게
            "quiet_zone": 6.0 # 양옆 여백 확보
        }
        
        my_barcode.write(fp, options=options) 
        
        img = Image.open(fp)
        # 미리보기 화면에 꽉 차게 보이도록 비율 유지하며 축소
        img.thumbnail((320, 160))
        
        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        current_barcode_obj = my_barcode
        current_barcode_data = data
        save_button.configure(state="normal")
        
    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

def save_barcode():
    try:
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        # 저장 시에도 동일한 옵션 적용
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 10, 
            "text_distance": 5, 
            "module_height": 18.0,
            "quiet_zone": 6.0
        }
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}", options=options)
        messagebox.showinfo("성공", f"{filename} 파일이 저장되었습니다!")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- UI 레이아웃 ---
root = ctk.CTk()
root.title("물류 바코드 시스템 Pro")
root.geometry("400x550") # 레이아웃을 위해 높이를 약간 키움

title_label = ctk.CTkLabel(root, text="📦 바코드 생성기", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=(25, 15))

entry = ctk.CTkEntry(root, width=280, height=40, font=ctk.CTkFont(size=14),
                     placeholder_text="데이터를 입력해 주세요")
entry.pack(pady=10)

generate_btn = ctk.CTkButton(root, text="1. 화면에서 바코드 확인", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=generate_barcode)
generate_btn.pack(pady=15)

barcode_label = ctk.CTkLabel(root, text="바코드를 생성하면 여기에 표시됩니다.", 
                             width=320, height=180, 
                             fg_color=("gray85", "gray25"), 
                             corner_radius=10)
barcode_label.pack(pady=15)

save_button = ctk.CTkButton(root, text="2. PNG 파일로 저장", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#2FA572", hover_color="#1D7A50",
                            command=save_barcode, state="disabled")
save_button.pack(pady=10)

root.mainloop()
