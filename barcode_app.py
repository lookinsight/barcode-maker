import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import qrcode
import random

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

current_barcode_pil = None
current_barcode_data = ""
history_list = []

# 🌃 서울 야경 느낌의 배경 생성 (창문 너머 도심 풍경 느낌)
def create_seoul_night_bg(width, height):
    base = Image.new('RGB', (width, height), '#050a14')
    draw = ImageDraw.Draw(base, 'RGBA')
    # 멀리 보이는 건물 불빛들 (랜덤 사각형)
    for _ in range(50):
        x, y = random.randint(0, width), random.randint(height//2, height)
        w, h = random.randint(20, 60), random.randint(40, 150)
        draw.rectangle([x, y, x+w, y+h], fill='#101a30')
        # 건물 창문 불빛
        for i in range(2, w-2, 10):
            for j in range(2, h-2, 15):
                if random.random() > 0.6:
                    draw.rectangle([x+i, y+j, x+i+5, y+j+8], fill=random.choice(['#ffd700', '#ffffff', '#ff4500'])+'80')
    return base

# 🏷️ ICQA 로고 생성 (Gray 배경 요청 반영)
def get_icqa_logo(size=55):
    logo = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(logo)
    draw.rounded_rectangle((0, 0, size, size), radius=12, fill="#333333") # Gray 배경
    try: font = ImageFont.truetype("arial.ttf", 16)
    except: font = ImageFont.load_default()
    draw.text((8, 17), "ICQA", font=font, fill="white")
    return logo

def generate_barcode():
    global current_barcode_pil, current_barcode_data
    data = entry.get()
    b_type = type_combo.get()
    if not data:
        messagebox.showwarning("경고", "데이터를 입력해 주세요.")
        return
    try:
        if b_type == "QR Code":
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
            lw = 70; logo = get_icqa_logo(lw)
            barcode_img.paste(logo, ((barcode_img.size[0]-lw)//2, (barcode_img.size[1]-lw)//2), logo)
            final_img = barcode_img
        else:
            code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            writer = ImageWriter()
            my_barcode = code_class(data, writer=writer)
            fp = io.BytesIO()
            my_barcode.write(fp, options={"write_text": True, "font_path": "arial.ttf", "font_size": 10, "text_distance": 5, "module_width": 0.4, "module_height": 18, "quiet_zone": 10, "dpi": 300})
            barcode_img = Image.open(fp).convert('RGBA')
            lw = 55; logo = get_icqa_logo(lw)
            # 💡 로고를 우측 상단에 배치
            final_img = barcode_img.copy()
            final_img.paste(logo, (final_img.size[0]-lw-5, 5), logo)

        current_barcode_pil = final_img
        current_barcode_data = data
        
        # 화면 표시 (비비드한 창문 느낌)
        img_w, img_h = final_img.size
        display_w = 480
        display_h = int(img_h * (display_w / img_w))
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        barcode_label.configure(image=img_ctk, text="")
        barcode_label.image = img_ctk
        save_button.configure(state="normal", fg_color="#2FA572")
        
        add_to_history(data, b_type, final_img)
    except Exception as e:
        messagebox.showerror("오류", f"에러 발생: {e}")

def add_to_history(data, b_type, img):
    global history_list
    history_list.insert(0, {"data": data, "type": b_type, "img": img})
    if len(history_list) > 6: history_list.pop()
    for widget in history_scroll.winfo_children(): widget.destroy()
    for item in history_list:
        # 💡 히스토리에 바코드 종류와 데이터가 명확히 나오도록 수정
        btn_text = f"[{item['type']}]\n{item['data']}"
        btn = ctk.CTkButton(history_scroll, text=btn_text, font=("Arial", 12), width=180, height=60, fg_color="#1e293b", hover_color="#334155", command=lambda d=item: restore_history(d))
        btn.pack(side="left", padx=10)

def restore_history(item):
    entry.delete(0, 'end'); entry.insert(0, item['data'])
    type_combo.set(item['type']); generate_barcode()

def save_barcode():
    if current_barcode_pil:
        filename = f"ICQA_{current_barcode_data}.png"
        current_barcode_pil.save(filename)
        messagebox.showinfo("성공", f"{filename} 저장 완료!")

# UI 레이아웃
root = ctk.CTk()
root.title("Warehouse Pro v4.3 - Seoul Night")
root.geometry("1100x850")

# 배경 설정
bg_pil = create_seoul_night_bg(1920, 1080)
bg_ctk = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1920, 1080))
bg_label = ctk.CTkLabel(root, text="", image=bg_ctk)
bg_label.pack(fill="both", expand=True)

# 💡 중앙 정렬을 위한 메인 카드 (빌딩 안 창문 느낌의 테두리)
main_card = ctk.CTkFrame(bg_label, corner_radius=25, fg_color="#0f172a", border_width=3, border_color="#1e293b")
main_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

ctk.CTkLabel(main_card, text="Logistics Barcode Generator", font=("Arial", 35, "bold"), text_color="#f8fafc").pack(pady=(40, 30))

# 💡 중앙 정렬을 위해 center_frame 사용
center_frame = ctk.CTkFrame(main_card, fg_color="transparent")
center_frame.pack(expand=True)

input_row = ctk.CTkFrame(center_frame, fg_color="transparent")
input_row.pack(pady=10)

# 바코드 종류 선택 복구
type_combo = ctk.CTkComboBox(input_row, values=["Code 128", "Code 39", "QR Code"], width=160, height=55, font=("Arial", 15))
type_combo.set("Code 128"); type_combo.pack(side="left", padx=10)

entry = ctk.CTkEntry(input_row, width=450, height=55, font=("Arial", 18), placeholder_text="데이터를 입력하세요", fg_color="#1e293b", border_color="#334155")
entry.pack(side="left", padx=10)
entry.bind("<Return>", lambda e: generate_barcode())

ctk.CTkButton(input_row, text="생성", width=120, height=55, font=("Arial", 16, "bold"), command=generate_barcode).pack(side="left", padx=10)

# 💡 창문 느낌의 바코드 프리뷰 영역
barcode_label = ctk.CTkLabel(center_frame, text="Barcode Window", width=750, height=320, fg_color="white", corner_radius=15, text_color="gray")
barcode_label.pack(pady=30)

# 히스토리 영역 (바코드 종류와 데이터 표시)
ctk.CTkLabel(center_frame, text="생성 히스토리", font=("Arial", 14), text_color="#94a3b8").pack(pady=(10, 5))
history_scroll = ctk.CTkScrollableFrame(center_frame, height=100, orientation="horizontal", fg_color="transparent")
history_scroll.pack(fill="x", padx=40)

save_button = ctk.CTkButton(main_card, text="Save as PNG", font=("Arial", 16, "bold"), width=300, height=50, state="disabled", command=save_barcode)
save_button.pack(pady=(20, 40))

root.mainloop()
