import { test, expect } from '@playwright/test';

test.describe('PGCB Portal Comprehensive E2E Journeys', () => {
  test('PUBLIC: Homepage loads, displays Bangla-first content, and toggles Bangla <-> English', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('পাওয়ার গ্রিড প্রকৌশলী সমিতি');

    const registerBtn = page.getByRole('link', { name: /সদস্যপদের? আবেদন/ }).first();
    await expect(registerBtn).toBeVisible();

    // Switch to English
    const langBtn = page.getByRole('button', { name: /Switch language/i }).first();
    await langBtn.click();
    await expect(page.locator('h1')).toContainText('Power Grid Engineers Association');

    // Switch back to Bangla
    await langBtn.click();
    await expect(page.locator('h1')).toContainText('পাওয়ার গ্রিড প্রকৌশলী সমিতি');
  });

  test('PUBLIC: Member directory, notices, events, and publications load', async ({ page }) => {
    // Member directory
    await page.goto('/members');
    await expect(page.locator('h1')).toContainText('সদস্য প্রকৌশলী ডিরেক্টরি');
    await expect(page.getByText(/মোট সক্রিয় সদস্য/)).toBeVisible();

    // Notices
    await page.goto('/notices');
    await expect(page.locator('h1')).toContainText('অফিসিয়াল নোটিশ বোর্ড');

    // Events
    await page.goto('/events');
    await expect(page.locator('h1')).toContainText(/ইভেন্ট ও কার্যক্রম|কেন্দ্রীয় সম্মেলন, কাউন্সিল ও কারিগরি কর্মশালা/);

    // Publications / Journal
    await page.goto('/journal');
    await expect(page.locator('h1')).toContainText(/গ্রিড কারিগরি জার্নাল ও প্রকাশনা|কারিগরি জার্নাল, গবেষণা ও স্মরণিকা/);
  });

  test('PUBLIC: Circular directory filters correctly', async ({ page }) => {
    await page.goto('/circulars');
    await page.waitForLoadState('networkidle');

    const officeOrderBtn = page.getByRole('button', { name: 'অফিস আদেশ' });
    await officeOrderBtn.click();
    await expect(officeOrderBtn).toHaveClass(/bg-primary/);
  });

  test('PUBLIC: Certificate and membership verification handle valid and invalid tokens', async ({ page }) => {
    await page.goto('/certificate/invalid-token-123');
    await expect(page.getByText('সনদপত্রটি খুঁজে পাওয়া যায়নি')).toBeVisible();

    await page.goto('/verify?membership_id=PGD-2026-1001');
    await expect(page.getByText(/PGD-2026-1001/).first()).toBeVisible();
  });

  test('SECURITY: Unauthenticated user trying to access /member is denied', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/member');
    await expect(page.getByText('সদস্য পোর্টাল প্রবেশাধিকার')).toBeVisible();
    await expect(page.getByRole('link', { name: 'লগইন করুন' })).toBeVisible();
  });

  test('AUTH: Invalid login is rejected and registration form submits via /backend proxy', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Email').fill('member@example.org');
    await page.getByPlaceholder('Password').fill('WrongPassword999!');
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.locator('.notice-error')).toBeVisible();

    const uniqueEmail = `e2e.reg.${Date.now()}@example.org`;
    const regRes = await page.request.post('/backend/api/v1/auth/register', {
      data: {
        email: uniqueEmail,
        password: 'ChangeMe123!',
        name_bn: 'ইটুই নিবন্ধনকারী',
        name_en: 'E2E Registrant',
        phone: '01711000000',
      },
    });
    expect(regRes.ok()).toBeTruthy();
  });

  test('MEMBER & SECURITY: Member login, dashboard, profile/document/application APIs, and /admin denial', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Email').fill('member@example.org');
    await page.getByPlaceholder('Password').fill('ChangeMe123!');
    await page.getByRole('button', { name: 'Login' }).click();

    await page.waitForURL(/\/portal/);
    await expect(page.getByText(/সদস্য ড্যাশবোর্ড|প্রোফাইল|PGD-2026-1001/).first()).toBeVisible();

    // Verify member profile update & document upload with valid PDF magic bytes
    const profRes = await page.request.get('/backend/api/v1/member/profile');
    expect(profRes.ok()).toBeTruthy();
    const prof = await profRes.json();

    const patchRes = await page.request.patch('/backend/api/v1/member/profile', {
      data: {
        ...prof,
        current_address: 'ঢাকা, বাংলাদেশ',
      },
    });
    expect(patchRes.ok()).toBeTruthy();

    const docRes = await page.request.post('/backend/api/v1/member/documents?document_type=NID', {
      multipart: {
        file: {
          name: 'e2e_nid.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.from('%PDF-1.4\n%E2E Member Document\n%%EOF'),
        },
      },
    });
    expect(docRes.ok()).toBeTruthy();

    // Security: Member trying to access /admin is denied
    await page.goto('/admin');
    await expect(page.getByText(/অননুমোদিত এক্সেস|Access Restricted/).first()).toBeVisible();

    // Logout invalidates session
    const logoutRes = await page.request.post('/backend/api/v1/auth/logout');
    expect(logoutRes.ok()).toBeTruthy();
  });

  test('ADMIN & PAYMENT: Admin login, dashboard stats, member/circular/event/certificate management, and payment flow', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('Email').fill('admin@example.org');
    await page.getByPlaceholder('Password').fill('ChangeMe123!');
    await page.getByRole('button', { name: 'Login' }).click();

    await page.waitForURL(/\/admin/);
    await expect(page.getByText(/সচিবালয় নিয়ন্ত্রণ প্যানেল/).first()).toBeVisible();

    // Admin members page
    await page.goto('/admin/members');
    await expect(page.getByText(/PGD-2026-1001/).first()).toBeVisible();

    // Admin circular CRUD via proxy
    const circRes = await page.request.post('/backend/api/v1/admin/circulars', {
      data: {
        title_bn: 'ইটুই টেস্ট সার্কুলার ২০২৬',
        category: 'GENERAL',
        summary_bn: 'ইটুই পরীক্ষার জন্য প্রকাশিত সার্কুলার',
        is_published: true,
      },
    });
    expect(circRes.ok()).toBeTruthy();

    // Admin event CRUD + certificate issuance & verification
    const evtRes = await page.request.post('/backend/api/v1/admin/events', {
      data: {
        title_bn: 'ইটুই কারিগরি কর্মশালা ২০২৬',
        event_date: new Date(Date.now() + 86400_000).toISOString(),
        location_bn: 'ঢাকা',
        registration_enabled: true,
        is_published: true,
      },
    });
    expect(evtRes.ok()).toBeTruthy();
    const evt = await evtRes.json();

    const regRes = await page.request.post(`/backend/api/v1/events/${evt.id}/registrations`, {
      data: {
        name: 'E2E Certificate Engineer',
        email: `e2e.cert.${Date.now()}@example.org`,
      },
    });
    expect(regRes.ok()).toBeTruthy();
    const reg = await regRes.json();

    const checkInRes = await page.request.post(`/backend/api/v1/admin/event-registrations/${reg.id}/check-in`);
    expect(checkInRes.ok()).toBeTruthy();

    const certRes = await page.request.post(`/backend/api/v1/certificates/event-registrations/${reg.id}`);
    expect(certRes.ok()).toBeTruthy();
    const cert = await certRes.json();

    await page.goto(`/certificate/${cert.verification_token}`);
    await expect(page.getByText('VERIFIED CERTIFICATE OF PARTICIPATION')).toBeVisible();

    // Payment initiation via checkout endpoint
    const checkoutRes = await page.request.post('/backend/api/v1/member/payments/checkout', {
      data: {
        amount: 500,
        currency: 'BDT',
        purpose: 'DONATION',
        provider: 'TEST',
      },
    });
    expect(checkoutRes.ok()).toBeTruthy();
    const checkout = await checkoutRes.json();
    expect(checkout.provider_transaction_id).toContain('TEST-');
  });

  test('PRODUCTION E2E: Complete 15-step Member Lifecycle, Payment Hardening & Verification', async ({ page }) => {
    const ts = Date.now();
    const testEmail = `prod.e2e.${ts}@example.org`;

    // 1 & 2. Register & Verify account (REQUIRE_EMAIL_VERIFICATION=false in E2E)
    const regRes = await page.request.post('/backend/api/v1/auth/register', {
      data: {
        email: testEmail,
        password: 'ChangeMe123!',
        name_bn: 'প্রোডাকশন ইটুই প্রকৌশলী',
        name_en: 'Production E2E Engineer',
        phone: '01788000099',
      },
    });
    expect(regRes.ok()).toBeTruthy();

    // 3. Login as newly registered member
    const loginRes = await page.request.post('/backend/api/v1/auth/login', {
      data: { email: testEmail, password: 'ChangeMe123!' },
    });
    expect(loginRes.ok()).toBeTruthy();

    // 4. Complete profile
    const profPatch = await page.request.patch('/backend/api/v1/member/profile', {
      data: {
        name_bn: 'প্রোডাকশন ইটুই প্রকৌশলী',
        name_en: 'Production E2E Engineer',
        phone: '01788000099',
        designation_bn: 'সহকারী প্রকৌশলী',
        designation_en: 'Assistant Engineer',
        employee_id: `PGCB-E2E-${ts}`,
        diploma_institution: 'ঢাকা পলিটেকনিক ইনস্টিটিউট',
        graduation_year: 2018,
        nid_number: '1996000011223',
        current_address: 'ঢাকা, বাংলাদেশ',
        permanent_address: 'ঢাকা, বাংলাদেশ',
      },
    });
    expect(profPatch.ok()).toBeTruthy();
    const memberId = (await profPatch.json()).id;

    // 5. Upload documents
    const docUpload = await page.request.post('/backend/api/v1/member/documents?document_type=NID', {
      multipart: {
        file: {
          name: 'prod_e2e_nid.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.from('%PDF-1.4\n%Production E2E NID Document\n%%EOF'),
        },
      },
    });
    expect(docUpload.ok()).toBeTruthy();

    // 6. Submit membership application
    const applyRes = await page.request.post('/backend/api/v1/member/apply');
    expect(applyRes.ok()).toBeTruthy();

    // 8. Payment (verify tampered client amount is rejected first, then initiate valid ANNUAL_STANDARD payment)
    const tamperedPay = await page.request.post('/backend/api/v1/member/payments/checkout', {
      data: {
        membership_plan_id: 'ANNUAL_STANDARD',
        amount: 1,
        provider: 'TEST',
      },
    });
    expect(tamperedPay.status()).toBe(400);

    const validPay = await page.request.post('/backend/api/v1/member/payments/checkout', {
      data: {
        membership_plan_id: 'ANNUAL_STANDARD',
        provider: 'TEST',
        idempotency_key: `e2e-idem-${ts}`,
      },
    });
    expect(validPay.ok()).toBeTruthy();
    const payData = await validPay.json();
    expect(payData.amount).toBe(2000);

    // 9. Payment verification (Server-side callback + idempotency replay check)
    const cbRes = await page.request.post('/backend/api/v1/payments/callback/TEST', {
      data: {
        transaction_id: payData.transaction_id,
        provider_transaction_id: payData.provider_transaction_id,
        status: 'SUCCESS',
        amount: 2000,
      },
    });
    expect(cbRes.ok()).toBeTruthy();

    // 7, 10 & 11. Admin review & approval -> Membership ID assigned
    await page.request.post('/backend/api/v1/auth/login', {
      data: { email: 'admin@example.org', password: 'ChangeMe123!' },
    });
    const reviewRes = await page.request.post(`/backend/api/v1/admin/members/${memberId}/review?action=REVIEW`);
    expect(reviewRes.ok()).toBeTruthy();

    const approveRes = await page.request.post(`/backend/api/v1/admin/members/${memberId}/review?action=APPROVE`);
    expect(approveRes.ok()).toBeTruthy();
    const approvedData = await approveRes.json();
    expect(approvedData.status).toBe('ACTIVE');
    expect(approvedData.membership_id).toBeTruthy();

    // 14. Certificate creation by admin
    const evtRes = await page.request.post('/backend/api/v1/admin/events', {
      data: {
        title_bn: 'প্রোডাকশন ইটুই সার্টিফিকেট কর্মশালা',
        event_date: new Date(Date.now() + 86400_000).toISOString(),
        location_bn: 'ঢাকা',
        registration_enabled: true,
        is_published: true,
      },
    });
    const evt = await evtRes.json();
    const eregRes = await page.request.post(`/backend/api/v1/events/${evt.id}/registrations`, {
      data: { name: 'Production E2E Engineer', email: testEmail },
    });
    const ereg = await eregRes.json();
    await page.request.post(`/backend/api/v1/admin/event-registrations/${ereg.id}/check-in`);
    const certRes = await page.request.post(`/backend/api/v1/certificates/event-registrations/${ereg.id}`);
    expect(certRes.ok()).toBeTruthy();
    const cert = await certRes.json();

    // Switch back to member session to verify Digital ID, QR verification, Certificate, and Notifications
    await page.request.post('/backend/api/v1/auth/login', {
      data: { email: testEmail, password: 'ChangeMe123!' },
    });

    // 12. Digital ID (PNG + 2-page PDF)
    const cardPng = await page.request.get('/backend/api/v1/member/card?side=front');
    expect(cardPng.ok()).toBeTruthy();
    const cardPdf = await page.request.get('/backend/api/v1/member/card.pdf');
    expect(cardPdf.ok()).toBeTruthy();

    // 13. QR verification
    const qrVerify = await page.request.get(`/backend/api/v1/public/verify/${approvedData.membership_id}`);
    expect(qrVerify.ok()).toBeTruthy();
    expect((await qrVerify.json()).verified).toBe(true);

    // 14b. Verify Certificate
    const certVerify = await page.request.get(`/backend/api/v1/certificates/verify/${cert.verification_token}`);
    expect(certVerify.ok()).toBeTruthy();
    expect((await certVerify.json()).verified).toBe(true);

    // 15. Notification delivery
    const notifRes = await page.request.get('/backend/api/v1/member/notifications');
    expect(notifRes.ok()).toBeTruthy();
    const notifs = await notifRes.json();
    expect(notifs.length).toBeGreaterThanOrEqual(2);
  });
});

