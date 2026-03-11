import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import os
import qrcode
import sys

# 💡 실행 환경에 따른 리소스(폰트, 사진) 경로 찾기
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

current_barcode_pil = None
current_barcode_data = ""
history_list = []
favorites_list = []

# 🏷️ ICQA 로고 생성
def get_icqa_logo(size=55):
    logo = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(logo)
    draw.rounded_rectangle((0, 0, size, size), radius=12, fill="#333333") 
    try:
        font_path = resource_path("arial.ttf")
        font = ImageFont.truetype(font_path, 16)
    except:
        font = ImageFont.load_default()
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
        font_path = resource_path("arial.ttf")
        fp = io.BytesIO()
        
        if b_type == "QR Code":
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
            lw = 60
            icqa_logo = get_icqa_logo(lw)
            barcode_img.paste(icqa_logo, (barcode_img.size[0] - lw - 15, 15), icqa_logo)
            final_img = barcode_img
            
        else:
            code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            writer = ImageWriter()
            my_barcode = code_class(data, writer=writer)
            
            options = {
                "write_text": True, "font_path": font_path, "font_size": 10, 
                "text_distance": 5.0, "module_width": 0.4, "module_height": 18.0, 
                "quiet_zone": 10.0, "dpi": 300
            }
            my_barcode.write(fp, options=options) 
            barcode_img = Image.open(fp).convert('RGBA')
            
            lw = 50
            icqa_logo = get_icqa_logo(lw)
            margin = 15
            
            new_w = barcode_img.size[0] + lw + margin
            new_h = barcode_img.size[1]
            final_img = Image.new('RGBA', (new_w, new_h), 'white')
            final_img.paste(barcode_img, (0, 0))
            final_img.paste(icqa_logo, (new_w - lw - margin, margin), icqa_logo)
        
        current_barcode_pil = final_img
        current_barcode_data = data
        
        display_w = 480
        display_h = int(final_img.size[1] * (display_w / final_img.size[0]))
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        save_button.configure(state="normal", fg_color="#2FA572")
        
        add_to_history(data, b_type, final_img)

    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

# ⭐ 즐겨찾기에 바코드 저장
def add_to_favorites():
    global favorites_list
    data = entry.get()
    b_type = type_combo.get()
    
    if not data:
        messagebox.showwarning("경고", "저장할 데이터를 먼저 입력해 주세요.")
        return
        
    for item in favorites_list:
        if item['data'] == data and item['type'] == b_type:
            messagebox.showinfo("알림", "이미 즐겨찾기에 저장된 바코드입니다.")
            return
            
    if len(favorites_list) >= 20:
        messagebox.showwarning("경고", "자주 쓰는 바코드는 최대 20개까지만 저장할 수 있습니다.")
        return
        
    favorites_list.append({'data': data, 'type': b_type})
    update_fav_combo()
    messagebox.showinfo("성공", f"[{b_type}] {data}\n자주 쓰는 바코드에 추가되었습니다!")

# ⭐ 즐겨찾기 목록 업데이트
def update_fav_combo():
    vals = ["🌟 자주 쓰는 바코드 꺼내기..."] + [f"[{f['type']}] {f['data']}" for f in favorites_list]
    fav_combo.configure(values=vals)
    fav_combo.set("🌟 자주 쓰는 바코드 꺼내기...")

# ⭐ 즐겨찾기 선택 시 불러오기
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

# 💡 [신규] 즐겨찾기 관리 창 열기
def open_manage_favorites():
    manage_win = ctk.CTkToplevel(root)
    manage_win.title("즐겨찾기 관리")
    manage_win.geometry("450x450")
    manage_win.transient(root)
    manage_win.grab_set()

    ctk.CTkLabel(manage_win, text="⚙️ 자주 쓰는 바코드 관리", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

    scroll = ctk.CTkScrollableFrame(manage_win, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def refresh_manage_list():
        for w in scroll.winfo_children():
            w.destroy()
        
        if not favorites_list:
            ctk.CTkLabel(scroll, text="저장된 즐겨찾기가 없습니다.", text_color="gray").pack(pady=20)
            return

        for i, fav in enumerate(favorites_list):
            frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8)
            frame.pack(fill="x", pady=5)
            
            lbl = ctk.CTkLabel(frame, text=f"[{fav['type']}] {fav['data']}", font=ctk.CTkFont(size=14))
            lbl.pack(side="left", padx=15, pady=10)
            
            del_btn = ctk.CTkButton(frame, text="삭제", width=50, fg_color="#ef4444", hover_color="#dc2626", command=lambda idx=i: delete_fav(idx))
            del_btn.pack(side="right", padx=(5, 10))
            
            edit_btn = ctk.CTkButton(frame, text="수정", width=50, fg_color="#3b82f6", hover_color="#2563eb", command=lambda idx=i: open_edit_fav(idx))
            edit_btn.pack(side="right", padx=5)

    def delete_fav(idx):
        favorites_list.pop(idx)
        update_fav_combo()
        refresh_manage_list()

    def open_edit_fav(idx):
        edit_win = ctk.CTkToplevel(manage_win)
        edit_win.title("수정")
        edit_win.geometry("300x250")
        edit_win.transient(manage_win)
        edit_win.grab_set()

        ctk.CTkLabel(edit_win, text="바코드 종류", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        edit_type_combo = ctk.CTkComboBox(edit_win, values=["Code 128", "Code 39", "QR Code"])
        edit_type_combo.set(favorites_list[idx]['type'])
        edit_type_combo.pack()

        ctk.CTkLabel(edit_win, text="바코드 데이터", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        edit_data_entry = ctk.CTkEntry(edit_win, width=200)
        edit_data_entry.insert(0, favorites_list[idx]['data'])
        edit_data_entry.pack()

        def save_edit():
            new_data = edit_data_entry.get()
            if not new_data: return
            favorites_list[idx]['type'] = edit_type_combo.get()
            favorites_list[idx]['data'] = new_data
            update_fav_combo()
            refresh_manage_list()
            edit_win.destroy()

        ctk.CTkButton(edit_win, text="저장", width=100, fg_color="#2FA572", hover_color="#1D7A50", command=save_edit).pack(pady=20)

    refresh_manage_list()

def delete_history_item(index):
    global history_list
    history_list.pop(index)
    display_history_list() 

def display_history_list():
    for widget in history_scroll.winfo_children():
        widget.destroy()
        
    for i, item in enumerate(history_list):
        item_frame = ctk.CTkFrame(history_scroll, fg_color="transparent")
        item_frame.pack(side="left", padx=10)
        
        btn_text = f"[{item['type']}]\n{item['data']}"
        btn = ctk.CTkButton(item_frame, text=btn_text, font=ctk.CTkFont(size=12), 
                             fg_color="#1e293b", hover_color="#334155", corner_radius=10,
                             height=60, width=160,
                             command=lambda idx=i: display_history_item(idx))
        btn.pack(side="left")
        
        del_btn = ctk.CTkButton(item_frame, text="삭제", font=ctk.CTkFont(size=12, weight="bold"),
                                fg_color="#ef4444", hover_color="#dc2626", corner_radius=8,
                                height=60, width=45,
                                command=lambda idx=i: delete_history_item(idx))
        del_btn.pack(side="left", padx=(5, 0))

def display_history_item(index):
    global current_barcode_pil, current_barcode_data
    item = history_list[index]
    final_img = item['pil_img']
    
    current_barcode_pil = final_img
    current_barcode_data = item['data']
    
    display_w = 480
    display_h = int(final_img.size[1] * (display_w / final_img.size[0]))
    img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
    
    barcode_label.configure(image=img_ctk, text="") 
    barcode_label.image = img_ctk
    
    entry.delete(0, 'end')
    entry.insert(0, current_barcode_data)
    type_combo.set(item['type'])
    save_button.configure(state="normal", fg_color="#2FA572")

def save_barcode():
    if current_barcode_pil:
        try:
            filename = f"barcode_{current_barcode_data}.png"
            current_barcode_pil.save(filename) 
            messagebox.showinfo("성공", f"{filename} 파일이 저장되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

def add_to_history(data, b_type, img):
    global history_list
    for item in history_list:
        if item['data'] == data and item['type'] == b_type:
             history_list.remove(item)
             break
    history_list.insert(0, {'data': data, 'type': b_type, 'pil_img': img})
    if len(history_list) > 10:
        history_list.pop()
    display_history_list()


# --- 메인 창 세팅 ---
root = ctk.CTk()
root.title("Warehouse Pro v4.7 - Seoul Night View")
root.geometry("1000x800") 

try:
    bg_image_path = resource_path("logistic_future.jpg")
    bg_pil = Image.open(bg_image_path)
    bg_pil_high_res = ImageOps.fit(bg_pil, (2560, 1440), Image.Resampling.LANCZOS)
    bg_ctk = ctk.CTkImage(light_image=bg_pil_high_res, dark_image=bg_pil_high_res, size=(2560, 1440))
    
    bg_label = ctk.CTkLabel(root, text="", image=bg_ctk)
    bg_label.place(relx=0.5, rely=0.5, anchor="center") 
except:
    bg_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="#0a0f1e")
    bg_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
    bg_label = bg_frame

main_container = ctk.CTkFrame(root, corner_radius=25, fg_color=("#333333", "#141414"), border_width=1, border_color="#333333")
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

header_label = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"), text_color="#E0E0E0")
header_label.pack(pady=(40, 30))

input_row_container = ctk.CTkFrame(main_container, fg_color="transparent")
input_row_container.pack(fill="x", pady=(0, 20))

fav_row = ctk.CTkFrame(input_row_container, fg_color="transparent")
fav_row.pack(anchor="center", pady=(0, 10))

fav_combo = ctk.CTkOptionMenu(fav_row, values=["🌟 자주 쓰는 바코드 꺼내기..."], width=300, height=35, font=ctk.CTkFont(size=14), command=load_favorite, fg_color="#334155", button_color="#1e293b", button_hover_color="#475569")
fav_combo.pack(side="left")

# 💡 [추가] 즐겨찾기 관리 버튼
fav_manage_btn = ctk.CTkButton(fav_row, text="⚙️ 관리", width=60, height=35, font=ctk.CTkFont(size=14), fg_color="#475569", hover_color="#334155", command=open_manage_favorites)
fav_manage_btn.pack(side="left", padx=(10, 0))

input_card = ctk.CTkFrame(input_row_container, fg_color="transparent")
input_card.pack(anchor="center") 

type_combo = ctk.CTkComboBox(input_card, values=["Code 128", "Code 39", "QR Code"], width=150, height=60, font=ctk.CTkFont(size=16), state="readonly")
type_combo.set("Code 128")
type_combo.pack(side="left", padx=(0, 15))

entry = ctk.CTkEntry(input_card, width=400, height=60, font=ctk.CTkFont(size=20), placeholder_text="데이터를 입력해 주세요", border_width=2, border_color="#404040", fg_color="#1A1A1A")
entry.pack(side="left", padx=(0, 15))
entry.bind("<Return>", lambda event: generate_barcode())

generate_btn = ctk.CTkButton(input_card, text="생성", width=100, height=60, font=ctk.CTkFont(size=18, weight="bold"), command=generate_barcode)
generate_btn.pack(side="left")

fav_add_btn = ctk.CTkButton(input_card, text="⭐ 저장", width=80, height=60, font=ctk.CTkFont(size=16, weight="bold"), fg_color="#f59e0b", hover_color="#d97706", command=add_to_favorites)
fav_add_btn.pack(side="left", padx=(15, 0))

barcode_display_frame = ctk.CTkFrame(main_container, width=700, height=300, fg_color="white", corner_radius=15, border_width=1, border_color="gray80")
barcode_display_frame.pack(pady=20, padx=40)
barcode_display_frame.pack_propagate(False)

barcode_label = ctk.CTkLabel(barcode_display_frame, text="Barcode Preview", text_color="gray60", font=ctk.CTkFont(size=14))
barcode_label.pack(expand=True)

ctk.CTkLabel(main_container, text="생성 히스토리", font=ctk.CTkFont(size=14, weight="bold"), text_color="#A0A0A0").pack(pady=(5, 5))

history_scroll = ctk.CTkScrollableFrame(main_container, height=100, orientation="horizontal", fg_color="transparent", scrollbar_button_color=("gray60", "gray40"), border_width=0)
history_scroll.pack(fill="x", padx=40, pady=5)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=250, height=45, font=ctk.CTkFont(size=16), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(pady=(10, 15))

credit_label = ctk.CTkLabel(main_container, text="Designed & Developed by Theo with Gemini", font=ctk.CTkFont(size=12, slant="italic"), text_color="#64748b")
credit_label.pack(side="bottom", pady=(0, 15))

root.mainloop()
