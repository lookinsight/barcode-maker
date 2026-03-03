import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image
import io
import os

# 테마 설정 (시스템 모드를 따르되, 바코드 영역만 고대비 화이트 적용)
ctk.set_appearance_mode("Dark") # 서울 야경과 어울리는 다크 모드 고정
ctk.set_default_color_theme("dark-blue") # 고급스러운 컬러 테마

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
        
        # 💡 [화면 스캔 최적화 황금 비율]
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 11, 
            "text_distance": 5.0, 
            "module_width": 0.45,   # 💡 화면 픽셀 매칭을 위한 선 두께 조정
            "module_height": 18.0,  # 💡 미관상 가장 보기 좋은 세로 길이
            "quiet_zone": 10.0,     # 💡 주변 흰색 여백 충분히 확보
            "dpi": 400
        }
        
        my_barcode.write(fp, options=options) 
        
        img = Image.open(fp)
        # 💡 [세련된 크기 설정] 거대하지 않게, 하지만 스캔은 잘 되게 고정 (너비 450px)
        display_w = 480
        img_w, img_h = img.size
        display_h = int(img_h * (display_w / img_w))
        
        img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
        
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
        # 저장 시에도 동일한 고품질 옵션 적용
        options = {
            "write_text": True, 
            "font_path": font_path, 
            "font_size": 11, 
            "text_distance": 5.0, 
            "module_width": 0.45,
            "module_height": 18.0,
            "quiet_zone": 10.0,
            "dpi": 400
        }
        filename = current_barcode_obj.save(f"barcode_{current_barcode_data}", options=options)
        messagebox.showinfo("성공", f"파일 저장 완료: {filename}")
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# --- 모던 & 대형 프라이빗 UI 레이아웃 ---
root = ctk.CTk()
root.title("Warehouse Logistics Pro - Seoul Night Edition v3.0")
# 💡 [요청사항 반영] 전체 창 크기를 대폭 확장
root.geometry("1000x800") 

# 💡 [요청사항 반영] '서울 야경' 느낌의 고급스러운 다크 그라데이션 배경 구현
bg_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="#0a0f1e") # 깊은 밤하늘 색상
bg_frame.pack(fill="both", expand=True)

# 그라데이션 효과를 위한 서브 프레임 (상단은 약간 밝은 블루)
bg_gradient = ctk.CTkFrame(bg_frame, corner_radius=0, fg_color="#1a2542", height=300)
bg_gradient.place(x=0, y=0, relwidth=1)

# 중앙 콘텐츠 영역 (반투명 Glassmorphism 효과)
main_container = ctk.CTkFrame(bg_frame, corner_radius=25, fg_color=("#333333", "#141414"), border_width=1, border_color="#333333")
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

# 상단 헤더
header_label = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"), text_color="#E0E0E0")
header_label.pack(pady=(50, 40))

# 입력창 섹션 (고급스러운 카드 형태)
input_card = ctk.CTkFrame(main_container, fg_color="transparent")
input_card.pack(fill="x", padx=60)

entry = ctk.CTkEntry(input_card, width=550, height=60, font=ctk.CTkFont(size=20),
                     placeholder_text="데이터를 입력해 주세요", border_width=2, border_color="#404040", fg_color="#1A1A1A")
entry.pack(side="left", padx=(0, 20))

# 엔터 키를 누르면 바로 생성되도록 연결
entry.bind("<Return>", lambda event: generate_barcode())

generate_btn = ctk.CTkButton(input_card, text="생성", width=120, height=60, 
                             font=ctk.CTkFont(size=18, weight="bold"), command=generate_barcode)
generate_btn.pack(side="left")

# 바코드 디스플레이 (💡 핵심: 고대비 화이트 카드 고정)
barcode_display_frame = ctk.CTkFrame(main_container, width=700, height=320, fg_color="white", corner_radius=15, border_width=1, border_color="gray80")
barcode_display_frame.pack(pady=40, padx=40)
barcode_display_frame.pack_propagate(False)

barcode_label = ctk.CTkLabel(barcode_display_frame, text="Barcode Preview", text_color="gray60", font=ctk.CTkFont(size=14))
barcode_label.pack(expand=True)

# 하단 정보 및 버튼
status_label = ctk.CTkLabel(main_container, text="Coupang Logistics Team / v3.0 / Designed for Efficiency", font=ctk.CTkFont(size=12), text_color="#808080")
status_label.pack(side="bottom", pady=20)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=250, height=50, 
                            font=ctk.CTkFont(size=16), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(side="bottom", pady=(0, 10))

root.mainloop()
