# Roadmap — สิ่งที่เราจะทำ

เป้าหมาย: ให้นายจ้าง ผู้ร่วมงาน และคนที่มองหาคนร่วมงาน รู้ว่า **เราเป็นใคร ช่วยอะไรได้ และมีหลักฐานอะไร**
ผ่านเว็บบน GitHub Pages (desktop เป็นหลัก + mobile web app) และ Resume หลายแบบที่ generate จากข้อมูลชุดเดียว

สถานะ: ✅ เสร็จ · 🟡 โครงพร้อม รอเนื้อหา/ปรับ · ⬜ ยังไม่เริ่ม

## Phase 0 — โครงสร้าง ✅
- ✅ README / about / skills / experience / projects / interests (เอกสาร Markdown สำหรับอ่านบน GitHub)
- ✅ `data/profile.yaml` เป็นแหล่งข้อมูลเดียว (ฟิลด์ `{en, th}` ได้)
- ✅ `variants/*.yaml` = Resume 1 แบบต่อ 1 ไฟล์ (กรองด้วย tag, จำกัดความยาว, เลือกภาษา)
- ✅ `build.py` → `dist/` : เว็บ + Resume (HTML / MD / PDF)
- ✅ เว็บ 2 เวอร์ชัน: desktop (default) + mobile web app (`/m/`, แถบเมนูล่าง, redirect จอเล็ก, ปุ่ม "เว็บเต็ม")
- ✅ 2 ภาษา: ไทย (root) / อังกฤษ (`/en/`) · dark mode ตามระบบ
- ✅ WebMCP (8 tools แบบ read-only) + `profile.json`, `llms.txt`, JSON-LD สำหรับ AI ที่เข้ามา scan
- ✅ GitHub Actions deploy ไป Pages (`.github/workflows/pages.yml`)

## Phase 1 — เนื้อหาจริง 🟡 (สำคัญที่สุด)
- ⬜ ข้อมูลติดต่อ (email, LinkedIn) และ summary 3–4 บรรทัด
- ⬜ ประสบการณ์: ช่วงเวลา + ผลลัพธ์เป็นตัวเลข (ลดต้นทุน %, เวลา pipeline, SLA)
- ⬜ ผลงานอย่างน้อย 5 ชิ้น ตามหัวข้อ: Lakehouse, Fraud on AKS, Superset, Cost/Performance, AI Agent (โจทย์ → สิ่งที่ทำ → ผลลัพธ์ → เทคโนโลยี)
- ⬜ ตรวจข้อมูลลับ/ข้อมูลลูกค้าก่อน publish ทุกชิ้น
- ⬜ แทนที่ทุก `TODO` (build จะเตือนจำนวน TODO ที่เหลือ)

## Phase 2 — Deploy ⬜
- ⬜ รวมเข้า `main` และตั้งค่า Settings → Pages → Source = GitHub Actions
- ⬜ ตรวจบนเว็บจริงด้วย Playwright: overflow 360–390px, redirect มือถือ, ลิงก์ Resume ทุกแบบ, light/dark
- ⬜ ทดสอบ WebMCP กับเบราว์เซอร์/agent จริงที่รองรับ (ตอนนี้ทดสอบกับ `modelContext` จำลองเท่านั้น)
- ⬜ เพิ่ม favicon และ Open Graph image (ให้ลิงก์สวยเวลาแชร์)
- ⬜ (ถ้าต้องการ) custom domain

## Phase 3 — Resume หลายแบบ ⬜
- 🟡 มี 3 แบบเริ่มต้น: `default`, `data-engineer`, `ai-lead-th`
- ⬜ เพิ่มแบบตามกลุ่มผู้อ่าน เช่น Cost/FinOps, Fraud, 1-page สำหรับ recruiter
- ⬜ ปรับ print CSS ให้พอดี A4 (1–2 หน้า) และตรวจ PDF ภาษาไทย
- ⬜ (ตัวเลือก) export DOCX จาก Markdown สำหรับระบบ ATS บางแห่ง

## Phase 4 — เนื้อหาที่เติบโต ⬜
- ⬜ หน้า "Interests / Notes": บันทึกสิ่งที่กำลังเรียนรู้ (Databricks cost, AI agent, vector search)
- ⬜ Changelog ของโปรไฟล์ (เหมือน management-framework) เพื่อให้เห็นว่าอัปเดตต่อเนื่อง
- ⬜ ลิงก์ไป management-framework ในฐานะผลงานที่เผยแพร่
- ⬜ (ตัวเลือก) Matomo สำหรับดูว่าใครเปิดอ่านส่วนไหน

## ตัดสินใจแล้ว
| เรื่อง | ข้อสรุป |
|---|---|
| CSS | plain CSS + design tokens ตระกูลเดียวกับ management-framework (ไม่ใช้ Tailwind/Bootstrap) |
| Stack | Python + Jinja สร้าง static HTML; Next.js เก็บไว้ถ้าต้องการฟีเจอร์ที่ใช้ server |
| เวอร์ชันเว็บ | desktop เป็น default, mobile เป็น web app แยก (`/m/`) |
| ภาษา | ไทยเป็นหลัก, อังกฤษที่ `/en/` |
| AI เข้ามา scan | WebMCP (draft, บางเบราว์เซอร์) + ช่องทางสำรองที่ทุก crawler อ่านได้: `profile.json`, `llms.txt`, JSON-LD |

## เรื่องที่ยังต้องตัดสินใจ
- [ ] สี accent (ตอนนี้ใช้น้ำเงิน `#245fa6` เหมือน repo ที่ผ่านมา)
- [ ] License: โค้ด (MIT?) และเนื้อหา (CC BY 4.0 หรือสงวนสิทธิ์) — profile ส่วนตัวมักสงวนสิทธิ์เนื้อหาไว้
- [ ] ใส่ภาพถ่าย/โลโก้หรือไม่
- [ ] ชื่อ URL: `ppongsakorn.github.io/profiles/` หรือใช้ repo `ppongsakorn.github.io`
