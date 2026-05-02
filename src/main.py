import flet as ft
import sqlite3
from datetime import datetime

DB = "attendance.db"
ADMIN_PASSWORD = "123456"  # غيّرها كما تريد


# -------------------- DB --------------------
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
            time TEXT NOT NULL
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


def get_student(reg_no: str):
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
        "INSERT INTO attendance (reg_no, date, time) VALUES (?, ?, ?)",
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
def main(page: ft.Page):
    page.title = "نظام حضور الطلاب QR"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    def notify(text: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(text))
        page.snack_bar.open = True
        page.update()

    is_admin = False

    # -------- shared widgets --------
    students_list = ft.Column(spacing=10, expand=False)
    today_list = ft.Column(spacing=10, expand=False)

    total_students_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)
    total_today_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD)

    reg_input = ft.TextField(
        label="رقم القيد",
        hint_text="مثال: 246066",
        border_radius=14,
        width=320,
    )
    name_input = ft.TextField(
        label="اسم الطالب",
        hint_text="اسم الطالب كاملًا",
        border_radius=14,
        width=320,
    )

    qr_input = ft.TextField(
        label="QR الممسوح",
        hint_text="REG-246066",
        border_radius=14,
        width=360,
    )

    password_input = ft.TextField(
        label="كلمة مرور الأدمن",
        password=True,
        can_reveal_password=True,
        border_radius=14,
        width=320,
    )

    # -------- refresh helpers --------
    def refresh_stats():
        total_students_text.value = str(count_students())
        total_today_text.value = str(count_today_attendance())
        page.update()

    def refresh_students():
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
        refresh_stats()

    def refresh_today():
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
            for time, reg_no, name in rows:
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
                                ft.Text(f"{reg_no}  •  {time}", color=ft.Colors.GREY_700),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )
        refresh_stats()

    # -------- views --------
    def build_header():
        return ft.Container(
            padding=20,
            border_radius=0,
            bgcolor=ft.Colors.INDIGO,
            content=ft.Column(
                [
                    ft.Text(
                        "نظام حضور الطلاب عبر QR",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "إدارة الطلاب والتحضير بسرعة وبشكل منظم",
                        size=14,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                "الحضور",
                                on_click=lambda e: show_attendance(),
                                style=ft.ButtonStyle(color=ft.Colors.WHITE),
                            ),
                            ft.OutlinedButton(
                                "الإدارة",
                                on_click=lambda e: show_admin_gate(),
                                style=ft.ButtonStyle(color=ft.Colors.WHITE),
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=8,
            ),
        )

    def card(title, content):
        return ft.Container(
            padding=16,
            border_radius=18,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
            content=ft.Column(
                [
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    content,
                ],
                spacing=12,
            ),
        )

    def attendance_view():
        return ft.Column(
            [
                card(
                    "تحضير الطالب",
                    ft.Column(
                        [
                            qr_input,
                            ft.ElevatedButton(
                                "تسجيل الحضور",
                                icon=ft.Icons.QR_CODE_SCANNER,
                                on_click=handle_scan,
                            ),
                            ft.Text(
                                "صيغة QR المطلوبة: REG-246066",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=12,
                    ),
                ),
                ft.Row(
                    [
                        ft.Container(
                            expand=1,
                            content=card(
                                "عدد الطلاب",
                                ft.Text(total_students_text.value, size=24, weight=ft.FontWeight.BOLD),
                            ),
                        ),
                        ft.Container(
                            expand=1,
                            content=card(
                                "حضور اليوم",
                                ft.Text(total_today_text.value, size=24, weight=ft.FontWeight.BOLD),
                            ),
                        ),
                    ],
                    spacing=12,
                ),
                card(
                    "آخر الحضور",
                    today_list,
                ),
            ],
            spacing=16,
            expand=True,
        )

    def admin_login_view():
        return ft.Column(
            [
                card(
                    "دخول الأدمن",
                    ft.Column(
                        [
                            password_input,
                            ft.ElevatedButton(
                                "دخول",
                                icon=ft.Icons.LOCK_OPEN,
                                on_click=login_admin,
                            ),
                            ft.TextButton(
                                "رجوع",
                                on_click=lambda e: show_attendance(),
                            ),
                        ],
                        spacing=12,
                    ),
                )
            ],
            spacing=16,
            expand=True,
        )

    def admin_view():
        return ft.Column(
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
                                on_click=add_student_click,
                            ),
                        ],
                        spacing=12,
                    ),
                ),
                card(
                    "قائمة الطلاب",
                    students_list,
                ),
            ],
            spacing=16,
            expand=True,
        )

    screen_host = ft.Container(expand=True, padding=16)

    def show_attendance():
        screen_host.content = attendance_view()
        refresh_today()
        page.update()

    def show_admin_gate():
        if is_admin:
            show_admin()
        else:
            show_login()

    def show_login():
        screen_host.content = admin_login_view()
        page.update()

    def show_admin():
        screen_host.content = admin_view()
        refresh_students()
        page.update()

    # -------- actions --------
    def handle_scan(e):
        data = qr_input.value.strip()

        if not data.startswith("REG-"):
            notify("QR غير صحيح. الصيغة المطلوبة: REG-246066")
            return

        reg_no = data.removeprefix("REG-").strip()
        name = get_student(reg_no)

        if not name:
            notify("الطالب غير موجود")
            return

        if marked_today(reg_no):
            notify(f"{name} مسجل مسبقًا اليوم")
            return

        mark_attendance(reg_no)
        qr_input.value = ""
        notify(f"تم تسجيل حضور: {name}")
        refresh_today()
        page.update()

    def add_student_click(e):
        reg_no = reg_input.value.strip()
        name = name_input.value.strip()

        if not reg_no or not name:
            notify("أدخل رقم القيد والاسم")
            return

        add_student(reg_no, name)
        reg_input.value = ""
        name_input.value = ""
        notify("تمت إضافة الطالب")
        refresh_students()
        page.update()

    def login_admin(e):
        nonlocal is_admin
        if password_input.value == ADMIN_PASSWORD:
            is_admin = True
            notify("تم الدخول كأدمن")
            show_admin()
        else:
            notify("كلمة المرور غير صحيحة")

    # -------- layout --------
    page.add(
        ft.SafeArea(
            content=ft.Column(
                [
                    build_header(),
                    screen_host,
                ],
                spacing=0,
                expand=True,
            )
        )
    )

    # start
    show_attendance()


init_db()
ft.app(target=main)
