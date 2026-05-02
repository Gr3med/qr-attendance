import flet as ft
import qrcode
import base64
from io import BytesIO

# ==========================================
# منطقة المنطق البرمجي (Logic) - [لم يتم المساس بها]
# ==========================================

def generate_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def process_attendance(scanned_data: str) -> bool:
    if scanned_data:
        return True
    return False

# ==========================================
# منطقة تصميم الواجهة (Mobile UI/UX)
# ==========================================

def main(page: ft.Page):
    page.title = "QR Attendance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a" 
    page.padding = 0 # تم التصفير لاستخدام SafeArea
    page.theme = ft.Theme(font_family="Segoe UI")

    def create_glass_card(content_widget):
        return ft.Container(
            content=content_widget,
            bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE),
            border_radius=15,
            padding=20,
            border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.WHITE)),
            blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
            alignment=ft.alignment.center,
        )

    # ----------------------------------------
    # تبويب: توليد رمز QR
    # ----------------------------------------
    user_id_input = ft.TextField(
        label="رقم المعرف",
        border_color=ft.colors.BLUE_400,
        width=250,
        text_align=ft.TextAlign.CENTER
    )
    
    qr_image = ft.Image(src=None, width=200, height=200, visible=False)
    
    def on_generate_click(e):
        if not user_id_input.value:
            user_id_input.error_text = "مطلوب"
            page.update()
            return
        
        user_id_input.error_text = None
        img_b64 = generate_qr_base64(user_id_input.value)
        qr_image.src_base64 = img_b64
        qr_image.visible = True
        page.update()

    btn_generate = ft.ElevatedButton(
        "إنشاء الرمز", 
        on_click=on_generate_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=ft.colors.BLUE_700,
            color=ft.colors.WHITE
        )
    )

    tab_generate_content = ft.Column(
        controls=[
            ft.Text("إصدار بطاقات QR", size=18, weight=ft.FontWeight.BOLD),
            user_id_input,
            btn_generate,
            qr_image
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
    )

    # ----------------------------------------
    # تبويب: تسجيل الحضور
    # ----------------------------------------
    scanner_input = ft.TextField(
        label="انتظار الفحص...",
        border_color=ft.colors.TEAL_400,
        width=250,
        text_align=ft.TextAlign.CENTER,
    )
    
    status_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

    def on_scan_submit(e):
        scanned_val = scanner_input.value.strip()
        if not scanned_val:
            return
        
        success = process_attendance(scanned_val)
        
        if success:
            status_text.value = f"تم التسجيل: {scanned_val}"
            status_text.color = ft.colors.GREEN_400
        else:
            status_text.value = "فشل التسجيل!"
            status_text.color = ft.colors.RED_400
            
        scanner_input.value = ""
        scanner_input.focus()
        page.update()

    scanner_input.on_submit = on_scan_submit

    tab_scan_content = ft.Column(
        controls=[
            ft.Text("تسجيل الحضور", size=18, weight=ft.FontWeight.BOLD),
            scanner_input,
            status_text
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
    )

    # ----------------------------------------
    # تجميع الواجهة في SafeArea للهواتف
    # ----------------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="إنشاء",
                icon=ft.icons.QR_CODE_2,
                content=ft.Container(content=create_glass_card(tab_generate_content), padding=15)
            ),
            ft.Tab(
                text="فحص",
                icon=ft.icons.CAMERA_ALT,
                content=ft.Container(content=create_glass_card(tab_scan_content), padding=15)
            ),
        ],
        expand=1,
    )

    # استخدام SafeArea لمنع تداخل الواجهة مع حواف الهاتف
    page.add(ft.SafeArea(tabs, expand=True))

if __name__ == "__main__":
    ft.app(target=main)
