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

# Windows 인쇄 라이브러리 (배포 시 환경 확인 필요)
try:
    import win32print
    import win32ui
    from PIL import ImageWin
except ImportError:
    print("인쇄 기능을 사용하려면 pywin32 라이브러리가 필요합니다.")

# 💡 실행 환경 리소스 경로 (PyInstaller 빌드 대응)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 💾 데이터 자동 저장 파일 설정
FAV_FILE = "favorites.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# 글로벌 변수
current_barcode_pil = None
current_barcode_data = ""
history_list = []
favorites_list = []

# --- [기능 1] 데이터 자동 저장 및 로드 ---
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

# --- [기능 2] 상품명 포함 바코드 생성 ---
def create_final_barcode_image(barcode_img, data, product_name):
    lw, margin = 55, 20
    header_height = 50 if product_name else 10
    
    new_w = barcode_img.size[0] + lw + margin
    new_h = barcode_img.size[1] + header_height
    final_img = Image.new('RGBA', (new_w, new_h), 'white')
    draw = ImageDraw.Draw(final_img)
    
    try:
        font_path = resource_path("arial.ttf")
        font = ImageFont.truetype(font_path, 16)
        title_font = ImageFont.truetype(font_path, 20)
    except:
        font = title_font = ImageFont.load_default()

    # 상품명 표시 (바코드 상단)
    if product_name:
        draw.text((margin, 10), f"ITEM: {product_name}", font=title_font, fill="black")

    final_img.paste(barcode_img, (0, header_height))
    
    # ICQA 로고 삽입
    logo_size = 50
    logo = Image.new('RGBA', (logo_size, logo_size), (0,0,0,0))
    l_draw = ImageDraw.Draw(logo)
    l_draw.rounded_rectangle((0, 0, logo_size, logo_size), radius=12, fill="#333333")
    l_draw.text((8, 15), "ICQA", font=font, fill="white")
    final_img.paste(logo, (new_w - logo_size - 15, 15), logo)
    
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
        if b_type == "QR Code":
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        else:
            code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            my_barcode = code_class(data, writer=ImageWriter())
            my_barcode.write(fp, options={"write_text": True, "font_size": 10, "dpi": 300}) 
            barcode_img = Image.open(fp).convert('RGBA')
        
        final_img = create_final_barcode_image(barcode_img, data, p_name)
        current_barcode_pil = final_img
        current_barcode_data = data
        
        # 프리뷰 업데이트
        display_w = 480
        display_h = int(final_img.size[1] * (display_w / final_img.size[0]))
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        barcode_label.configure(image=img_ctk, text="")
        
        save_button.configure(state="normal", fg_color="#2FA572")
        print_btn_full.configure(state="normal")
        print_btn_half.configure(state="normal")
        
        add_to_history(data, b_type, final_img)
    except Exception as e:
        messagebox.showerror("오류", f"생성 실패: {e}")

# --- [기능 3] 명함 사이즈 인쇄 로직 ---
def print_barcode(size_mode):
    if not current_barcode_pil: return
    try:
        printer_name = win32print.GetDefaultPrinter()
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        
        # 명함(90x50mm) 또는 1/2명함(45x50mm) 계산
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

# --- [기능 4] 즐겨찾기 관리 ---
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

# --- UI 메인 구성 ---
root = ctk.CTk()
root.title("Warehouse Pro v5.0 - Logistics Expert")
root.geometry("1000x850")

main_container = ctk.CTkFrame(root, corner_radius=20, fg_color=("#f0f0f0", "#141414"))
main_container.pack(padx=30, pady=30, fill="both", expand=True)

header = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=32, weight="bold"))
header.pack(pady=30)

# 상품명 입력칸 (New!)
product_entry = ctk.CTkEntry(main_container, width=500, height=45, placeholder_text="상품명을 입력하면 바코드 위에 표시됩니다.")
product_entry.pack(pady=(0, 15))

# 입력 영역
input_frame = ctk.CTkFrame(main_container, fg_color="transparent")
input_frame.pack(pady=10)

type_combo = ctk.CTkComboBox(input_frame, values=["Code 128", "Code 39", "QR Code"], width=140, height=50)
type_combo.set("Code 128")
type_combo.pack(side="left", padx=5)

entry = ctk.CTkEntry(input_frame, width=300, height=50, font=ctk.CTkFont(size=18), placeholder_text="데이터 입력")
entry.pack(side="left", padx=5)

gen_btn = ctk.CTkButton(input_frame, text="생성", width=80, height=50, font=ctk.CTkFont(weight="bold"), command=generate_barcode)
gen_btn.pack(side="left", padx=5)

fav_btn = ctk.CTkButton(input_frame, text="⭐ 저장", width=80, height=50, fg_color="#f59e0b", command=add_to_favorites)
fav_btn.pack(side="left", padx=5)

# 즐겨찾기 선택 메뉴
fav_combo = ctk.CTkOptionMenu(main_container, width=450, height=35, values=[], command=lambda c: print("Selected")) # load_favorite 연동 필요
fav_combo.pack(pady=10)

# 바코드 프리뷰
barcode_display_frame = ctk.CTkFrame(main_container, width=600, height=250, fg_color="white", corner_radius=10)
barcode_display_frame.pack(pady=20)
barcode_display_frame.pack_propagate(False)
barcode_label = ctk.CTkLabel(barcode_display_frame, text="Barcode Preview", text_color="gray")
barcode_label.pack(expand=True)

# 인쇄 옵션 버튼 (New!)
print_frame = ctk.CTkFrame(main_container, fg_color="transparent")
print_frame.pack(pady=10)
print_btn_full = ctk.CTkButton(print_frame, text="🖨️ 명함 크기 인쇄", state="disabled", command=lambda: print_barcode("full"))
print_btn_full.pack(side="left", padx=10)
print_btn_half = ctk.CTkButton(print_frame, text="🖨️ 1/2 크기 인쇄", state="disabled", command=lambda: print_barcode("half"))
print_btn_half.pack(side="left", padx=10)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=200, height=40, state="disabled", command=lambda: current_barcode_pil.save(f"barcode_{current_barcode_data}.png"))
save_button.pack(pady=20)

# 하단 크레딧 (수정 완료)
credit = ctk.CTkLabel(main_container, text="Developed by 룩희 & 재민", font=ctk.CTkFont(size=13, slant="italic"), text_color="#64748b")
credit.pack(side="bottom", pady=15)

load_favorites() # 즐겨찾기 불러오기
root.mainloop()
