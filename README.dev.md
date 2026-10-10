# วิธีใช้ระบบ Generate

ข้อมูลทั้งหมดอยู่ที่ `data/profile.yaml` (แหล่งเดียว) — ส่วน Resume แต่ละแบบคือไฟล์ใน `variants/`

```bash
pip install -r requirements.txt
python build.py                 # html + md -> dist/
python build.py --pdf           # + PDF (ต้องมี Chromium)
python build.py --only ai-lead-th
```

## เพิ่ม Resume แบบใหม่ (ไม่จำกัด)
คัดลอก `variants/default.yaml` เป็นชื่อใหม่ แล้วปรับ:

| key | ความหมาย |
|---|---|
| `tags` | เลือกเฉพาะรายการที่มี tag ตรงกัน (รายการที่ตรงมากกว่าจะขึ้นก่อน; ไม่มี tag = ใส่ทุกแบบ) |
| `lang` | `en` / `th` (ฟิลด์ใส่ `{en:..., th:...}` ได้) |
| `summary` | key ใน `summaries:` |
| `sections` | ลำดับและส่วนที่แสดง |
| `max_bullets`, `max_projects` | จำกัดความยาวให้พอดี 1–2 หน้า |
| `formats` | `html`, `md`, `pdf` |

Push เข้า `main` แล้ว GitHub Actions จะ build และ deploy ไป GitHub Pages เอง
(ตั้งค่าครั้งเดียว: Settings → Pages → Source = **GitHub Actions**)
