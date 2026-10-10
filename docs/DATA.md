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
| `honors` | title, description, date (`YYYY`/`YYYY-MM`), result, status |
| `publications` | title, venue, date, role, status (**ไม่เก็บชื่อผู้เขียนร่วม**) |
| `patents` | title, description, issuer, number, url, status |
| `languages` | name, level |
| `notes` | slug, title, kind (topic/event), date, summary, tags, source, status (ยังไม่แสดงบนเว็บ) |
| `education` | school, degree, field, start, end (ปีเดียว `YYYY` ได้), status |
| `certifications` | name, issuer, date, url, status |
| `interests` | รายการข้อความ |

### ฟิลด์เล่าเรื่อง (experience / education)
`era` (ผูกกับ `eras`), `headline` (สรุปบรรทัดเดียว), `highlight: true` (ติดป้ายไฮไลต์), `side: true` (งานควบคู่),
`stack[]` (เทคโนโลยี), `bullets` (สิ่งที่ได้สร้างและส่งมอบ), `impact[]` (ผลลัพธ์ที่วัดได้ — **รอเจ้าของ**), `learned[]` (ความรู้/ประสบการณ์ที่ได้ — **รอเจ้าของ**)
- `eras` = 5 ช่วงอาชีพบนแถบสรุป · `snapshot` = ภาพรวมสำหรับ recruiter (`highlights` ใช้ `{years}` ได้, `stack`, `open_to`, `scope`; ค่า `TODO` ไม่แสดง)
- `hobbies[]` = {slug, name, public}

### สองภาษา
ข้อความบรรยายต้องมีทั้ง `en` และ `th` · ชื่อบริษัท/ตำแหน่ง/ศัพท์เทคนิคคงเป็นอังกฤษ · validator เตือนถ้าขาดภาษาใดภาษาหนึ่ง

`sanitized: true` หมายถึงเจ้าของตรวจแล้วว่าไม่มีชื่อลูกค้า ตัวเลขภายใน หรือข้อมูลลับ — validator จะเตือนผลงานที่ publish แล้วแต่ยังเป็น `false`

## PII: ห้ามเข้า Git (repo นี้เป็น public)
**ห้ามอยู่ใน repo:** อีเมลส่วนตัว เบอร์โทร ที่อยู่ วันเกิด IP address เลขบัตร/ใบเสร็จ รายชื่อและข้อความของบุคคลอื่น
(Connections, Invitations, Messages) ข้อมูลโฆษณา และ URL รูปภาพที่มี token ของ LinkedIn

- **อีเมลสาธารณะ** มีได้ที่เดียวคือ `basics.email` ใน `data/profile.yaml` เมื่อเจ้าของเลือกเผยแพร่เอง (ตอนนี้ยังเป็น `TODO`)
- ไฟล์ export ดิบเก็บใน `private/` เท่านั้น (gitignore) แล้วลบทิ้งเมื่อเสร็จ
- **ด่านอัตโนมัติ** `scripts/check_pii.py` จับ: ไฟล์ `*.csv/*.zip/*.vcf/*.xlsx`, อีเมล, เบอร์โทร (ไทย/สากล), IPv4, เลข 13 หลัก, URL รูป LinkedIn
  - local: pre-commit hook บล็อก commit (เปิดครั้งเดียวต่อเครื่อง: `sh scripts/install_hooks.sh`)
  - CI: รันก่อน build ทุกครั้ง · ตรวจ history ย้อนหลัง: `python scripts/check_pii.py --history`
- ข้อมูลของ**บุคคลที่สาม** (ผู้เขียนร่วม ลูกค้า คอนเนกชัน) ไม่ใส่ชื่อ ใช้บทบาทแทน

## แผนที่ข้อมูลจาก LinkedIn export
| ไฟล์ | การตัดสินใจ | ลงที่ |
|---|---|---|
| Positions | **ใช้** (8 ตำแหน่ง 2006-ปัจจุบัน เรียบเรียงเป็น bullets + tags) | `experience` |
| Profile | **ใช้บางส่วน**: headline, summary, เมืองระดับเขต/จังหวัด | `summaries`, `basics.location` |
| Skills (50) | **ใช้** จัดกลุ่มใหม่ 8 กลุ่ม ตัดคำกว้างเกินไป | `skills` |
| Education | **ใช้** (รอชื่อสถาบัน) | `education` |
| Certifications | **ใช้** (MCAD, SCJP; ไม่มีวันที่) | `certifications` |
| Honors | **ใช้** (4 รางวัล/การแข่งขัน; ไม่เดาอันดับ) | `honors` |
| Publications / Patents | **ใช้** ไม่ใส่ชื่อผู้เขียนร่วม | `publications`, `patents` |
| Languages | **ใช้** | `languages` |
| Rich_Media | **ใช้บางส่วน**: เนื้อหาโพสต์งาน Databricks → `notes` (draft); ไม่ใช้ URL รูป/ชื่อบุคคลอื่น | `notes` |
| Company_Follows | **ไม่ใช้** (รายการติดตามเป็นข้อมูลส่วนตัว/ไม่ใช่ผลงาน) | - |
| Causes_You_Care_About | **ยังไม่ใช้** (รอเจ้าของตัดสินใจ) | - |
| Email_Addresses, PhoneNumbers, Whatsapp, Registration (IP), Receipts, Ad_Targeting | **ห้ามใช้ (PII)** | - |
| Connections, Invitations, Messages, Notes | **ห้ามใช้** (ข้อมูลบุคคลอื่น) ผมไม่เปิดอ่าน | - |
| Profile_Summary, Organizations | ว่าง | - |

## ความสัมพันธ์ (tag เป็นตัวเชื่อม)
```
focus (data · pipeline · bi · fraud · ai · cost)
   ├─ experience.bullets ─┐
   ├─ projects ───────────┼─► Resume variants (กรองด้วย tag)
   ├─ skills ─────────────┤
   └─ notes ──────────────┘
extra_tags: leadership · software (ยุค developer 2006–2020) · teaching
ไม่มี tag โฟกัส: honors · publications · patents · education · certifications · languages  → ส่วน "เบื้องหลัง/หลักฐานเสริม"
```

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

ตัวนำเข้าอ่านเฉพาะไฟล์ในตาราง "ใช้" ข้างบน (และจากไฟล์ Profile อ่านแค่ headline/summary/เมือง) ไม่เปิด Connections, Invitations, Messages, Email Addresses, Phone Numbers หรือไฟล์ PII อื่น
