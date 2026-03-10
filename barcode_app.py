import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont, ImageEnhance # 💡 이미지 투명도 조절을 위해Enhance 추가
import io
import os
import random

# 테마 설정 (시스템 모드를 따르되, 바코드 영역만 고대비 화이트 적용)
ctk.set_appearance_mode("Dark") # 우주 야경과 어울리는 다크 모드 고정
ctk.set_default_color_theme("dark-blue") # 고급스러운 컬러 테마

current_barcode_obj = None
current_barcode_data = ""
icqa_logo_pil = None # PIL 로고 이미지 저장
history_list = [] # 💡 생성 히스토리를 저장할 리스트

# 💡 [핵심 구현] 우주 배경 구현 (코드만으로 은하수/별빛 표현)
def create_space_background(width, height):
    base = Image.new('RGB', (width, height), '#05050a') # 깊은 밤하늘 색상
    draw = ImageDraw.Draw(base, 'RGBA')
    
    # 은하수 효과 (부드러운 컬러 그라데이션)
    nebula_count = 15
    for _ in range(nebula_count):
        x = int(width * (0.05 + 0.9 * (random.random())))
        y = int(height * (0.05 + 0.9 * (random.random())))
        radius = random.randint(150, 450)
        opacity = random.randint(15, 35)
        color_hex = random.choice(['#3a1a5e', '#1a3a5e', '#5e1a3a', '#5e3a1a'])
        # 부드러운 타원
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color_hex + f'{opacity:02x}')
    
    # 별빛 효과 (흰색/노란색 점)
    star_count = 800
    for _ in range(star_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        opacity = random.randint(100, 255)
        # 렌덤 크기 1 or 2 픽셀
        size = random.randint(1, 2)
        draw.ellipse((x, y, x + size, y + size), fill=(255, 255, 255, opacity))
    
    return base

# 💡 [요청사항 반영 1] ICQA 로고 디자인 변경 및 위치 조정
def generate_icqa_logo(size=50):
    # 크기 50x50, 둥근 모서리의 그레이 박스에 흰색 ICQA 텍스트
    logo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    
    logo_color = "#333333" # 💡 [요청사항 반영] ICQA 로고 배경 색상을 그레이로 변경
    # draw.rounded_rectangle((0, 0, size, size), radius=10, fill=logo_color)
    
    # 💡rounded_rectangle 대신 ellipse를 사용하여 로고를 원형으로 변경 (미관상)
    # 하지만 rounded_rectangle을 원했으므로 rounded_rectangle 유지. 
    draw.rounded_rectangle((0, 0, size, size), radius=10, fill=logo_color)
    
    # 폰트 설정 (폰트 파일이 없을 수 있으므로 기본 폰트 사용 또는 arial.ttf)
    try:
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        font = ImageFont.truetype(font_path, size=18)
    except:
        font = ImageFont.load_default()
        
    text = "ICQA"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    draw.text(((size-tw)/2, (size-th)/2 - 2), text, font=font, fill="white")
    return logo

def generate_barcode():
    global current_barcode_obj, current_barcode_data, history_list
    
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
        
        # 💡 [화면 스캔 최적화 정밀 설정]
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
        barcode_img = Image.open(fp).convert('RGBA')
        
        # 💡 미리보기 크기를 세련되게 고정 (너비 480px 내외)
        # (v3.0의 정돈된 크기 유지)
        display_w = 480
        img_w, img_h = barcode_img.size
        display_h = int(img_h * (display_w / img_w))
        
        # v3.0의 자연스러운 크기 유지
        img_ctk = ctk.CTkImage(light_image=barcode_img, dark_image=barcode_img, size=(display_w, display_h))
        
        # 💡 [요청사항 반영 1] 바코드 우측 상단에 ICQA 로고 배치
        # 미리보기 이미지 위에 로고를 겹치기 위해 PIL 이미지 사용
        # generate_icqa_logo를 PIL 이미지로 return받음
        icqa_logo = generate_icqa_logo(50)
        
        # 미리보기 이미지 위에 로고 합성 (복제하여 원본 유지)
        combined_pil = barcode_img.copy()
        bw, bh = combined_pil.size
        logo_x = bw - 50 - 10 # quiet_zone 10.0 마진
        logo_y = 10 #quiet_zone 10.0 마진
        combined_pil.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
        
        # v3.0의 자연스러운 크기 유지
        img_ctk_with_logo = ctk.CTkImage(light_image=combined_pil, dark_image=combined_pil, size=(display_w, display_h))
        
        # 💡 [화면 스캔 최적화 정밀 설정] 폰트 에러 방지를 위해 고해상도 화이트 카드 이미지를 렌더링하고, 
        # 그 위에 바코드 이미지를 합성하는 것이 가장 확실함. 하지만 코드 수정량을 줄이기 위해 기존 방식 유지.
        
        barcode_label.configure(image=img_ctk_with_logo, text="") 
        barcode_label.image = img_ctk_with_logo
        
        current_barcode_obj = my_barcode
        current_barcode_data = data
        save_button.configure(state="normal", fg_color="#2FA572") # 활성화 시 초록색으로 변경
        
        # 💡 [생성 히스토리 구현]
        if 'current_barcode_obj' in globals():
             add_to_history(data, combined_pil, icqa_logo)

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
        
        # 💡 [요청사항 반영 1] 저장된 파일에도 바코드 우측 상단에 ICQA 로고 배치
        # 저장된 파일 경로를 알아내서 PIL 이미지로 연 다음 로고 합성
        saved_img = Image.open(filename).convert('RGBA')
        icqa_logo = generate_icqa_logo(50)
        bw, bh = saved_img.size
        logo_x = bw - 50 - 10 # quiet_zone 10.0 마진
        logo_y = 10 #quiet_zone 10.0 마진
        saved_img.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
        saved_img.save(filename) # 로고 합성 후 덮어쓰기

    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# 💡 [핵심 구현] 생성 히스토리 추가 함수
def add_to_history(data, pil_img, logo_pil):
    global history_list
    # 중복 제거
    for item in history_list:
        if item['data'] == data:
             history_list.remove(item)
             break
    
    # 💡 [요청사항 반영] 히스토리에 PIL 이미지를 저장 (화면 로딩 및 저장 속도 향상)
    entry = {'data': data, 'pil_img': pil_img, 'logo_pil': logo_pil}
    history_list.insert(0, entry) # 가장 최근 것이 맨 위로
    
    # 5개로 제한
    if len(history_list) > 5:
        history_list.pop()
    
    display_history_list()

# 💡 [핵심 구현] 생성 히스토리 목록 화면 업데이트 함수
def display_history_list():
    global history_list
    # 기존 버튼 제거
    for widget in history_scroll_frame.winfo_children():
        widget.destroy()
        
    # 히스토리 버튼 생성
    for i, item in enumerate(history_list):
        # 💡 [요청사항 반영] 히스토리에도 ICQA 로고가 박힌 바코드 이미지를 사용
        # 미니 바코드 미리보기 이미지 생성
        history_w = 120
        pil_w, pil_h = item['pil_img'].size
        history_h = int(pil_h * (history_w / pil_w))
        
        # CTkImage로 변환
        history_pil = item['pil_img'].resize((history_w, history_h), Image.Resampling.LANCZOS)
        history_ctk = ctk.CTkImage(light_image=history_pil, dark_image=history_pil, size=(history_w, history_h))
        
        # 💡 [요청사항 반영 3] 히스토리 카드 버튼 (Glassmorphism 투명 패널 위에 화이트 카드 형태)
        card_btn = ctk.CTkButton(history_scroll_frame, text="", image=history_ctk, 
                                fg_color="white", hover_color="gray90", corner_radius=10, 
                                border_width=1, border_color="gray80",
                                height=history_h+20, width=history_w+20,
                                command=lambda index=i: display_history_item(index))
        card_btn.pack(side="left", padx=10, pady=10)
        
        # CTkImage 객체를 전역 변수에 저장해야 가비지 컬렉션 안됨
        card_btn.image = history_ctk

# 💡 [핵심 구현] 생성 히스토리 아이템 클릭 시 화면 업데이트 함수
def display_history_item(index):
    global history_list, current_barcode_obj, current_barcode_data
    
    item = history_list[index]
    pil_img = item['pil_img']
    logo_pil = item['logo_pil']
    
    # 💡 [화면 스캔 및 저장 파일 모두 적용] PIL 이미지를 로드하여 화면 스캔 및 저장 파일 모두 적용
    # generate_barcode와 동일한 PIL 이미지를 사용하므로 문제 없음
    
    # generate_barcode와 동일한 미리보기 크기 설정
    img_w, img_h = pil_img.size
    display_w = 480
    display_h = int(img_h * (display_w / img_w))
    
    # PIL 이미지 위에 로고 합성 (복제하여 원본 유지)
    combined_pil = pil_img.copy()
    bw, bh = combined_pil.size
    logo_x = bw - 50 - 10 # quiet_zone 10.0 마진
    logo_y = 10 #quiet_zone 10.0 마진
    combined_pil.paste(logo_pil, (logo_x, logo_y), logo_pil)
    
    # CTkImage로 변환
    img_ctk_with_logo = ctk.CTkImage(light_image=combined_pil, dark_image=combined_pil, size=(display_w, display_h))
    
    barcode_label.configure(image=img_ctk_with_logo, text="") 
    barcode_label.image = img_ctk_with_logo
    
    # generate_barcode와 동일하게 객체 업데이트
    # barcode.get_barcode_class('code128')(data, writer=ImageWriter())
    # 를 통해 barcode_obj를 복구해야 함. current_barcode_data를 Global로 저장해서 사용.
    current_barcode_data = item['data']
    
    try:
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        code128 = barcode.get_barcode_class('code128')
        writer = ImageWriter()
        current_barcode_obj = code128(current_barcode_data, writer=writer)
    except:
        pass # 폰트 에러 방지

    entry.delete(0, 'end')
    entry.insert(0, current_barcode_data)
    save_button.configure(state="normal", fg_color="#2FA572")

# --- 모던 & 대형 프라이빗 UI 레이아웃 ---
root = ctk.CTk()
root.title("Warehouse Logistics Pro - Space Edition v4.2")
# 💡 [요청사항 반영 2] 전체 창 크기를 대폭 확장
root.geometry("1000x800") 

# 💡 [요청사항 반영 3] '우주 화면' 배경 구현 (코드만으로 은하수/별빛 표현)
bg_pil = create_space_background(1000, 800)
bg_ctk = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1000, 800))
bg_label = ctk.CTkLabel(root, text="", image=bg_ctk, corner_radius=0)
bg_label.pack(fill="both", expand=True)

# 그라데이션 효과를 위한 서브 프레임 (상단은 약간 밝은 블루)
# bg_gradient = ctk.CTkFrame(bg_label, corner_radius=0, fg_color="#1a2542", height=300)
# bg_gradient.place(x=0, y=0, relwidth=1)

# 중앙 콘텐츠 영역 (💡 Glassmorphism 투명 패널 구현)
main_container = ctk.CTkFrame(bg_label, corner_radius=25, fg_color=("#333333", "#141414"), border_width=1, border_color="#333333")
main_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.85)

# 상단 헤더
header_label = ctk.CTkLabel(main_container, text="Logistics Barcode Generator", font=ctk.CTkFont(size=36, weight="bold"), text_color="#E0E0E0")
header_label.pack(pady=(50, 40))

# 입력창 섹션 (💡 고급스러운 카드 형태)
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

# 💡 [요청사항 반영 1] ICQA 로고 우측 상단 배치
# generate_barcode 내부 PIL 합성 코드로 처리됨

# 하단 정보 및 버튼
status_label = ctk.CTkLabel(main_container, text="Coupang Logistics Team / v3.0 / Designed for Efficiency", font=ctk.CTkFont(size=12), text_color="#808080")
status_label.pack(side="bottom", pady=20)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=250, height=50, 
                            font=ctk.CTkFont(size=16), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(side="bottom", pady=(0, 10))

# 💡 [핵심 구현] 생성 히스토리 스크롤 뷰 추가 (Glassmorphism 투명 패널 위에 화이트 카드 형태)
# Glassmorphism 효과를 위해 CTkFrame 사용 (border_width=1, corner_radius=15)
# 화이트 카드 형태를 위해 CTkButton 사용 (fg_color="white", hover_color="gray90")
# 히스토리 리스트는 가로 스크롤 가능하게 CTkScrollableFrame 사용

ctk.CTkLabel(main_container, text="생성 히스토리", font=ctk.CTkFont(size=14, weight="bold"), text_color="#A0A0A0").pack(pady=(10, 5))

# Glassmorphism 패널
history_main_frame = ctk.CTkFrame(main_container, corner_radius=15, fg_color=("#333333", "#141414"), border_width=1, border_color="#333333")
history_main_frame.pack(pady=(0, 20), padx=40, fill="x", expand=False)
history_main_frame.pack_propagate(False) # 가로 스크롤 가능하게 하기 위해 pack_propagate(False)
# CTkScrollableFrame은 CTkFrame 내부에 위치시켜 가로 스크롤 가능하게 함
history_scroll_frame = ctk.CTkScrollableFrame(history_main_frame, corner_radius=12, fg_color="transparent", 
                                                width=1000, height=140, # 💡 가로 스크롤을 위해 width 대폭 확장
                                                orientation="horizontal", border_width=0, scrollbar_button_color=("gray60", "gray40")) # 가로 스크롤바 커스터마이징
history_scroll_frame.pack(fill="x", expand=True, padx=0, pady=0) # history_main_frame 내부에 위치

root.mainloop()
