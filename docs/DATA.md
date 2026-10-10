# โครงข้อมูล (`data/profile.yaml`)

แหล่งข้อมูลเดียวของทั้งเว็บ, Resume ทุกแบบ, `profile.json` และ WebMCP — แก้ที่นี่ที่เดียว

## กติกากลาง
- **ข้อความ** ใส่ได้ 2 แบบ: `"text"` หรือ `{en: "...", th: "..."}`
- **tags** ต้องมาจากคำศัพท์ที่กำหนด = slug ของ `focus` (`data, pipeline, bi, fraud, ai, cost`) + `extra_tags` (`leadership`)
  - tag เดียวเชื่อมทุกอย่าง: การ์ด focus → ผลงาน, Resume แต่ละแบบ (`variants/*.yaml` กรองด้วย tag), WebMCP
- **วันที่** รูปแบบ `YYYY-MM` (ตำแหน่งปัจจุบัน `end: Present`)
- **status** `draft` = ยังไม่ตรวจ → **ไม่ขึ้น** เว็บ / Resume / `profile.json` / WebMCP (ไม่ระบุ = `published`)
  ดูของที่เป็น draft ได้เฉพาะในเครื่องด้วย `python build.py --drafts`
- ค่าที่ยังไม่รู้ ให้ใส่ `TODO` (ห้ามเดา)

## ฟิลด์

| ส่วน | ฟิลด์ |
|---|---|
| `basics` | name, label, email, location, links[{label,url}] |
| `summaries` | key → ข้อความ (variant เลือกด้วย `summary:`) |
| `focus` (6) | slug, short, title, desc |
| `skills` | group, tags, items[] |
| `experience` | company, role, location, start, end, tags, status, bullets[{text, tags, status}] |
| `projects` | **slug** (kebab-case, ไม่ซ้ำ), name, period, role, tags, summary, problem, actions[], result, metrics[{label,value}], stack[], links[{label,url}], **sanitized**, status |
| `notes` | slug, title, tags, status (ยังไม่แสดงบนเว็บ) |
| `education` | school, degree, start, end, status |
| `certifications` | name, issuer, date, url, status |
| `interests` | รายการข้อความ |

`sanitized: true` หมายถึงเจ้าของตรวจแล้วว่าไม่มีชื่อลูกค้า ตัวเลขภายใน หรือข้อมูลลับ — validator จะเตือนผลงานที่ publish แล้วแต่ยังเป็น `false`

## คำสั่ง
```bash
python scripts/validate_data.py     # ตรวจโครงสร้าง tag slug วันที่ (error = exit 1, รันใน CI ด้วย)
python build.py                     # สร้างเว็บ+Resume (ข้าม draft)
python build.py --drafts            # ดูรวม draft (เฉพาะในเครื่อง ห้าม deploy)
```

## นำเข้าจาก LinkedIn
1. LinkedIn → Settings → Data privacy → **Get a copy of your data** → เลือก Positions, Projects, Skills, Education, Certifications, Profile
2. วางโฟลเดอร์ที่แตกไฟล์ไว้ใน `private/` (ถูก gitignore — **ห้าม commit ไฟล์ดิบ**)
3. `python scripts/import_linkedin.py private/<โฟลเดอร์>` → ได้ `private/linkedin.draft.yaml` (ทุกรายการ `status: draft`, tags ว่าง)
4. ตรวจทีละรายการ: จัด tag, ตัดข้อมูลลับ, เขียน problem/actions/result, แล้วย้ายเข้า `data/profile.yaml` และเปลี่ยนเป็น `published`
5. ลบโฟลเดอร์ใน `private/` เมื่อเสร็จ

ตัวนำเข้าอ่านเฉพาะ 6 ไฟล์ข้างต้น ไม่เปิด Connections, Messages, Email Addresses หรือ Phone Numbers
