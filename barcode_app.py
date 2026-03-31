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
history_list = [] 

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

def wrap_text_korean(text, font, max_width, draw):
    if not text: return []
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0,0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
    return lines

def create_final_barcode_image(barcode_img, data, product_name):
    margin = 25
    barcode_w = barcode_img.size[0]
    barcode_h = barcode_img.size[1]
    
    # 💡 간격 기준 (상품명과 바코드, 바코드와 데이터 사이의 여백)
    inter_element_spacing = 20 
    
    try:
        font_p = resource_path("malgun.ttf")
        title_font = ImageFont.truetype(font_p, 26) 
    except:
        title_font = ImageFont.load_default()

    dummy_img = Image.new('RGBA', (1, 1), 'white')
    draw = ImageDraw.Draw(dummy_img)
    
    lines = []
    if product_name:
        lines = wrap_text_korean(product_name, title_font, barcode_w, draw)
    
    line_height = 0
    if lines:
        bbox = draw.textbbox((0,0), "A", font=title_font)
        line_height = bbox[3] - bbox[1] + 8 
        
    header_height = (len(lines) * line_height) + inter_element_spacing if product_name else 10
    
    # 💡 [핵심 수정] 데이터 텍스트 폰트 크기를 고해상도에 맞춰 8 -> 22로 대폭 상향!
    try:
        font_p = resource_path("arial.ttf")
        data_font = ImageFont.truetype(font_p, 22) 
    except:
        data_font = ImageFont.load_default()
        
    bbox = draw.textbbox((0, 0), data, font=data_font)
    data_text_h = bbox[3] - bbox[1]
    
    new_w = barcode_w + (margin * 2)
    new_h = barcode_h + header_height + inter_element_spacing + data_text_h + 15
    final_img = Image.new('RGBA', (new_w, new_h), 'white')
    draw = ImageDraw.Draw(final_img)
    
    if product_name:
        y_text = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_w = bbox[2] - bbox[0]
            x_text = margin + (barcode_w - text_w) // 2 
            draw.text((x_text, y_text), line, font=title_font, fill="black")
            y_text += line_height

    final_img.paste(barcode_img, (margin, header_height))
    
    # 바코드 데이터 텍스트 그리기
    y_data_text = header_height + barcode_h + inter_element_spacing
    bbox = draw.textbbox((0, 0), data, font=data_font)
    text_w = bbox[2] - bbox[0]
    x_data_text = margin + (barcode_w - text_w) // 2
    draw.text((x_data_text, y_data_text), data, font=data_font, fill="black")
    
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
            
            # 바코드 그릴 때 자동 글자 삽입 기능은 끄기 (수동으로 그리기 위해)
            options = {"write_text": False, "font_size": 6, "dpi": 300, "font_path": font_p}
            my_barcode.write(fp, options=options) 
            barcode_img = Image.open(fp).convert('RGBA')
        
        final_img = create_final_barcode_image(barcode_img, data, p_name)
        current_barcode_pil = final_img
        current_barcode_data = data
        
        max_w, max_h = 560, 210 
        img_w, img_h = final_img.size
        ratio = min(max_w / img_w, max_h / img_h)
        display_w, display_h = int(img_w * ratio), int(img_h * ratio)
        
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        barcode_label.configure(image=img_ctk, text="")
        
        save_button.configure(state="normal", fg_color="#2FA572")
        print_btn_full.configure(state="normal")
        print_btn_half.configure(state="normal")
        
        add_to_history(data, b_type, p_name, final_img)
        
    except Exception as e:
        messagebox.showerror("오류", f"생성 실패: {e}")

def add_to_history(data, b_type, p_name, img):
    global history_list
    for item in history_list:
        if item['data'] == data and item['type'] == b_type and item.get('p_name') == p_name:
            history_list.remove(item)
            break
    history_list.insert(0, {'data': data, 'type': b_type, 'p_name': p_name, 'pil_img': img})
    if len(history_list) > 10: 
        history_list.pop()
    display_history_list()

def delete_history_item(index):
    global history_list
    history_list.pop(index)
    display_history_list()

def display_history_list():
    for widget in history_scroll.winfo_children():
        widget.destroy()
        
    for i, item in enumerate(history_list):
        item_frame = ctk.CTkFrame(history_scroll, fg_color="transparent")
        item_frame.pack(side="left", padx=5)
        
        display_text = item.get('p_name', '')
        if not display_text: display_text = item['data']
        if len(display_text) > 8: display_text = display_text[:8] + ".."
        
        btn_text = f"[{item['type']}]\n{display_text}"
        btn = ctk.CTkButton(item_frame, text=btn_text, font=ctk.CTkFont(size=12), 
                             fg_color="#1e293b", hover_color="#334155", corner_radius=10,
                             height=50, width=120,
                             command=lambda idx=i: display_history_item(idx))
        btn.pack(side="left")
        
        del_btn = ctk.CTkButton(item_frame, text="X", font=ctk.CTkFont(size=12, weight="bold"),
                                fg_color="#ef4444", hover_color="#dc2626", corner_radius=8,
                                height=50, width=30,
                                command=lambda idx=i: delete_history_item(idx))
        del_btn.pack(side="left", padx=(2, 0))

def display_history_item(index):
    global current_barcode_pil, current_barcode_data
    item = history_list[index]
    final_img = item['pil_img']
    
    current_barcode_pil = final_img
    current_barcode_data = item['data']
    
    max_w, max_h = 560, 210 
    img_w, img_h = final_img.size
    ratio = min(max_w / img_w, max_h / img_h)
    display_w, display_h = int(img_w * ratio), int(img_h * ratio)
    img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
    
    barcode_label.configure(image=img_ctk, text="") 
    
    entry.delete(0, 'end')
    entry.insert(0, item['data'])
    type_combo.set(item['type'])
    product_entry.delete(0, 'end')
    product_entry.insert(0, item.get('p_name', ''))
    
    save_button.configure(state="normal", fg_color="#2FA572")
    print_btn_full.configure(state="normal")
    print_btn_half.configure(state="normal")

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
    data, b_type, p_name = entry.get(), type_combo.get(), product_entry.get()
    if not data: return
    if len(favorites_list) >= 20:
        messagebox.showwarning("경고", "최대 20개까지만 저장 가능합니다.")
        return
    
    if not any(f['data'] == data for f in favorites_list):
        favorites_list.append({'data': data, 'type': b_type, 'p_name': p_name})
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
            product_entry.delete(0, 'end')
            product_entry.insert(0, f.get('p_name', ''))
            generate_barcode()
            break
    fav_combo.set("🌟 자주 쓰는 바코드 꺼내기...")

# --- UI 메인 구성 ---
root = ctk.CTk()
root.title("Warehouse Pro v5.6 - Logistics Expert") 
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
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.92)

header = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"))
header.pack(pady=(20, 20))

product_frame = ctk.CTkFrame(main_container, fg_color="transparent")
product_frame.pack(pady=(0, 15))

product_entry = ctk.CTkEntry(product_frame, width=450, height=45, placeholder_text="[상품명 입력] 바코드 상단에 인쇄됩니다.")
product_entry.pack(side="left", padx=(0, 5))

product_clear_btn = ctk.CTkButton(product_frame, text="X", width=45, height=45, font=ctk.CTkFont(weight="bold", size=16), 
                                  fg_color="#ef4444", hover_color="#dc2626", 
                                  command=lambda: product_entry.delete(0, 'end'))
product_clear_btn.pack(side="left")

input_frame = ctk.CTkFrame(main_container, fg_color="transparent")
input_frame.pack(pady=5)

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

barcode_display_frame = ctk.CTkFrame(main_container, width=600, height=230, fg_color="white", corner_radius=10)
barcode_display_frame.pack(pady=5)
barcode_display_frame.pack_propagate(False)
barcode_label = ctk.CTkLabel(barcode_display_frame, text="Barcode Preview", text_color="gray")
barcode_label.pack(expand=True)

print_frame = ctk.CTkFrame(main_container, fg_color="transparent")
print_frame.pack(pady=5)
print_btn_full = ctk.CTkButton(print_frame, text="🖨️ 명함 크기 인쇄", state="disabled", command=lambda: print_barcode("full"))
print_btn_full.pack(side="left", padx=10)
print_btn_half = ctk.CTkButton(print_frame, text="🖨️ 1/2 크기 인쇄", state="disabled", command=lambda: print_barcode("half"))
print_btn_half.pack(side="left", padx=10)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=200, height=35, state="disabled", command=lambda: current_barcode_pil.save(f"barcode_{current_barcode_data}.png"))
save_button.pack(pady=5)

ctk.CTkLabel(main_container, text="생성 히스토리", font=ctk.CTkFont(size=14, weight="bold"), text_color="#A0A0A0").pack(pady=(5, 0))
history_scroll = ctk.CTkScrollableFrame(main_container, height=60, orientation="horizontal", fg_color="transparent", scrollbar_button_color=("gray60", "gray40"), border_width=0)
history_scroll.pack(fill="x", padx=40, pady=(0, 5))

credit = ctk.CTkLabel(main_container, text="Developed by 룩희 & 재민", font=ctk.CTkFont(size=12, slant="italic"), text_color="#64748b")
credit.pack(side="bottom", pady=10)

load_favorites()
root.mainloop()
