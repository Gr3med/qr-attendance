import flet as ft
import sqlite3
from datetime import datetime

# Flutter widget wrapper (QR Scanner)
from flet_flutter import FlutterControl
from flet_flutter import MobileScanner  # uses camera for QR/Barcode

DB = "attendance.db"
ADMIN_PASSWORD = "123456"


# ---------- DB ----------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            reg_no TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_students():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT reg_no, name FROM students ORDER BY reg_no")
    rows = c.fetchall()
    conn.close()
    return rows


def add_student(reg_no, name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO students (reg_no, name) VALUES (?,?)", (reg_no, name))
    conn.commit()
    conn.close()


def get_student(reg_no):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE reg_no=?", (reg_no,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def marked_today(reg_no):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM attendance WHERE reg_no=? AND date=? LIMIT 1", (reg_no, today))
    r = c.fetchone()
    conn.close()
    return r is not None


def mark_attendance(reg_no):
    now = datetime.now()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO attendance (reg_no, date, time) VALUES (?, ?, ?)",
        (reg_no, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
    )
    conn.commit()
    conn.close()


# ---------- UI ----------
def main(page: ft.Page):
    page.title = "QR Attendance"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # Theme (simple modern look)
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
        use_material3=True
    )

    msg = ft.Text(size=16, weight=ft.FontWeight.BOLD)

    is_admin = False

    # ---------- Admin UI ----------
    reg_input = ft.TextField(label="رقم القيد", border_radius=12)
    name_input = ft.TextField(label="اسم الطالب", border_radius=12)

    students_list = ft.Column()

    def refresh_students():
        students_list.controls.clear()
        for reg, name in get_students():
            students_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(reg, weight="bold"),
                        ft.Text(name)
                    ], alignment="spaceBetween"),
                    padding=10,
                    border_radius=12,
                    bgcolor=ft.colors.GREY_100
                )
            )
        page.update()

    def add_student_click(e):
        if not reg_input.value or not name_input.value:
            msg.value = "أدخل البيانات"
            page.update()
            return
        add_student(reg_input.value, name_input.value)
        reg_input.value = ""
        name_input.value = ""
        msg.value = "تمت الإضافة"
        refresh_students()

    admin_view = ft.Column([
        ft.Text("لوحة الإدارة", size=24, weight="bold"),
        reg_input,
        name_input,
        ft.ElevatedButton("إضافة", on_click=add_student_click),
        ft.Divider(),
        students_list,
        ft.ElevatedButton("⬅ رجوع", on_click=lambda e: show_attendance())
    ])

    # ---------- Scanner ----------
    def on_scan(barcode):
        data = barcode["rawValue"]

        if not data.startswith("REG-"):
            msg.value = "QR غير صحيح"
            page.update()
            return

        reg_no = data.replace("REG-", "")
        name = get_student(reg_no)

        if not name:
            msg.value = "الطالب غير موجود"
            page.update()
            return

        if marked_today(reg_no):
            msg.value = f"{name} مسجل مسبقًا"
            page.update()
            return

        mark_attendance(reg_no)
        msg.value = f"✔ تم تسجيل: {name}"
        page.update()

    scanner = FlutterControl(
        control=MobileScanner(
            on_detect=on_scan,
            fit="cover"
        ),
        expand=True
    )

    attendance_view = ft.Stack([
        scanner,
        ft.Container(
            content=ft.Column([
                ft.Text("وجّه الكاميرا نحو QR", color="white"),
                ft.ElevatedButton("دخول الأدمن", on_click=lambda e: show_login())
            ]),
            alignment=ft.alignment.bottom_center,
            padding=20
        )
    ])

    # ---------- Login ----------
    password_input = ft.TextField(password=True, label="كلمة المرور")

    def login(e):
        nonlocal is_admin
        if password_input.value == ADMIN_PASSWORD:
            is_admin = True
            show_admin()
        else:
            msg.value = "كلمة المرور خاطئة"
            page.update()

    login_view = ft.Column([
        ft.Text("دخول الأدمن", size=22),
        password_input,
        ft.ElevatedButton("دخول", on_click=login),
        ft.ElevatedButton("رجوع", on_click=lambda e: show_attendance())
    ])

    # ---------- Navigation ----------
    def show_admin():
        if not is_admin:
            show_login()
            return
        page.controls.clear()
        page.add(admin_view, msg)
        refresh_students()

    def show_login():
        page.controls.clear()
        page.add(login_view, msg)

    def show_attendance():
        page.controls.clear()
        page.add(attendance_view, msg)

    # start
    if len(get_students()) == 0:
        show_admin()
    else:
        show_attendance()


init_db()
ft.app(target=main)
