import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import qrcode
import random # 💡 우주 배경을 위해 반드시 필요합니다.

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

current_barcode_pil = None # 💡 저장용 이미지를 담을 변수
current_barcode_data = ""
history_list = []

# 🌌 우주 배경 생성 (코드만으로 별빛 은하수 구현)
def create_space_background(width, height):
    base = Image.new('RGB', (width, height), '#05050a')
    draw = ImageDraw.Draw(base, 'RGBA')
    for _ in range(15): # 네뷸라 효과
        x, y = random.randint(0, width), random.randint(0, height)
        r = random.randint(150, 450)
        color = random.choice(['#1a237e', '#311b92', '#4a148c', '#004d40']) + '20'
        draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    for _ in range(600): # 별빛
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=(255, 255, 255, random.randint(100, 255)))
    return base

# 🏷️ ICQA 로고 생성
def get_icqa_logo(size=50):
    logo = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(logo)
    draw.rounded_rectangle((0, 0, size, size), radius=10, fill="#2FA572")
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    draw.text((8, 15), "ICQA", font=font, fill="white")
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
            # QR 중앙에 로고 삽입
            lw = 60
            logo = get_icqa_logo(lw)
            barcode_img.paste(logo, ((barcode_img.size[0]-lw)//2, (barcode_img.size[1]-lw)//2), logo)
            final_img = barcode_img
        else:
            code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            writer = ImageWriter()
            my_barcode = code_class(data, writer=writer)
            fp = io.BytesIO()
            my_barcode.write(fp, options={"write_text": True, "font_path": "arial.ttf", "font_size": 10, "text_distance": 5, "module_width": 0.4, "module_height": 18, "quiet_zone": 10, "dpi": 300})
            barcode_img = Image.open(fp).convert('RGBA')
            # 오른쪽에 로고 붙이기
            lw = 50
            logo = get_icqa_logo(lw)
            final_img = Image.new('RGBA', (barcode_img.size[0] + lw + 10, barcode_img.size[1]), 'white')
            final_img.paste(barcode_img, (0, 0))
            final_img.paste(logo, (barcode_img.size[0], (barcode_img.size[1]-lw)//2), logo)

        current_barcode_pil = final_img
        current_barcode_data = data
        
        # 미리보기 업데이트
        img_w, img_h = final_img.size
        display_w = 480
        display_h = int(img_h * (display_w / img_w))
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        barcode_label.configure(image=img_ctk, text="")
        barcode_label.image = img_ctk
        save_button.configure(state="normal", fg_color="#2FA572")
        
        # 히스토리 추가
        add_to_history(data, b_type, final_img)
    except Exception as e:
        messagebox.showerror("오류", f"생성 중 에러: {e}")

def add_to_history(data, b_type, img):
    global history_list
    history_list.insert(0, {"data": data, "type": b_type, "img": img})
    if len(history_list) > 5: history_list.pop()
    for widget in history_scroll.winfo_children(): widget.destroy()
    for item in history_list:
        btn = ctk.CTkButton(history_scroll, text=f"{item['type']}: {item['data']}", fg_color="gray20", hover_color="gray30", command=lambda d=item: restore_history(d))
        btn.pack(side="left", padx=5)

def restore_history(item):
    entry.delete(0, 'end')
    entry.insert(0, item['data'])
    type_combo.set(item['type'])
    generate_barcode()

def save_barcode():
    if current_barcode_pil:
        filename = f"{current_barcode_data}.png"
        current_barcode_pil.save(filename)
        messagebox.showinfo("성공", f"{filename} 저장 완료!")

# UI 설정
root = ctk.CTk()
root.title("Warehouse Pro v4.1 - Space Edition")
root.geometry("1000x800")

bg_pil = create_space_background(1000, 800)
bg_ctk = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1000, 800))
bg_label = ctk.CTkLabel(root, text="", image=bg_ctk)
bg_label.pack(fill="both", expand=True)

main_card = ctk.CTkFrame(bg_label, corner_radius=25, fg_color="#141414", border_width=1, border_color="#333333")
main_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

ctk.CTkLabel(main_card, text="Logistics Barcode Generator", font=("Arial", 32, "bold")).pack(pady=40)

input_frame = ctk.CTkFrame(main_card, fg_color="transparent")
input_frame.pack(fill="x", padx=60)

type_combo = ctk.CTkComboBox(input_frame, values=["Code 128", "Code 39", "QR Code"], width=150, height=50)
type_combo.set("Code 128")
type_combo.pack(side="left", padx=(0, 10))

entry = ctk.CTkEntry(input_frame, width=400, height=50, placeholder_text="데이터를 입력하세요")
entry.pack(side="left", padx=10)
entry.bind("<Return>", lambda e: generate_barcode())

ctk.CTkButton(input_frame, text="생성", width=100, height=50, command=generate_barcode).pack(side="left")

barcode_label = ctk.CTkLabel(main_card, text="Barcode Preview", width=700, height=300, fg_color="white", corner_radius=15)
barcode_label.pack(pady=30)

history_scroll = ctk.CTkScrollableFrame(main_card, height=100, orientation="horizontal", fg_color="transparent")
history_scroll.pack(fill="x", padx=60, pady=10)

save_button = ctk.CTkButton(main_card, text="Save as PNG", state="disabled", command=save_barcode)
save_button.pack(pady=20)

root.mainloop()
