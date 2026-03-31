import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import json
import sys
import qrcode

try:
    import win32print
    import win32ui
    from PIL import ImageWin
except ImportError:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

FAV_FILE = "favorites.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

current_barcode_pil = None
current_barcode_data = ""
favorites_list = []

def load_favorites():
    global favorites_list
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                favorites_list = json.load(f)
            update_fav_combo()
        except:
            favorites_list = []

def save_favorites_to_file():
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites_list, f, ensure_ascii=False, indent=4)

def create_final_barcode_image(barcode_img, data, product_name):
    margin = 25
    header_height = 60 if product_name else 10
    
    new_w = barcode_img.size[0] + (margin * 2)
    new_h = barcode_img.size[1] + header_height
    final_img = Image.new('RGBA', (new_w, new_h), 'white')
    draw = ImageDraw.Draw(final_img)
    
    try:
        font_p = resource_path("malgun.ttf")
        title_font = ImageFont.truetype(font_p, 26) 
    except:
        title_font = ImageFont.load_default()

    if product_name:
        # 💡 [핵심 수정] 최신 Pillow 라이브러리에 맞춰 글자 크기 계산 방식(textbbox)으로 변경!
        bbox = draw.textbbox((0, 0), product_name, font=title_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((margin, (header_height - text_h) // 2), product_name, font=title_font, fill="black")

    final_img.paste(barcode_img, (margin, header_height))
    
    return final_img

def generate_barcode():
    global current_barcode_pil, current_barcode_data
    data = entry.get()
    p_name = product_entry.get()
    b_type = type_combo.get()
    
    if not data:
        messagebox.showwarning("경고", "데이터를 입력하세요.")
        return
        
    try:
        fp = io.BytesIO()
        font_p = resource_path("arial.ttf") 

        if b_type == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        else:
            code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            my_barcode = code_class(data, writer=ImageWriter())
            
            options = {"write_text": True, "font_size": 8, "dpi": 300, "font_path": font_p, "text_distance": 3.0}
            my_barcode.write(fp, options=options) 
            barcode_img = Image.open(fp).convert('RGBA')
        
        final_img = create_final_barcode_image(barcode_img, data, p_name)
        current_barcode_pil = final_img
        current_barcode_data = data
        
        max_w, max_h = 560, 230 
        img_w, img_h = final_img.size
        ratio = min(max_w / img_w, max_h / img_h)
        display_w, display_h = int(img_w * ratio), int(img_h * ratio)
        
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        barcode_label.configure(image=img_ctk, text="")
        
        save_button.configure(state="normal", fg_color="#2FA572")
        print_btn_full.configure(state="normal")
        print_btn_half.configure(state="normal")
        
    except Exception as e:
        messagebox.showerror("오류", f"생성 실패: {e}")

def print_barcode(size_mode):
    if not current_barcode_pil: return
    try:
        printer_name = win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        
        w_px = 900 if size_mode == "full" else 450
        h_px = 500
        
        hDC.StartDoc(f"Barcode_{current_barcode_data}")
        hDC.StartPage()
        dib = ImageWin.Dib(current_barcode_pil)
        dib.draw(hDC.GetHandleOutput(), (100, 100, 100 + w_px, 100 + h_px))
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        messagebox.showinfo("인쇄", "프린터로 전송되었습니다.")
    except Exception as e:
        messagebox.showerror("인쇄 오류", f"프린터 연결을 확인하세요: {e}")

def add_to_favorites():
    data, b_type = entry.get(), type_combo.get()
    if not data: return
    if len(favorites_list) >= 20:
        messagebox.showwarning("경고", "최대 20개까지만 저장 가능합니다.")
        return
    
    if not any(f['data'] == data for f in favorites_list):
        favorites_list.append({'data': data, 'type': b_type})
        save_favorites_to_file()
        update_fav_combo()
        messagebox.showinfo("성공", "자주 쓰는 바코드에 추가되었습니다.")

def update_fav_combo():
    vals = ["🌟 자주 쓰는 바코드 꺼내기..."] + [f"[{f['type']}] {f['data']}" for f in favorites_list]
    fav_combo.configure(values=vals)
    fav_combo.set("🌟 자주 쓰는 바코드 꺼내기...")

def load_favorite(choice):
    if choice.startswith("🌟"): return
    for f in favorites_list:
        if f"[{f['type']}] {f['data']}" == choice:
            entry.delete(0, 'end')
            entry.insert(0, f['data'])
            type_combo.set(f['type'])
            generate_barcode()
            break
    fav_combo.set("🌟 자주 쓰는 바코드 꺼내기...")

# --- UI 메인 구성 ---
root = ctk.CTk()
root.title("Warehouse Pro v5.2 - Logistics Expert") 
root.geometry("1100x850")

try:
    bg_image_path = resource_path("logistic_future.jpg")
    bg_pil = Image.open(bg_image_path)
    bg_pil_high_res = ImageOps.fit(bg_pil, (2560, 1440), Image.Resampling.LANCZOS)
    bg_ctk = ctk.CTkImage(light_image=bg_pil_high_res, dark_image=bg_pil_high_res, size=(2560, 1440))
    bg_label = ctk.CTkLabel(root, text="", image=bg_ctk)
    bg_label.place(relx=0.5, rely=0.5, anchor="center") 
except Exception as e:
    bg_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="#0a0f1e")
    bg_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)

main_container = ctk.CTkFrame(root, corner_radius=20, fg_color=("#333333", "#141414"), border_width=1, border_color="#444444")
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

header = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"))
header.pack(pady=30)

product_entry = ctk.CTkEntry(main_container, width=500, height=45, placeholder_text="[상품명 입력] 바코드 상단에 크게 인쇄됩니다.")
product_entry.pack(pady=(0, 15))

input_frame = ctk.CTkFrame(main_container, fg_color="transparent")
input_frame.pack(pady=10)

type_combo = ctk.CTkComboBox(input_frame, values=["Code 128", "Code 39", "QR Code"], width=140, height=50)
type_combo.set("Code 128")
type_combo.pack(side="left", padx=5)

entry = ctk.CTkEntry(input_frame, width=300, height=50, font=ctk.CTkFont(size=18), placeholder_text="바코드 데이터 입력")
entry.pack(side="left", padx=5)

gen_btn = ctk.CTkButton(input_frame, text="생성", width=80, height=50, font=ctk.CTkFont(weight="bold"), command=generate_barcode)
gen_btn.pack(side="left", padx=5)

fav_btn = ctk.CTkButton(input_frame, text="⭐ 저장", width=80, height=50, fg_color="#f59e0b", hover_color="#d97706", command=add_to_favorites)
fav_btn.pack(side="left", padx=5)

fav_combo = ctk.CTkOptionMenu(main_container, width=450, height=35, values=["🌟 자주 쓰는 바코드 꺼내기..."], command=load_favorite)
fav_combo.pack(pady=10)

barcode_display_frame = ctk.CTkFrame(main_container, width=600, height=250, fg_color="white", corner_radius=10)
barcode_display_frame.pack(pady=20)
barcode_display_frame.pack_propagate(False)
barcode_label = ctk.CTkLabel(barcode_display_frame, text="Barcode Preview", text_color="gray")
barcode_label.pack(expand=True)

print_frame = ctk.CTkFrame(main_container, fg_color="transparent")
print_frame.pack(pady=10)
print_btn_full = ctk.CTkButton(print_frame, text="🖨️ 명함 크기 인쇄", state="disabled", command=lambda: print_barcode("full"))
print_btn_full.pack(side="left", padx=10)
print_btn_half = ctk.CTkButton(print_frame, text="🖨️ 1/2 크기 인쇄", state="disabled", command=lambda: print_barcode("half"))
print_btn_half.pack(side="left", padx=10)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=200, height=40, state="disabled", command=lambda: current_barcode_pil.save(f"barcode_{current_barcode_data}.png"))
save_button.pack(pady=20)

credit = ctk.CTkLabel(main_container, text="Developed by 룩희 & 재민", font=ctk.CTkFont(size=13, slant="italic"), text_color="#64748b")
credit.pack(side="bottom", pady=15)

load_favorites()
root.mainloop()
