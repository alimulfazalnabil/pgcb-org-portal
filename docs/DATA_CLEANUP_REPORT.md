# Data Cleanup & Official Dataset Report — PGCB Organization Portal

**Date:** September 29, 2026  
**Branch:** `production-completion`

---

## 1. Removal of Hardcoded Demo / Fabricated Content

| Location | Previous Demo / Placeholder Content | Clean Production Replacement |
|---|---|---|
| `apps/web/app/circles/[slug]/page.tsx` | Hardcoded `allowed` array of 9 names + fake names `প্রকৌ. উদাহরণ নাম 1/2/3` | Dynamic lookup via `GET /api/v1/public/circles/{circle_id}` supporting all 20 Diprokous circles and displaying real verified members |
| `apps/web/app/committee/message/page.tsx` | Hardcoded `"প্রকৌশলী মোঃ আব্দুর রহমান"` | Dynamic fetch from `GET /api/v1/public/committee` and `GET /api/v1/public/settings` |
| `apps/web/app/contact/page.tsx` | Hardcoded `"IDEb Bhaban, Kakrail"` & `+880 2 2234 8901` | Dynamic fetch from `GET /api/v1/public/settings` defaulting to **পিজিসিবি ভবন, আফতাবনগর, বাড্ডা, ঢাকা-১২১২** |
| `apps/web/app/media/page.tsx` | Static `▧` text symbol instead of images | Real `<img>` rendering with institutional SVG fallback and lightbox modal |
| `services/api/app/db/seed.py` | `MediaAsset(url='#')` with English placeholder titles | Official Bengali institutional titles and `/brand/pgcb-logo.svg` asset URLs |

---

## 2. Official 1,457-Member & 20-Circle Diprokous Dataset (`2026–2028` Term)

Extracted and normalized from the official 81-page Diprokous (PGCB) Central Executive Committee Election `2026–2028` Final Voter List (`চূড়ান্ত ভোটার তালিকা`):

- **Structured CSV:** `services/api/data/pgcb_members_official_2026_2028.csv` (`1,457` members)
- **Structured JSON:** `services/api/data/pgcb_members_official_2026_2028.json` (`20` circles + `1,457` members)
- **Idempotent PostgreSQL/SQLite SQL Seed:** `services/api/data/pgcb_members_official_2026_2028.sql`
- **Automated Importer & Validator:** `services/api/scripts/import_official_member_list.py` (`--dry-run` and `--apply`)
- **Integrated Seed Flag:** `python -m app.db.seed --production --import-official-members`

### Validation Summary
- **Total Official Members:** `1,457`
- **Total Official Branch Committees / Grid Circles:** `20`
- **Unique Membership IDs (`PGD-2026-0001` .. `PGD-2026-1457`):** `1,457`
- **Unique Diprokous Member Nos:** `1,457`
- **Unique PGCB Employee IDs:** `1,457`
