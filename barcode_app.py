import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import os

# 테마 설정 (시스템 설정을 따르되, 바코드 영역만 고대비 화이트 적용)
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
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        
        my_barcode = code128(data, writer=writer)
        fp = io.BytesIO()
        
        # 💡 [화면 스캔 & 디자인 황금 비율 설정]
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 10, 
            "text_distance": 5.0, 
            "module_width": 0.4,   # 💡 너무 굵지 않으면서 화면 픽셀에 딱 맞는 두께
            "module_height": 16.0, # 💡 미관상 가장 보기 좋은 세로 길이
            "quiet_zone": 8.0,     # 💡 깔끔한 여백
            "dpi": 300
        }
        
        my_barcode.write(fp, options=options) 
        
        img = Image.open(fp)
        # 💡 미리보기 크기를 '자연스러운' 사이즈로 고정 (너비 400px 내외)
        display_w = 420
        img_w, img_h = img.size
        display_h = int(img_h * (display_w / img_w))
        
        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        current_barcode_obj = my_barcode
        current_barcode_data = data
        save_button.configure(state="normal", fg_color="#2FA572")
        
    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

def save_barcode():
    try:
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 10, 
            "text_distance": 5.0, 
            "module_width": 0.4,
            "module_height": 16.0,
            "quiet_zone": 8.0,
            "dpi": 300
        }
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}", options=options)
        messagebox.showinfo("성공", f"저장 완료: {filename}")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- 모던 & 콤팩트 UI 레이아웃 ---
root = ctk.CTk()
root.title("Logistics Pro v2.3")
root.geometry("550x680") # 💡 적당하고 보기 좋은 창 크기

# 배경 프레임
main_frame = ctk.CTkFrame(root, corner_radius=20)
main_frame.pack(fill="both", expand=True, padx=25, pady=25)

title_label = ctk.CTkLabel(main_frame, text="Barcode System", font=ctk.CTkFont(size=26, weight="bold"))
title_label.pack(pady=(30, 20))

# 입력창 영역
input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
input_frame.pack(fill="x", padx=40)

entry = ctk.CTkEntry(input_frame, width=320, height=45, font=ctk.CTkFont(size=15),
                     placeholder_text="데이터를 입력해 주세요", border_width=2)
entry.pack(side="left", padx=(0, 10))

# 엔터 키를 누르면 바로 생성되도록 연결
entry.bind("<Return>", lambda event: generate_barcode())

generate_btn = ctk.CTkButton(input_frame, text="생성", width=80, height=45, 
                             font=ctk.CTkFont(size=14, weight="bold"), command=generate_barcode)
generate_btn.pack(side="left")

# 바코드 디스플레이 (고대비 화이트 박스)
barcode_display_frame = ctk.CTkFrame(main_frame, width=480, height=220, fg_color="white", corner_radius=12, border_width=1, border_color="gray70")
barcode_display_frame.pack(pady=30, padx=20)
barcode_display_frame.pack_propagate(False)

barcode_label = ctk.CTkLabel(barcode_display_frame, text="바코드 미리보기", text_color="gray60", font=ctk.CTkFont(size=13))
barcode_label.pack(expand=True)

# 하단 버튼 및 정보
save_button = ctk.CTkButton(main_frame, text="PNG 파일로 내보내기", width=250, height=45, 
                            font=ctk.CTkFont(size=14), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(pady=(10, 20))

status_label = ctk.CTkLabel(main_frame, text="입력 후 Enter를 누르면 바코드가 생성됩니다.", font=ctk.CTkFont(size=11), text_color="gray")
status_label.pack(side="bottom", pady=15)

root.mainloop()
