import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io

# 1. 프로그램 기본 테마 설정 (시스템 설정에 따라 다크/라이트 모드 자동 전환)
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") # 기본 버튼 색상을 파란색 톤으로 설정

current_barcode_obj = None
current_barcode_data = ""

def generate_barcode():
    global current_barcode_obj, current_barcode_data
    
    data = entry.get()
    if not data:
        messagebox.showwarning("경고", "바코드에 들어갈 데이터를 입력해 주세요.")
        return
        
    try:
        code128 = barcode.get_barcode_class('code128')
        my_barcode = code128(data, writer=ImageWriter())
        
        fp = io.BytesIO()
        my_barcode.write(fp)
        
        img = Image.open(fp)
        img.thumbnail((300, 150)) 
        
        # 2. 모던 UI에 맞게 이미지를 변환하는 전용 도구 사용
        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        
        # 3. 빈 액자에 있던 '안내 글자'를 지우고 바코드 이미지를 덮어씌움
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        current_barcode_obj = my_barcode
        current_barcode_data = data
        
        save_button.configure(state="normal")
        
    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

def save_barcode():
    try:
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}")
        messagebox.showinfo("성공", f"{filename} 파일이 저장되었습니다!")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- 화면 디자인 구성 ---

root = ctk.CTk() # 기존 tk.Tk() 대신 모던한 창 생성 도구 사용
root.title("물류 로케이션 바코드 시스템 Pro")
root.geometry("400x520")

# 타이틀 텍스트 (크고 굵은 폰트 적용)
title_label = ctk.CTkLabel(root, text="📦 바코드 생성기", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=(25, 15))

# 입력창 (모서리가 둥글고, 안에 힌트 글자가 희미하게 적혀있음)
entry = ctk.CTkEntry(root, width=280, height=40, font=ctk.CTkFont(size=14),
                     placeholder_text="예: A1-01 (1단:빨강, 2단:주황, 3단:노랑, 4단:초록, 5단:파랑)")
entry.pack(pady=10)

# 첫 번째 버튼 (모서리가 둥근 세련된 형태)
generate_btn = ctk.CTkButton(root, text="1. 화면에서 바코드 확인", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"), command=generate_barcode)
generate_btn.pack(pady=15)

# 바코드가 들어갈 공간 (초기에는 연한 회색 배경과 안내 텍스트가 표시됨)
barcode_label = ctk.CTkLabel(root, text="바코드를 생성하면 여기에 표시됩니다.", 
                             width=320, height=160, 
                             fg_color=("gray85", "gray25"), # 라이트/다크 모드 배경색
                             corner_radius=10) # 모서리 둥글게
barcode_label.pack(pady=15)

# 두 번째 버튼 (저장 버튼이라는 것을 강조하기 위해 색상을 초록색으로 변경)
save_button = ctk.CTkButton(root, text="2. PNG 파일로 저장", width=200, height=40, font=ctk.CTkFont(size=14, weight="bold"),
                            fg_color="#2FA572", hover_color="#1D7A50", # 초록색 계열 색상 지정
                            command=save_barcode, state="disabled")
save_button.pack(pady=10)

root.mainloop()
