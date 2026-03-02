import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import os

# 테마 설정
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
        
        # 💡 간격 및 비율 최적화
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 10, 
            "text_distance": 5.0, # 숫자와 바코드 사이의 충분한 간격
            "module_height": 18.0, # 바코드 선을 길게 하여 가독성 향상
            "quiet_zone": 6.0,
            "background": "white",
            "foreground": "black"
        }
        
        my_barcode.write(fp, options=options) 
        
        img = Image.open(fp)
        # 미리보기 이미지를 더 크게 표시 (350x180)
        img.thumbnail((350, 180))
        
        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        current_barcode_obj = my_barcode
        current_barcode_data = data
        save_button.configure(state="normal", fg_color="#2FA572") # 활성화 시 초록색으로 변경
        
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
            "module_height": 18.0,
            "quiet_zone": 6.0
        }
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}", options=options)
        messagebox.showinfo("성공", f"파일이 저장되었습니다: {filename}")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- 메인 윈도우 설정 ---
root = ctk.CTk()
root.title("Logistics Barcode System v2.0")
root.geometry("500x650") # 창 크기를 더 크게 확장

# 상단 헤더 프레임
header_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
header_frame.pack(fill="x", padx=20, pady=(30, 20))

title_label = ctk.CTkLabel(header_frame, text="📦 바코드 생성 시스템", font=ctk.CTkFont(size=28, weight="bold"))
title_label.pack(side="left")

# 메인 콘텐츠 영역
main_frame = ctk.CTkFrame(root, corner_radius=15)
main_frame.pack(fill="both", expand=True, padx=20, pady=10)

# 입력 섹션
input_label = ctk.CTkLabel(main_frame, text="바코드 데이터 입력", font=ctk.CTkFont(size=14, weight="bold"))
input_label.pack(pady=(20, 5))

entry = ctk.CTkEntry(main_frame, width=350, height=45, font=ctk.CTkFont(size=16),
                     placeholder_text="데이터를 입력해 주세요", border_width=2)
entry.pack(pady=10)

generate_btn = ctk.CTkButton(main_frame, text="화면에서 바코드 확인", width=350, height=50, 
                             font=ctk.CTkFont(size=15, weight="bold"), command=generate_barcode)
generate_btn.pack(pady=20)

# 바코드 출력 섹션
barcode_display_frame = ctk.CTkFrame(main_frame, width=400, height=220, fg_color=("gray90", "gray20"), corner_radius=10)
barcode_display_frame.pack(pady=10, padx=20, fill="x")
barcode_display_frame.pack_propagate(False)

barcode_label = ctk.CTkLabel(barcode_display_frame, text="미리보기가 여기에 표시됩니다")
barcode_label.pack(expand=True)

# 저장 섹션
save_button = ctk.CTkButton(main_frame, text="PNG 파일로 저장하기", width=350, height=50, 
                            font=ctk.CTkFont(size=15, weight="bold"),
                            state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(pady=30)

footer_label = ctk.CTkLabel(root, text="Designed for Warehouse Efficiency", font=ctk.CTkFont(size=11), text_color="gray")
footer_label.pack(pady=10)

root.mainloop()
