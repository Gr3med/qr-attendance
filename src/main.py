import flet as ft
import qrcode
import base64
import csv
from io import BytesIO
from datetime import datetime
from PIL import Image
from pyzbar.pyzbar import decode

# ==========================================
# منطقة قواعد البيانات والمنطق البرمجي
# ==========================================

db_students = {}      
db_attendance = []    

def generate_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# ==========================================
# منطقة واجهة المستخدم (Mobile UI/UX)
# ==========================================

def main(page: ft.Page):
    page.title = "نظام الحضور الذكي"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f172a"
    page.padding = 0
    page.theme = ft.Theme(font_family="Segoe UI")

    # نظام الإشعارات المستقر 100%
    def show_snack_bar(msg, color):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=color
        )
        page.snack_bar.open = True
        page.update()

    def create_glass_card(content_widget):
        return ft.Container(
            content=content_widget,
            bgcolor=ft.Colors.WHITE10,
            border_radius=15,
            padding=20,
            border=ft.Border.all(1, ft.Colors.WHITE24),
            blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
            alignment=ft.Alignment(0, 0),
        )

    # ----------------------------------------
    # 1. واجهة التحضير (فتح الكاميرا والمسح)
    # ----------------------------------------
    scan_result_text = ft.Text("اضغط على الزر أدناه لفتح الكاميرا ومسح البطاقة", size=14, text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE54)

    def process_scanned_id(student_id):
        student_id = student_id.strip()
        if not db_students:
            scan_result_text.value = "يرجى تحديد مسار ملف الطلاب من الإدارة أولاً!"
            scan_result_text.color = ft.Colors.AMBER_400
        elif student_id in db_students:
            student_name = db_students[student_id]
            time_now = datetime.now().strftime("%I:%M %p")
            
            if any(record['id'] == student_id for record in db_attendance):
                scan_result_text.value = f"الطالب {student_name} مُحضر مسبقاً!"
                scan_result_text.color = ft.Colors.AMBER_400
            else:
                db_attendance.append({"id": student_id, "name": student_name, "time": time_now})
                scan_result_text.value = f"تم تحضير: {student_name}\n({time_now})"
                scan_result_text.color = ft.Colors.GREEN_400
                refresh_attendance_list()
        else:
            scan_result_text.value = f"رقم القيد ({student_id}) غير مسجل بالنظام!"
            scan_result_text.color = ft.Colors.RED_400
        page.update()

    # دالة قراءة الـ QR عبر pyzbar
    def on_qr_image_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            img_path = e.files[0].path
            try:
                img = Image.open(img_path)
                decoded_objects = decode(img)
                if decoded_objects:
                    qr_data = decoded_objects[0].data.decode('utf-8')
                    process_scanned_id(qr_data)
                else:
                    show_snack_bar("لم يتم التعرف على الـ QR، حاول التقاط صورة أوضح.", ft.Colors.RED_400)
            except Exception as ex:
                show_snack_bar("خطأ في معالجة الصورة.", ft.Colors.RED_400)

    # أداة اختيار الملفات/الكاميرا
    qr_picker = ft.FilePicker(on_result=on_qr_image_picked)
    page.overlay.append(qr_picker)
    page.update()

    btn_scan = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.CAMERA_ALT, size=24, color=ft.Colors.WHITE), ft.Text("التقاط صورة للبطاقة (Scan)", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.TEAL_600,
        padding=15,
        border_radius=10,
        on_click=lambda _: qr_picker.pick_files(allowed_extensions=["png", "jpg", "jpeg"]),
        ink=True
    )

    view_scan = ft.Container(
        content=create_glass_card(
            ft.Column(
                controls=[
                    ft.Icon(ft.Icons.QR_CODE_SCANNER, size=60, color=ft.Colors.TEAL_400),
                    ft.Text("نظام التحضير بالكاميرا", size=22, weight=ft.FontWeight.BOLD),
                    ft.Divider(color=ft.Colors.TRANSPARENT),
                    btn_scan,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    scan_result_text
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ),
        padding=20, alignment=ft.Alignment(0, -0.5)
    )

    # ----------------------------------------
    # 2. واجهة سجل الحضور (Dashboard)
    # ----------------------------------------
    attendance_list_view = ft.ListView(expand=True, spacing=10, padding=10)

    def refresh_attendance_list():
        attendance_list_view.controls.clear()
        if not db_attendance:
            attendance_list_view.controls.append(
                ft.Text("لا يوجد حضور حتى الآن.", text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE54)
            )
        for record in reversed(db_attendance): 
            attendance_list_view.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400),
                        title=ft.Text(record['name'], weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"رقم القيد: {record['id']} | الوقت: {record['time']}"),
                    ),
                    bgcolor=ft.Colors.WHITE10,
                    border_radius=10,
                )
            )
        page.update()

    view_dashboard = ft.Container(
        content=ft.Column([
            ft.Text("سجل الحضور اليومي", size=22, weight=ft.FontWeight.BOLD),
            attendance_list_view
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20
    )

    # ----------------------------------------
    # 3. واجهة الإدارة 
    # ----------------------------------------
    stats_text = ft.Text("الطلاب المسجلين: 0", color=ft.Colors.WHITE70)

    def update_admin_stats():
        stats_text.value = f"الطلاب المسجلين: {len(db_students)}"
        page.update()

    def load_csv_data(file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                db_students.clear()
                next(reader, None) 
                for row in reader:
                    if len(row) >= 2:
                        student_id, student_name = row[0].strip(), row[1].strip()
                        db_students[student_id] = student_name
            
            show_snack_bar(f"تم تحميل {len(db_students)} طالب بنجاح!", ft.Colors.GREEN_400)
            update_admin_stats()
            
        except FileNotFoundError:
            show_snack_bar("الملف غير موجود في هذا المسار!", ft.Colors.RED_400)
        except PermissionError:
            show_snack_bar("النظام يرفض الصلاحية للوصول لهذا المسار!", ft.Colors.RED_400)
        except Exception as ex:
            show_snack_bar(f"خطأ في قراءة الملف: تأكد من صيغة CSV", ft.Colors.RED_400)

    path_input = ft.TextField(
        label="مسار ملف الطلاب",
        hint_text="ألصق مسار الـ CSV هنا...",
        border_color=ft.Colors.PURPLE_400,
        width=250,
        text_align=ft.TextAlign.LEFT
    )

    btn_sync = ft.IconButton(
        icon=ft.Icons.SYNC,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_700,
        tooltip="قراءة المسار المكتوب",
        on_click=lambda _: load_csv_data(path_input.value.strip()) if path_input.value else show_snack_bar("أدخل المسار أولاً", ft.Colors.RED_400)
    )

    row_file_selector = ft.Row(
        controls=[path_input, btn_sync],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10
    )

    gen_id_input = ft.TextField(label="رقم القيد", width=250, border_color=ft.Colors.BLUE_400)
    qr_image = ft.Image(src="", width=150, height=150, visible=False)

    def on_generate_click(e):
        if gen_id_input.value:
            qr_image.src_base64 = generate_qr_base64(gen_id_input.value.strip())
            qr_image.visible = True
            page.update()

    btn_generate = ft.Container(
        content=ft.Text("توليد بطاقة QR", weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_700, padding=10, border_radius=8, width=150, alignment=ft.Alignment(0, 0),
        on_click=on_generate_click, ink=True
    )

    view_admin = ft.Container(
        content=ft.ListView(
            controls=[
                create_glass_card(
                    ft.Column([
                        ft.Text("إدارة قاعدة البيانات", size=18, weight=ft.FontWeight.BOLD),
                        row_file_selector,
                        stats_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(height=20),
                create_glass_card(
                    ft.Column([
                        ft.Text("إصدار بطاقات QR", size=18, weight=ft.FontWeight.BOLD),
                        gen_id_input,
                        btn_generate,
                        qr_image
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
            ]
        ),
        padding=20
    )

    # ----------------------------------------
    # شريط التنقل السفلي 
    # ----------------------------------------
    views = [view_scan, view_dashboard, view_admin]
    main_content = ft.Container(content=views[0], expand=True)

    def on_nav_change(e):
        main_content.content = views[e.control.selected_index]
        if e.control.selected_index == 1:
            refresh_attendance_list() 
        page.update()

    page.navigation_bar = ft.NavigationBar(
        bgcolor=ft.Colors.WHITE10,
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.QR_CODE_SCANNER, label="تحضير"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="السجل"),
            ft.NavigationBarDestination(icon=ft.Icons.ADMIN_PANEL_SETTINGS, label="الإدارة"),
        ]
    )

    page.add(ft.SafeArea(main_content, expand=True))

if __name__ == "__main__":
    ft.run(main)
