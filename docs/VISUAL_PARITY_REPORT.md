# Visual Parity Report — PGCB Organization Portal

**Date:** September 29, 2026  
**Branch:** `production-completion`

---

## 1. Design System Alignment

| Token / Element | Target Specification | Implementation Status |
|---|---|---|
| Primary Institutional Brand | Deep Emerald (`#046A38` / `text-primary`, `bg-primary`) | **Aligned** across `tailwind.config.js`, `globals.css`, and all 71 routes |
| Dark Hero / Navigation Accent | Deep Slate / Emerald (`from-slate-900 via-slate-800 to-emerald-950`) | **Aligned** across Homepage, Directory, Circles, Notices, Circulars, Journal, Events, Media, and Verify |
| Bengali Typography | `Hind Siliguri` / `Noto Sans Bengali` with clean line-height (`1.6–1.75`) | **Aligned** in `app/layout.tsx` and `globals.css` |
| Secondary / Latin Typography | `Plus Jakarta Sans` & `JetBrains Mono` for IDs/codes | **Aligned** for `PGD-2026-XXXX`, Employee IDs, Receipt Nos, and QR Tokens |
| Card Radius & Elevation | `rounded-2xl` / `rounded-3xl`, `border-slate-200/80`, subtle hover lift | **Aligned** across all public, member, and admin surfaces |

---

## 2. Upgraded Legacy Routes (14 Routes Brought to Full Visual Parity)

All 14 legacy minified routes that previously used raw `section` / `grid-3` CSS have been upgraded to the modern Tailwind institutional design system:

1. `/committee` (`apps/web/app/committee/page.tsx`) — Unified with `/leadership` Executive Committee view.
2. `/committee/message` (`apps/web/app/committee/message/page.tsx`) — Dynamic President & General Secretary statement card.
3. `/circles` (`apps/web/app/circles/page.tsx`) — 20-circle regional network grid with live search and active member badges.
4. `/circles/[slug]` (`apps/web/app/circles/[slug]/page.tsx`) — Dynamic Circle detail with statistics, committee roster, active member directory preview, and regional office contact.
5. `/media` (`apps/web/app/media/page.tsx`) — Photo & video archive with category tabs, real `<img>` rendering, and interactive lightbox modal.
6. `/journal` (`apps/web/app/journal/page.tsx`) — Technical journal & research archive with search and `TECHNICAL` / `REPORT` / `SOUVENIR` filter tabs.
7. `/journal/[id]` (`apps/web/app/journal/[id]/page.tsx`) — Journal article reader with abstract callout and PDF/archive link.
8. `/events` (`apps/web/app/events/page.tsx`) — Conference & workshop calendar with upcoming filter and fee/capacity badges.
9. `/events/[id]` (`apps/web/app/events/[id]/page.tsx`) — Event detail view with venue, schedule, capacity, and registration CTA.
10. `/events/[id]/register` (`apps/web/app/events/[id]/register/page.tsx`) — Delegate registration form wired to `POST /api/v1/events/{id}/register`.
11. `/events/ticket/[token]` (`apps/web/app/events/ticket/[token]/page.tsx`) — Printable QR-verified delegate pass.
12. `/contact` (`apps/web/app/contact/page.tsx`) — Central secretariat contact page pulling PGCB Bhaban, Aftabnagar address from `/api/v1/public/settings` and returning support ticket numbers (`PGCB-TKT-...`).
13. `/privacy` & `/terms` (`apps/web/app/privacy/page.tsx`, `apps/web/app/terms/page.tsx`) — Institutional data protection and terms of use pages.
14. `/accessibility` (`apps/web/app/accessibility/page.tsx`) — Accessibility statement and keyboard/screen-reader support guide.
