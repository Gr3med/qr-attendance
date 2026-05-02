import sqlite3
import time
from datetime import datetime

import cv2
import numpy as np
import flet as ft
import flet_camera as fc
from openpyxl import load_workbook

DB = "attendance.db"
QR_SEP = "|"
PATH_KEY = "excel_path"

qr = cv2.QRCodeDetector()


# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS students(
        reg TEXT PRIMARY KEY,
        name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS att(
        reg TEXT,
        name TEXT,
        date TEXT,
        time TEXT,
        UNIQUE(reg,date)
    )
    """)

    conn.commit()
    conn.close()


def import_excel(path):
    wb = load_workbook(path)
    ws = wb.active

    data = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] and r[1]:
            name = str(r[0]).strip()
            reg = str(r[1]).strip()
            data.append((reg, name))

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM students")
    c.executemany("INSERT INTO students VALUES (?,?)", data)
    conn.commit()
    conn.close()

    return len(data)


def get_student(reg):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE reg=?", (reg,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None


def mark(reg, name):
    now = datetime.now()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO att VALUES (?,?,?,?)",
        (reg, name, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
    )
    conn.commit()
    conn.close()


# ---------------- APP ----------------
async def main(page: ft.Page):
    page.title = "QR Attendance"
    page.theme_mode = ft.ThemeMode.LIGHT

    prefs = page.shared_preferences

    result = ft.Text(size=20, weight="bold")

    path_input = ft.TextField(
        label="مسار Excel",
        hint_text="/storage/emulated/0/Download/students.xlsx"
    )

    # تحميل المسار المحفوظ
    saved = await prefs.get(PATH_KEY)
    if saved:
        path_input.value = saved

    def notify(t):
        page.snack_bar = ft.SnackBar(content=ft.Text(t))
        page.snack_bar.open = True
        page.update()

    async def save_path(e):
        await prefs.set(PATH_KEY, path_input.value)
        notify("✔ تم حفظ المسار")

    async def load_excel(e):
        try:
            count = import_excel(path_input.value)
            notify(f"✔ تم تحميل {count} طالب")
        except Exception as ex:
            notify(f"❌ {ex}")

    def parse(q):
        if QR_SEP not in q:
            return None, None
        name, reg = q.split(QR_SEP)
        return name.strip(), reg.strip()

    last_scan = {"val": "", "time": 0}

    def on_frame(e):
        try:
            now = time.time()
            if now - last_scan["time"] < 1:
                return

            img = np.frombuffer(e.bytes, np.uint8)
            frame = cv2.imdecode(img, 1)

            val, _, _ = qr.detectAndDecode(frame)

            if not val:
                return

            if val == last_scan["val"]:
                return

            last_scan["val"] = val
            last_scan["time"] = now

            name, reg = parse(val)

            if not reg:
                result.value = "❌ QR غير صحيح"
                page.update()
                return

            db_name = get_student(reg)

            if not db_name:
                result.value = "❌ غير موجود"
                page.update()
                return

            mark(reg, db_name)

            result.value = f"✔ {db_name}"
            page.update()

        except:
            pass

    cam = fc.Camera(
        preview_enabled=True,
        on_stream_image=on_frame
    )

    page.add(
        ft.Column(
            [
                ft.Text("📷 QR Attendance", size=24),
                cam,
                result,
                ft.Divider(),
                path_input,
                ft.Row(
                    [
                        ft.ElevatedButton("💾 حفظ", on_click=save_path),
                        ft.ElevatedButton("📥 تحميل Excel", on_click=load_excel),
                    ]
                ),
            ],
            scroll=True
        )
    )


init_db()
ft.app(target=main)
