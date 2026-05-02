import flet as ft
import sqlite3
from datetime import datetime

DB = "attendance.db"

# ---------- DATABASE ----------
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

# ---------- DB HELPERS ----------
def get_students():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT reg_no, name FROM students")
    data = c.fetchall()
    conn.close()
    return data

def add_student(reg_no, name):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO students (reg_no, name) VALUES (?, ?)", (reg_no, name))
        conn.commit()
    except:
        pass
    conn.close()

def get_student(reg_no):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE reg_no=?", (reg_no,))
    result = c.fetchone()
    conn.close()
    return result

def already_marked_today(reg_no):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE reg_no=? AND date=?", (reg_no, today))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_attendance(reg_no):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO attendance (reg_no, date, time) VALUES (?, ?, ?)",
        (reg_no, date, time)
    )
    conn.commit()
    conn.close()

# ---------- MAIN APP ----------
def main(page: ft.Page):
    page.title = "نظام حضور QR - رقم القيد"
    page.scroll = "auto"

    output = ft.Text(size=18, weight="bold", color="green")

    # ---------- ADMIN ----------
    name_input = ft.TextField(label="اسم الطالب", width=300)
    reg_input = ft.TextField(label="رقم القيد (مثال: 246066)", width=300)

    student_list = ft.Column()

    def refresh_students():
        student_list.controls.clear()
        for s in get_students():
            student_list.controls.append(
                ft.Text(f"{s[0]} | {s[1]}")
            )
        page.update()

    def add_student_click(e):
        reg = reg_input.value.strip()
        name = name_input.value.strip()

        if not reg or not name:
            output.value = "❌ أدخل الاسم ورقم القيد"
            page.update()
            return

        add_student(reg, name)

        reg_input.value = ""
        name_input.value = ""

        output.value = "✔ تم إضافة الطالب"
        refresh_students()

    admin_view = ft.Column([
        ft.Text("👨‍💼 لوحة الإدارة", size=22),
        reg_input,
        name_input,
        ft.ElevatedButton("إضافة طالب", on_click=add_student_click),
        ft.Divider(),
        ft.Text("📋 قائمة الطلاب"),
        student_list,
        ft.ElevatedButton("➡️ الانتقال للحضور", on_click=lambda e: show_attendance())
    ])

    # ---------- ATTENDANCE ----------
    scan_input = ft.TextField(label="أدخل QR (مثال: REG-246066)", width=300)

    def handle_scan(e):
        data = scan_input.value.strip()

        if not data.startswith("REG-"):
            output.value = "❌ QR غير صحيح"
            page.update()
            return

        reg_no = data.replace("REG-", "")

        student = get_student(reg_no)

        if not student:
            output.value = "❌ الطالب غير موجود"
            page.update()
            return

        name = student[0]

        if already_marked_today(reg_no):
            output.value = f"⚠️ {name} مسجل مسبقًا اليوم"
            page.update()
            return

        mark_attendance(reg_no)
        output.value = f"✔ تم تسجيل حضور: {name}"

        scan_input.value = ""
        page.update()

    attendance_view = ft.Column([
        ft.Text("📷 تسجيل الحضور", size=22),
        scan_input,
        ft.ElevatedButton("تسجيل الحضور", on_click=handle_scan),
        ft.ElevatedButton("⬅️ الرجوع للإدارة", on_click=lambda e: show_admin())
    ])

    # ---------- NAVIGATION ----------
    def show_admin():
        page.controls.clear()
        page.add(admin_view, output)
        refresh_students()

    def show_attendance():
        page.controls.clear()
        page.add(attendance_view, output)

    # ---------- START ----------
    if len(get_students()) == 0:
        show_admin()
    else:
        show_attendance()

# ---------- RUN ----------
init_db()
ft.app(target=main)
