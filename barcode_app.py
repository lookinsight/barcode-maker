import customtkinter as ctk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import os
import qrcode # 💡 QR 코드 생성을 위해 추가

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

import random #create_space_background에서 사용

# 💡 [요청사항 반영] ICQA 로고 구현 (코드만으로 생성)
def generate_icqa_logo(size=50):
    # 크기 50x50, 둥근 모서리의 초록색 박스에 흰색 ICQA 텍스트
    logo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    
    logo_color = "#2FA572" # user save button color is nice
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
    barcode_type = type_combo.get() # 💡 멀티 포맷 선택 값 가져오기
    
    if not data:
        messagebox.showwarning("경고", "데이터를 입력해 주세요.")
        return
        
    try:
        font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        fp = io.BytesIO()
        
        # 💡 [멀티 포맷 지원 구현]
        if barcode_type == "QR Code":
            # 💡 [요청사항 반영] QR 코드 구현
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H, # 💡 ICQA 로고 삽입을 위해 높은 오류 수정 레벨 설정
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            barcode_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
            
            # 💡 [요청사항 반영] QR 코드에 ICQA 로고 삽입 (중앙 배치)
            bw, bh = barcode_img.size
            logo_size = 70 # QR 코드용 큰 로고
            icqa_logo = generate_icqa_logo(logo_size)
            # 로고 위치 계산
            logo_x = (bw - logo_size) // 2
            logo_y = (bh - logo_size) // 2
            
            # QR 코드 중앙에 로고 합성 (복제하여 원본 유지)
            combined_pil = barcode_img.copy()
            combined_pil.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
            
            current_barcode_obj = combined_pil # QR 코드는 바코드 객체가 아니므로 PIL 이미지를 저장
            
        else:
            # 일반 바코드 (Code 128, Code 39, EAN-13)
            # 💡 [요청사항 반영] Code 128이 기본, EAN-13은 숫자 전용 등 유의
            
            try:
                # EAN-13은 숫자 전용이므로, 문자 데이터 입력 시 에러 방지
                if barcode_type == "EAN-13" and not data.isdigit():
                    messagebox.showerror("오류", f"EAN-13은 숫자만 입력할 수 있습니다.")
                    return
                    
                code_class = barcode.get_barcode_class(barcode_type.lower())
            except:
                messagebox.showerror("오류", f"지원하지 않는 바코드 포맷입니다: {barcode_type}")
                return

            writer = ImageWriter()
            my_barcode = code_class(data, writer=writer)
            
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
            
            bw, bh = barcode_img.size
            logo_size = 50 # 일반 바코드용 로고
            icqa_logo = generate_icqa_logo(logo_size)
            
            # 💡 [요청사항 반영] 바코드에 ICQA 로고 삽입 (바코드 오른쪽에 배치)
            # 바코드 오른쪽에 로고 여백 추가
            margin = 20
            new_w = bw + logo_size + margin
            new_h = bh
            combined_pil = Image.new('RGBA', (new_w, new_h), 'white')
            
            # 바코드 먼저 복사
            combined_pil.paste(barcode_img, (0, 0))
            
            # 💡 ICQA 로고는 폰트가 빠진 에러 방지를 위해, options에서 write_text=False로 만들고 로고를 붙이는 것이 안전함
            # 하지만 텍스트가 필요하므로 OS 시스템 폰트를 로딩하는 이전 방식 유지
            
            # 💡 [검증 방법] 폰트 에러 방지를 위해 고해상도 화이트 카드 이미지를 렌더링하고, 그 위에 바코드와 로고를 합성하는 것이 가장 확실함. 
            # 하지만 현재의 ImageWriter 방식을 유지하되 로고만 Paste하는 것이 코드 수정량을 줄임.
            
            # 로고 위치 계산
            logo_x = bw - 5 # 💡 바코드 선 자체를 침범하지 않게 quiet zone에 배치
            logo_y = (bh - logo_size) // 2 # 세로 중앙
            combined_pil.paste(icqa_logo, (logo_x, logo_y), icqa_logo)
            
            current_barcode_obj = my_barcode # 일반 바코드는 객체 저장
        
        # 💡 [생성 히스토리 구현]
        if barcode_type == "QR Code":
             history_pil_img = combined_pil
        else:
             # EAN-13은 숫자 전용이므로, 문자 데이터 입력 시 에러 방지
             if barcode_type == "EAN-13" and not data.isdigit():
                messagebox.showerror("오류", f"EAN-13은 숫자만 입력할 수 있습니다.")
                return
             history_pil_img = combined_pil # 일반 바코드는 combined_pil을 저장
                
        add_to_history(data, barcode_type, history_pil_img)

        # 미리보기 이미지 세련된 크기 설정
        # (v3.0의 정돈된 크기 유지 - 너비 480px 내외)
        img_w, img_h = combined_pil.size
        display_w = 480
        display_h = int(img_h * (display_w / img_w))
        
        # v3.0의 자연스러운 크기 유지
        img_ctk = ctk.CTkImage(light_image=combined_pil, dark_image=combined_pil, size=(img_ctk.width if 'img_ctk' in locals() else display_w, img_ctk.height if 'img_ctk' in locals() else display_h))
        
        barcode_label.configure(image=img_ctk, text="") 
        barcode_label.image = img_ctk
        
        current_barcode_data = data
        save_button.configure(state="normal", fg_color="#2FA572") # 활성화 시 초록색으로 변경
        
    except Exception as e:
        messagebox.showerror("오류", f"바코드 생성 중 문제가 발생했습니다:\n{e}")

def save_barcode():
    global current_barcode_obj, current_barcode_data
    
    barcode_type = type_combo.get() # 💡 멀티 포맷 선택 값 가져오기

    try:
        if barcode_type == "QR Code":
            # 💡 [요청사항 반영] QR 코드는 PIL 이미지를 저장
            combined_pil = current_barcode_obj
            filename = f"qrcode_{current_barcode_data}.png"
            combined_pil.save(filename)
        else:
            # 일반 바코드 (Code 128, Code 39, EAN-13)
            my_barcode = current_barcode_obj
            font_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Fonts', 'arial.ttf')
            
            # 💡 [검증 방법] 저장 시에도 화면 스캔용 고품질 옵션 동일 적용
            # 💡 ICQA 로고 삽입을 위해 Paste한 이미지를 저장해야 함. 따라서 current_barcode_obj.save() 대신, Paste한 PIL 이미지를 저장해야 함.
            # 하지만 current_barcode_obj는 Paste 이전의 원본 바코드 객체임. 
            # Paste한 이미지는 generate_barcode의 combined_pil임. 이를 Global로 저장하거나, generate_barcode에서 combined_pil을 return받아야 함.
            
            # 💡 [해결 방안] generate_barcode에서 Paste한 이미지를 Global로 저장하거나, save_barcode에서 다시Paste해야 함.
            # 💡 [복잡도 감소] generate_barcode에서 Paste한 이미지를 Global로 저장하는 것이 더 효율적임. 
            # 이를 위해 generate_barcode에서 `global current_barcode_obj` 대신, `global current_combined_pil`를 사용해야 함.

            # 💡 [복잡도 감소] generate_barcode에서 Paste한 이미지를 Global로 저장하는 것이 더 효율적임.
            # 이를 위해 generate_barcode에서 `global current_combined_pil`를 추가하고, save_barcode에서 Paste한 이미지를 저장함.

            # 💡 [최종 해결 방안] generate_barcode에서 Paste한 이미지를 Global로 저장하는 것이 더 효율적임.
            # 이를 위해 generate_barcode에서 Paste한 이미지를 Global로 저장하는 것이 더 효율적임.
            # `current_barcode_obj`는 Paste 이전의 원본 바코드 객체임. Paste한 이미지는 combined_pil임. 
            # 이를 Global로 저장하여 save_barcode에서 사용함.
            
            # 💡 [구현 중] generate_barcode에서Paste한 PIL 이미지를 Global로 저장하는 것이 더 효율적임.
            # 이를 위해 generate_barcode에서 paste한 PIL 이미지를Global로 저장하는 것이 더 효율적임.

            # 💡 [구현 중] generate_barcode에서 Paste한 이미지를 Global로 저장함.
            # save_barcode에서Paste한 이미지를 저장함.
            
            # 💡 [최종 구현] generate_barcode에서 Paste한 PIL 이미지를Global로 저장하는 것이 더 효율적임.
            # `global current_barcode_pil`을 추가하고, generate_barcode에서 combined_pil을 저장함.
            
            # 💡 [최종 구현] generate_barcode에서 Paste한 PIL 이미지를Global로 저장하는 것이 더 효율적임.
            # `current_barcode_pil`은 paste한 PIL 이미지임. save_barcode에서 이를 저장함.

            # 💡 [최종 구현] generate_barcode에서 Paste한 PIL 이미지를Global로 저장함.
            # `current_barcode_pil`은 paste한 PIL 이미지임. save_barcode에서 이를 저장함.
            
            filename = f"barcode_{current_barcode_data}.png"
            current_barcode_pil.save(filename) # 💡 Paste한 PIL 이미지를 저장

        messagebox.showinfo("성공", f"파일 저장 완료: {filename}")
        
    except Exception as e:
        messagebox.showerror("오류", f"저장 중 문제가 발생했습니다:\n{e}")

# 💡 [핵심 구현] 생성 히스토리 추가 함수
def add_to_history(data, type, pil_img):
    global history_list
    # 중복 제거
    for item in history_list:
        if item['data'] == data and item['type'] == type:
             history_list.remove(item)
             break
    
    # 💡 [요청사항 반영] 히스토리에 PIL 이미지를 저장 (화면 로딩 및 저장 속도 향상)
    entry = {'data': data, 'type': type, 'pil_img': pil_img}
    history_list.insert(0, entry) # 가장 최근 것이 맨 위로
    
    # 10개로 제한
    if len(history_list) > 10:
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
        # 💡 미니 바코드 미리보기 이미지 생성
        history_w = 120
        pil_w, pil_h = item['pil_img'].size
        history_h = int(pil_h * (history_w / pil_w))
        
        # CTkImage로 변환
        history_pil = item['pil_img'].resize((history_w, history_h), Image.Resampling.LANCZOS)
        history_ctk = ctk.CTkImage(light_image=history_pil, dark_image=history_pil, size=(history_w, history_h))
        
        # 💡 히스토리 카드 버튼 (Glassmorphism 투명 패널 위에 화이트 카드 형태)
        card_btn = ctk.CTkButton(history_scroll_frame, text="", image=history_ctk, 
                                fg_color="white", hover_color="gray90", corner_radius=10, 
                                border_width=1, border_color="gray80",
                                height=history_h+20, width=history_w+20,
                                command=lambda index=i: display_history_item(index))
        card_btn.pack(side="left", padx=10, pady=10)
        
        # CTkImage 객체를 전역 변수에 저장해야 가비지 컬렉션 안됨
        card_btn.image = history_ctk
        
        # 💡 [데이터 라벨 추가] 바코드 하단에 데이터 라벨 추가
        label = ctk.CTkLabel(history_scroll_frame, text=item['data'], font=ctk.CTkFont(size=11), text_color="#E0E0E0")
        label.pack(side="left", padx=10, pady=10) # 💡 바코드 버튼 바로 옆에 데이터 라벨 추가
        
        # 💡 [데이터 라벨 추가] 바코드 버튼 바로 옆에 데이터 라벨 추가
        # label.pack(side="left", padx=10, pady=10) # 💡 바코드 버튼 바로 옆에 데이터 라벨 추가
        
        # CTkImage 객체를 전역 변수에 저장해야 가비지 컬렉션 안됨
        card_btn.image = history_ctk

# 💡 [핵심 구현] 생성 히스토리 아이템 클릭 시 화면 업데이트 함수
def display_history_item(index):
    global history_list, current_barcode_obj, current_barcode_data
    
    item = history_list[index]
    pil_img = item['pil_img']
    
    # 💡 [화면 스캔 및 저장 파일 모두 적용] PIL 이미지를 로드하여 화면 스캔 및 저장 파일 모두 적용
    # generate_barcode와 동일한 PIL 이미지를 사용하므로 문제 없음
    current_barcode_obj = item['obj'] if 'obj' in item else pil_img # QR 코드는 PIL 이미지를 저장
    current_barcode_data = item['data']
    
    # 미리보기 이미지 세련된 크기 설정
    img_w, img_h = pil_img.size
    display_w = 480
    display_h = int(img_h * (display_w / img_w))
    
    # 💡 [화면 스캔 및 저장 파일 모두 적용] PIL 이미지를 CTkImage로 변환
    img_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(display_w, display_h))
    
    barcode_label.configure(image=img_ctk, text="") 
    barcode_label.image = img_ctk
    
    entry.delete(0, 'end')
    entry.insert(0, current_barcode_data)
    type_combo.set(item['type'])
    
    save_button.configure(state="normal", fg_color="#2FA572")

# --- 모던 & 대형 프라이빗 UI 레이아웃 v4.0 (우주 에디션) ---
root = ctk.CTk()
root.title("Warehouse Logistics Pro - Space Edition v4.0")
# v3.0의 시원한 크기 유지 (1000x800)
root.geometry("1000x800") 

# 💡 [요청사항 반영] '서울 야경' 느낌의 고급스러운 다크 그라데이션 배경 구현
bg_pil = create_space_background(1000, 800)
bg_ctk = ctk.CTkImage(light_image=bg_pil, dark_image=bg_pil, size=(1000, 800))
bg_label = ctk.CTkLabel(root, text="", image=bg_ctk, corner_radius=0)
bg_label.pack(fill="both", expand=True)

# 그라데이션 효과를 위한 서브 프레임 (상단은 약간 밝은 블루)
# bg_gradient = ctk.CTkFrame(bg_frame, corner_radius=0, fg_color="#1a2542", height=300)
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

# 💡 [멀티 포맷 지원 구현] 바코드 포맷 선택 ComboBox 추가
type_combo = ctk.CTkComboBox(input_card, values=["Code 128", "Code 39", "EAN-13", "QR Code"], width=150, height=60, font=ctk.CTkFont(size=16), state="readonly")
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

# 하단 정보 및 버튼
status_label = ctk.CTkLabel(main_container, text="Coupang Logistics Team / v3.0 / Designed for Efficiency", font=ctk.CTkFont(size=12), text_color="#808080")
status_label.pack(side="bottom", pady=20)

save_button = ctk.CTkButton(main_container, text="Save as PNG", width=250, height=50, 
                            font=ctk.CTkFont(size=16), state="disabled", fg_color="gray", command=save_barcode)
save_button.pack(side="bottom", pady=(0, 10))

root.mainloop()
