import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import qrcode
import random

# 💡 [필수 설정] 프로그램 실행 환경에 따른 폰트 및 리소스 경로 찾기 함수
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

import sys #resource_path에서 사용

ctk.set_appearance_mode("Dark") # 서울 야경과 어울리는 다크 모드 고정
ctk.set_default_color_theme("dark-blue") # 고급스러운 컬러 테마

current_barcode_pil = None # 💡 저장용 이미지를 담을 PIL 이미지 변수
current_barcode_data = ""
history_list = [] # 💡 생성 히스토리를 저장할 리스트 (최대 10개)

# 💡 [삭제] create_space_background 또는 create_seoul_background 함수는 삭제합니다.

# 🏷️ ICQA 로고 디자인 (v4.1 Gray 배경 유지)
def get_icqa_logo(size=55):
    logo = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(logo)
    # v4.1 그레이 배경 반영
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
    b_type = type_combo.get() # 멀티 포맷 선택 값 가져오기
    
    if not data:
        messagebox.showwarning("경고", "데이터를 입력해 주세요.")
        return
        
    try:
        # 💡 [검증 방법] arial.ttf 폰트 파일을 프로그램 안에 심어서 cannot open resource 에러 방지
        font_path = resource_path("arial.ttf")
        fp = io.BytesIO()
        
        # 💡 [멀티 포맷 지원 구현]
        if b_type == "QR Code":
            # QR 코드 구현
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H, # 높은 오류 수정 레벨 설정
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
            
            # QR 코드 중앙에 로고 삽입
            lw = 70 # QR 코드용 큰 로고
            icqa_logo = get_icqa_logo(lw)
            # 로고 위치 계산
            logo_x = (barcode_img.size[0] - lw) // 2
            logo_y = (barcode_img.size[1] - lw) // 2
            
            # QR 코드 중앙에 로고 합성 (복제하여 원본 유지)
            barcode_img.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
            final_img = barcode_img
            
        else:
            # 일반 바코드 (Code 128, Code 39)
            # 💡 [요청사항 반영] Code 128이 기본
            try:
                code_class = barcode.get_barcode_class(b_type.lower().replace(" ", ""))
            except:
                messagebox.showerror("오류", f"지원하지 않는 바코드 포맷입니다: {b_type}")
                return

            writer = ImageWriter()
            my_barcode = code_class(data, writer=writer)
            
            # 💡 [화면 스캔 최적화 정밀 설정]
            options = {
                "write_text": True, 
                "font_path": font_path, 
                "font_size": 10, 
                "text_distance": 5.0, 
                "module_width": 0.4,   # 💡 화면 픽셀 매칭을 위한 선 두께 조정
                "module_height": 18.0,  # 💡 미관상 가장 보기 좋은 세로 길이
                "quiet_zone": 10.0,     # 💡 주변 흰색 여백 충분히 확보
                "dpi": 300
            }
            
            my_barcode.write(fp, options=options) 
            barcode_img = Image.open(fp).convert('RGBA')
            
            # 일반 바코드 오른쪽에 ICQA 로고 붙이기
            lw = 55 # 일반 바코드용 로고
            icqa_logo = get_icqa_logo(lw)
            
            # 바코드 오른쪽에 로고 여백 추가
            margin = 10
            new_w = barcode_img.size[0] + lw + margin
            new_h = barcode_img.size[1]
            final_img = Image.new('RGBA', (new_w, new_h), 'white')
            
            # 바코드 먼저 복사
            final_img.paste(barcode_img, (0, 0))
            
            # 로고 위치 계산
            logo_x = barcode_img.size[0] + 5 # 💡 quiet zone에 배치
            logo_y = (barcode_img.size[1] - lw) // 2 # 세로 중앙
            final_img.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
        
        current_barcode_pil = final_img
        current_barcode_data = data
        
        # 미리보기 이미지 세련된 크기 설정
        # (v3.0의 정돈된 크기 유지 - 너비 480px 내외)
        img_w, img_h = final_img.size
        display_w = 480
        display_h = int(img_h * (display_w / img_w))
        
        img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        save_button.configure(state="normal", fg_color="#2FA572") # 활성화 시 초록색으로 변경
        
        # 💡 [스마트 생성 히스토리 중복 누적 방지 구현 - PART 1]
        # 일반 생성 모드일 때만 히스토리에 추가
        if not hasattr(generate_barcode, "history_mode"):
             add_to_history(data, b_type, final_img)
        else:
             # 히스토리 모드 실행 후 속성 삭제
             delattr(generate_barcode, "history_mode")

    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

# [스마트 생성 히스토리 중복 누적 방지 구현 - PART 2]
# add_to_history는 동일하게 유지하되, display_history_item를 스마트하게 수정

# 💡 [핵심 구현] 생성 히스토리 목록 화면 업데이트 함수
def display_history_list():
    global history_list
    # 기존 버튼 제거
    for widget in history_scroll.winfo_children():
        widget.destroy()
        
    # 히스토리 버튼 생성 (가로 스크롤 프레임 안에)
    for i, item in enumerate(history_list):
        # 💡 히스토리 카드 버튼 (v4.1 디자인 유지)
        # [기존 Code 128] WH12345 형태의 텍스트 버튼으로 구현
        
        btn_text = f"[{item['type']}]\n{item['data']}"
        btn = ctk.CTkButton(history_scroll, text=btn_text, font=ctk.CTkFont(size=12), 
                             fg_color="#1e293b", hover_color="#334155", corner_radius=10,
                             height=60, width=180,
                             # 💡 [스마트 생성 히스토리 중복 누적 방지 구현 - PART 3] 
                             # 람다식 대신 전용 함수 연결
                             command=lambda index=i: display_history_item(index))
        btn.pack(side="left", padx=10)

# 💡 [핵심 구현] 스마트 생성 히스토리 아이템 클릭 시 화면 업데이트 함수
def display_history_item(index):
    global history_list, current_barcode_pil, current_barcode_data
    
    item = history_list[index]
    final_img = item['pil_img']
    
    # 💡 [요청사항 반영] 클릭 시 이미지를 바로 화면에 띄우고 파일 저장 변수 업데이트
    current_barcode_pil = final_img
    current_barcode_data = item['data']
    
    # 미리보기 이미지 세련된 크기 설정
    img_w, img_h = final_img.size
    display_w = 480
    display_h = int(img_h * (display_w / img_w))
    
    # CTkImage로 변환
    img_ctk = ctk.CTkImage(light_image=final_img, dark_image=final_img, size=(display_w, display_h))
    
    barcode_label.configure(image=img_ctk, text="") 
    barcode_label.image = img_ctk
    
    # 입력창과 콤보박스 정보 업데이트
    entry.delete(0, 'end')
    entry.insert(0, current_barcode_data)
    type_combo.set(item['type'])
    
    save_button.configure(state="normal", fg_color="#2FA572")
    
    # 💡 [스마트 생성 히스토리 중복 누적 방지 구현 - PART 4]
    # generate_barcode()를 호출하지 않고 여기서 이미지 디스플레이가 끝나므로 중복 적재 안됨

def save_barcode():
    if current_barcode_pil:
        try:
            filename = f"barcode_{current_barcode_data}.png"
            # paste한 PIL 이미지를 저장
            current_barcode_pil.save(filename) 
            messagebox.showinfo("성공", f"{filename} 파일이 저장되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# 💡 [핵심 구현] 생성 히스토리 추가 함수
def add_to_history(data, b_type, img):
    global history_list
    
    # 💡 스마트 중복 체크 로직
    # 목록에 동일한 데이터가 있으면 지우고 맨 위로 올림
    for item in history_list:
        if item['data'] == data and item['type'] == b_type:
             history_list.remove(item)
             break
             
    # 히스토리에 PIL 이미지를 저장 (화면 로딩 및 저장 속도 향상)
    entry_dict = {'data': data, 'type': b_type, 'pil_img': img}
    history_list.insert(0, entry_dict) # 가장 최근 것이 맨 위로
    
    # 10개로 제한
    if len(history_list) > 10:
        history_list.pop()
    
    display_history_list()

# --- 모던 & 대형 프라이빗 UI 레이아웃 v4.2 (서울 나이트 뷰 에디션) ---
root = ctk.CTk()
root.title("Warehouse Pro v4.2 - Seoul Night View")
# v3.0의 시원한 크기 유지 (1000x800)
root.geometry("1000x800") 

# 💡 [요청사항 반영] 실제 사진 배경 준비 (`seoul_night.jpg` 필수 업로드)
try:
    # `seoul_night.jpg` 폰트 파일이 없을 수 있으므로 resource_path 사용
    bg_image_path = resource_path("seoul_night.jpg")
    bg_pil = Image.open(bg_image_path)
    bg_ctk = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1000, 800))
    bg_label = ctk.CTkLabel(root, text="", image=bg_ctk)
    bg_label.pack(fill="both", expand=True)
except:
    # 사진 로딩 실패 시 v4.1 우주 느낌 다크 그라데이션 배경 구현
    bg_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="#0a0f1e") # 깊은 밤하늘 색상
    bg_frame.pack(fill="both", expand=True)
    bg_label = bg_frame # bg_label을 bg_frame으로 대체하여 하단 .place 코드 정상 작동 유도

# 중앙 콘텐츠 영역 (💡 Glassmorphism 투명 패널 구현)
main_container = ctk.CTkFrame(bg_label, corner_radius=25, fg_color=("#333333", "#141414"), border_width=1, border_color="#333333")
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

# 상단 헤더
header_label = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"), text_color="#E0E0E0")
header_label.pack(pady=(50, 40))

# 입력창 섹션 (💡 고급스러운 카드 형태)
input_card = ctk.CTkFrame(main_container, fg_color="transparent")
input_card.pack(fill="x", padx=60)

# 💡 [멀티 포맷 지원 구현] 바코드 포맷 선택 ComboBox 추가
type_combo = ctk.CTkComboBox(input_card, values=["Code 128", "Code 39", "QR Code"], width=150, height=60, font=ctk.CTkFont(size=16), state="readonly")
type_combo.set("Code 128") # Code 128이 기본
type_combo.pack(side="left", padx=(0, 20))

entry = ctk.CTkEntry(input_card, width=400, height=60, font=ctk.CTkFont(size=20),
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

# 💡 [핵심 구현] 생성 히스토리 가로 스크롤 영역
# v4.1 Glassmorphism 투명 패널 위에 화이트 카드 형태
ctk.CTkLabel(main_container, text="생성 히스토리", font=ctk.CTkFont(size=14, weight="bold"), text_color="#A0A0A0").pack(pady=(10, 5))

# 가로 스크롤 가능한 CTkScrollableFrame 사용
history_scroll = ctk.CTkScrollableFrame(main_container, height=100, orientation="horizontal", fg_color="transparent", 
                                          scrollbar_button_color=("gray60", "gray40"), border_width=0)
history_scroll.pack(fill="x", padx=40, pady=10)

# 하단 정보 및 버튼
status_label = ctk.CTkLabel(main_container, text="Coupang Logistics Team / v3.0 / Designed for Efficiency", font=ctk.CTkFont(size=12), text_color="#808080")
status_label.pack(side="bottom", pady=20)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=250, height=50, 
                            font=ctk.CTkFont(size=16), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(side="bottom", pady=(0, 10))

root.mainloop()
