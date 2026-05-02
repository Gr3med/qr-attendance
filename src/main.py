import time
import sqlite3
from datetime import datetime

import cv2
import numpy as np
import flet as ft
import flet_camera as fc

DB = "attendance.db"
ADMIN_PASSWORD = "123456"  # غيّرها كما تريد

qr_detector = cv2.QRCodeDetector()


# -------------------- DATABASE --------------------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            reg_no TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            UNIQUE(reg_no, date)
        )
    """)

    conn.commit()
    conn.close()


def add_student(reg_no: str, name: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO students (reg_no, name) VALUES (?, ?)",
        (reg_no, name),
    )
    conn.commit()
    conn.close()


def get_students():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT reg_no, name FROM students ORDER BY reg_no")
    rows = cur.fetchall()
    conn.close()
    return rows


def count_students():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students")
    n = cur.fetchone()[0]
    conn.close()
    return n


def get_student_name(reg_no: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM students WHERE reg_no = ?", (reg_no,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def marked_today(reg_no: str):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM attendance WHERE reg_no = ? AND date = ? LIMIT 1",
        (reg_no, today),
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def mark_attendance(reg_no: str):
    now = datetime.now()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO attendance (reg_no, date, time) VALUES (?, ?, ?)",
        (reg_no, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_today_attendance():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT a.time, s.reg_no, s.name
        FROM attendance a
        JOIN students s ON s.reg_no = a.reg_no
        WHERE a.date = ?
        ORDER BY a.time DESC
    """, (today,))
    rows = cur.fetchall()
    conn.close()
    return rows


def count_today_attendance():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
    n = cur.fetchone()[0]
    conn.close()
    return n


# -------------------- APP --------------------
async def main(page: ft.Page):
    page.title = "نظام حضور الطلاب عبر QR"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.theme = ft.Theme(use_material3=True, color_scheme_seed=ft.Colors.INDIGO)

    def notify(text: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(text))
        page.snack_bar.open = True
        page.update()

    state = {
        "is_admin": False,
        "camera_ready": False,
        "last_qr": "",
        "last_qr_ts": 0.0,
    }

    students_list = ft.Column(spacing=10)
    today_list = ft.Column(spacing=10)

    total_students_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)
    total_today_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)
    scan_result = ft.Text("وجّه الكاميرا نحو QR", size=16, weight=ft.FontWeight.BOLD)

    reg_input = ft.TextField(label="رقم القيد", hint_text="مثال: 246066", border_radius=14, width=320)
    name_input = ft.TextField(label="اسم الطالب", hint_text="اسم الطالب كاملًا", border_radius=14, width=320)
    password_input = ft.TextField(label="كلمة مرور الأدمن", password=True, can_reveal_password=True, border_radius=14, width=320)

    camera_preview = fc.Camera(
        expand=True,
        preview_enabled=True,
        content=ft.Container(
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, color=ft.Colors.WHITE70, size=54),
        ),
    )

    async def refresh_students():
        students_list.controls.clear()
        rows = get_students()

        if not rows:
            students_list.controls.append(
                ft.Container(
                    padding=16,
                    border_radius=16,
                    bgcolor=ft.Colors.GREY_100,
                    content=ft.Text("لا يوجد طلاب بعد."),
                )
            )
        else:
            for reg_no, name in rows:
                students_list.controls.append(
                    ft.Container(
                        padding=16,
                        border_radius=16,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(reg_no, size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text("رقم القيد", size=12, color=ft.Colors.GREY_600),
                                    ],
                                    spacing=2,
                                ),
                                ft.Text(name, size=16),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )

        total_students_text.value = str(count_students())
        page.update()

    async def refresh_today():
        today_list.controls.clear()
        rows = get_today_attendance()

        if not rows:
            today_list.controls.append(
                ft.Container(
                    padding=16,
                    border_radius=16,
                    bgcolor=ft.Colors.GREY_100,
                    content=ft.Text("لا يوجد حضور مسجل اليوم."),
                )
            )
        else:
            for time_str, reg_no, name in rows:
                today_list.controls.append(
                    ft.Container(
                        padding=16,
                        border_radius=16,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                        content=ft.Row(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN),
                                        ft.Text(name, weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=8,
                                ),
                                ft.Text(f"{reg_no}  •  {time_str}", color=ft.Colors.GREY_700),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )

        total_today_text.value = str(count_today_attendance())
        page.update()

    def build_header():
        return ft.Container(
            padding=20,
            bgcolor=ft.Colors.INDIGO,
            content=ft.Column(
                [
                    ft.Text("نظام حضور الطلاب عبر QR", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("مسح مباشر بالكاميرا، وتسجيل الحضور فورًا", size=14, color=ft.Colors.WHITE),
                    ft.Row(
                        [
                            ft.OutlinedButton("الحضور", on_click=lambda e: page.run_task(show_attendance)),
                            ft.OutlinedButton("الإدارة", on_click=lambda e: page.run_task(show_admin_gate)),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=8,
            ),
        )

    def stats_row():
        return ft.Row(
            [
                ft.Container(
                    expand=1,
                    padding=16,
                    border_radius=18,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                    content=ft.Column(
                        [ft.Text("عدد الطلاب"), total_students_text],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(
                    expand=1,
                    padding=16,
                    border_radius=18,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
                    content=ft.Column(
                        [ft.Text("حضور اليوم"), total_today_text],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            spacing=12,
        )

    def card(title, content):
        return ft.Container(
            padding=16,
            border_radius=18,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
            content=ft.Column([ft.Text(title, size=18, weight=ft.FontWeight.BOLD), content], spacing=12),
        )

    async def init_camera_and_stream():
        try:
            cameras = await camera_preview.get_available_cameras()
            if not cameras:
                notify("لا توجد كاميرا متاحة")
                return

            selected = next(
                (c for c in cameras if getattr(c, "lens_direction", None) == fc.CameraLensDirection.BACK),
                cameras[0],
            )

            await camera_preview.initialize(selected)

            if await camera_preview.supports_image_streaming():
                await camera_preview.start_image_stream()
                state["camera_ready"] = True
                scan_result.value = "الكاميرا جاهزة للمسح"
                page.update()
            else:
                notify("هذا الجهاز لا يدعم بث الصور المباشر")
        except Exception as ex:
            notify(f"خطأ في الكاميرا: {ex}")

    async def stop_camera():
        if state["camera_ready"]:
            try:
                await camera_preview.stop_image_stream()
            except Exception:
                pass
            state["camera_ready"] = False

    async def show_attendance():
        await stop_camera()
        page.controls.clear()

        attendance_layout = ft.SafeArea(
            content=ft.Column(
                [
                    build_header(),
                    ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                stats_row(),
                                card(
                                    "المسح المباشر",
                                    ft.Container(
                                        height=360,
                                        border_radius=24,
                                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                                        bgcolor=ft.Colors.BLACK,
                                        content=camera_preview,
                                    ),
                                ),
                                card(
                                    "النتيجة",
                                    ft.Column(
                                        [
                                            scan_result,
                                            ft.Text("صيغة QR: REG-246066", size=12, color=ft.Colors.GREY_600),
                                            ft.ElevatedButton(
                                                "دخول الأدمن",
                                                icon=ft.Icons.LOCK,
                                                on_click=lambda e: page.run_task(show_admin_gate),
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                ),
                                card("آخر الحضور اليوم", today_list),
                            ],
                            spacing=16,
                        ),
                    ),
                ],
                spacing=0,
            )
        )

        page.add(attendance_layout)
        page.update()
        await refresh_today()
        await init_camera_and_stream()

    async def show_admin_login():
        await stop_camera()
        page.controls.clear()

        login_layout = ft.SafeArea(
            content=ft.Column(
                [
                    build_header(),
                    ft.Container(
                        padding=16,
                        content=card(
                            "دخول الأدمن",
                            ft.Column(
                                [
                                    password_input,
                                    ft.ElevatedButton("دخول", icon=ft.Icons.LOCK_OPEN, on_click=lambda e: page.run_task(login_admin)),
                                    ft.TextButton("رجوع للحضور", on_click=lambda e: page.run_task(show_attendance)),
                                ],
                                spacing=12,
                            ),
                        ),
                    ),
                ],
                spacing=0,
            )
        )

        page.add(login_layout)
        page.update()

    async def show_admin():
        await stop_camera()
        page.controls.clear()

        admin_layout = ft.SafeArea(
            content=ft.Column(
                [
                    build_header(),
                    ft.Container(
                        padding=16,
                        content=ft.Column(
                            [
                                card(
                                    "إضافة طالب",
                                    ft.Column(
                                        [
                                            reg_input,
                                            name_input,
                                            ft.ElevatedButton(
                                                "إضافة الطالب",
                                                icon=ft.Icons.PERSON_ADD,
                                                on_click=lambda e: page.run_task(add_student_click),
                                            ),
                                        ],
                                        spacing=12,
                                    ),
                                ),
                                card("قائمة الطلاب", students_list),
                                ft.Row(
                                    [
                                        ft.OutlinedButton("عودة للحضور", on_click=lambda e: page.run_task(show_attendance)),
                                        ft.OutlinedButton("تسجيل حضور", on_click=lambda e: page.run_task(show_attendance)),
                                    ],
                                    spacing=12,
                                ),
                            ],
                            spacing=16,
                        ),
                    ),
                ],
                spacing=0,
            )
        )

        page.add(admin_layout)
        page.update()
        await refresh_students()

    async def show_admin_gate():
        if state["is_admin"]:
            await show_admin()
        else:
            await show_admin_login()

    async def login_admin(e=None):
        if password_input.value.strip() == ADMIN_PASSWORD:
            state["is_admin"] = True
            notify("تم الدخول كأدمن")
            await show_admin()
        else:
            notify("كلمة المرور غير صحيحة")

    async def add_student_click(e=None):
        reg_no = reg_input.value.strip()
        name = name_input.value.strip()

        if not reg_no or not name:
            notify("أدخل رقم القيد والاسم")
            return

        add_student(reg_no, name)
        reg_input.value = ""
        name_input.value = ""
        notify("تمت إضافة الطالب")
        await refresh_students()

    def on_stream_image(e: fc.CameraImageEvent):
        try:
            now = time.monotonic()

            # تقليل التكرار
            if now - state["last_qr_ts"] < 1.0:
                return

            arr = np.frombuffer(e.bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                return

            data, points, _ = qr_detector.detectAndDecode(frame)
            if not data:
                return

            if data == state["last_qr"] and (now - state["last_qr_ts"]) < 2.0:
                return

            state["last_qr"] = data
            state["last_qr_ts"] = now

            if not data.startswith("REG-"):
                scan_result.value = "QR غير صحيح. الصيغة المطلوبة: REG-246066"
                page.update()
                return

            reg_no = data.removeprefix("REG-").strip()
            student_name = get_student_name(reg_no)

            if not student_name:
                scan_result.value = f"الطالب غير موجود: {reg_no}"
                page.update()
                return

            if marked_today(reg_no):
                scan_result.value = f"{student_name} مسجل مسبقًا اليوم"
                page.update()
                return

            mark_attendance(reg_no)
            scan_result.value = f"تم تسجيل حضور: {student_name}"
            page.update()
            page.run_task(refresh_today)

        except Exception as ex:
            scan_result.value = f"خطأ في المسح: {ex}"
            page.update()

    camera_preview.on_stream_image = on_stream_image

    await show_attendance()


init_db()
ft.app(target=main)
