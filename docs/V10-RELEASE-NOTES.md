# v1.0 RC Release Notes

## Public experience
- Added site-wide public search across published circulars, journals, events and media.
- Added dynamic public statistics endpoint for future homepage KPI widgets.
- Added privacy, terms and accessibility pages.
- Added Next.js sitemap, robots and manifest metadata.
- Added 404/error states and a keyboard-accessible skip link.
- Added a responsive mobile navigation drawer and direct search entry point.

## Operations / platform
- API version promoted to `1.0.0-rc1`.
- Added `/live` liveness endpoint while retaining `/health` and `/ready`.
- Expanded release tests for liveness, stats and public search.
- Consolidated release documentation and production checklist.

## RC limitations
- The organization domain, approved logos/photos, legal wording and final contact data remain deployment inputs.
- Payment/SMS providers remain adapter-based until provider credentials/contracts are supplied.
- Clean Next.js install/build and Terraform plan require the standard CI/toolchain environment.
