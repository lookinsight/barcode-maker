import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import os # 시스템 폰트 경로를 찾기 위해 추가

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
        # 1. 윈도우 기본 폰트 경로 설정 (에러 방지 핵심)
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        
        # 2. Code 128 규격 및 폰트 설정 적용
        code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        
        # 3. 바코드 생성 및 가상 도화지에 쓰기 (텍스트 포함)
        my_barcode = code128(data, writer=writer)
        fp = io.BytesIO()
        # 하단 텍스트를 활성화(write_text=True)하고 폰트 경로를 지정합니다.
        my_barcode.write(fp, options={"write_text": True, "font_path": font_path, "font_size": 10, "text_distance": 1}) 
        
        img = Image.open(fp)
        img.thumbnail((300, 150))
        
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
        # 파일 저장 시에도 텍스트가 포함되도록 동일하게 설정
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}", 
                                           options={"write_text": True, "font_path": font_path, "font_size": 10, "text_distance": 1})
        messagebox.showinfo("성공", f"{filename} 파일이 저장되었습니다!")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- UI 레이아웃 (요청하신 안내 문구 반영) ---
root = ctk.CTk()
root.title("물류 바코드 시스템 Pro")
root.geometry("400x520")

title_label = ctk.CTkLabel(root, text="📦 바코드 생성기", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=(25, 15))

entry = ctk.CTkEntry(root, width=280, height=40, font=ctk.CTkFont(size=14),
                     placeholder_text="데이터를 입력해 주세요") #
entry.pack(pady=10)

generate_btn = ctk.CTkButton(root, text="1. 화면에서 바코드 확인", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=generate_barcode)
generate_btn.pack(pady=15)

barcode_label = ctk.CTkLabel(root, text="바코드를 생성하면 여기에 표시됩니다.", 
                             width=320, height=160, 
                             fg_color=("gray85", "gray25"), 
                             corner_radius=10)
barcode_label.pack(pady=15)

save_button = ctk.CTkButton(root, text="2. PNG 파일로 저장", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#2FA572", hover_color="#1D7A50",
                            command=save_barcode, state="disabled")
save_button.pack(pady=10)

root.mainloop()
