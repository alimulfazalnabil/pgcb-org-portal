'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { ShieldCheck, Lock, Users } from 'lucide-react';

interface RoleInfo {
  role: string;
  permissions: string[];
  user_count: number;
}

export default function AdminRolesPage() {
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [currentRole, setCurrentRole] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/backend/api/v1/admin/roles').then((r) => (r.ok ? r.json() : [])),
      fetch('/backend/api/v1/admin/permissions').then((r) => (r.ok ? r.json() : null)),
    ])
      .then(([rolesData, permData]) => {
        if (Array.isArray(rolesData)) setRoles(rolesData);
        if (permData?.role) setCurrentRole(permData.role);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const roleDescriptions: Record<string, string> = {
    SUPER_ADMIN: 'সকল মডিউল, নিরাপত্তা সেটিংস, রোল ও অডিট লগের পূর্ণ নিয়ন্ত্রণ (*)',
    CONTENT_EDITOR: 'সার্কুলার, নোটিশ, জার্নাল, ইভেন্ট ও মিডিয়া গ্যালারি প্রকাশনা ও সম্পাদনা',
    MEMBERSHIP_OFFICER: 'সদস্য আবেদন যাচাই, ডকুমেন্ট অনুমোদন, CSV ইমপোর্ট ও সনদ ইস্যু',
    CIRCLE_ADMIN: 'গ্রিড সার্কেল তথ্য ব্যবস্থাপনা এবং সার্কেলভিত্তিক সদস্য তালিকা পর্যবেক্ষণ',
    FINANCE_OFFICER: 'সদস্যপদ চাঁদা, নবায়ন ও ইভেন্ট পেমেন্ট যাচাই এবং আর্থিক রিপোর্ট এক্সপোর্ট',
    AUDITOR: 'সিকিউরিটি অডিট লগ, সদস্য রোস্টার এবং প্রকাশিত কনটেন্টের রিড-অনলি পরিদর্শন',
    MEMBER: 'নিজস্ব মেম্বার প্রোফাইল, ডিজিটাল কার্ড, ইভেন্ট নিবন্ধন ও নোটিফিকেশন অ্যাক্সেস',
  };

  return (
    <>
      <AdminHeader
        title="রোল ও পারমিশন ম্যাট্রিক্স (RBAC Governance)"
        subtitle="সচিবালয় ও পোর্টালের ৭টি প্রাতিষ্ঠানিক রোলের অ্যাক্সেস কন্ট্রোল ও পারমিশন তালিকা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2.5 text-xs">
            <ShieldCheck size={18} className="text-primary" />
            <span className="font-bold text-foreground">
              আপনার বর্তমান সক্রিয় রোল: <span className="font-mono text-primary">{currentRole || 'ADMIN'}</span>
            </span>
          </div>
          <span className="text-[11px] text-secondary">
            ন্যূনতম সুবিধা নীতি (Principle of Least Privilege) অনুযায়ী সার্ভার-সাইডে প্রতিটি রিকোয়েস্ট যাচাই করা হয়।
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-secondary bg-card border border-border rounded-2xl">
            আরবিএসি পারমিশন ম্যাট্রিক্স লোড হচ্ছে...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {roles.map((item) => (
              <div
                key={item.role}
                className="bg-card border border-border rounded-2xl p-6 space-y-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="px-2.5 py-1 rounded-md bg-primary/10 text-primary font-mono text-xs font-extrabold">
                      {item.role}
                    </span>
                    <p className="text-xs text-secondary mt-2 leading-relaxed">
                      {roleDescriptions[item.role] || 'প্রাতিষ্ঠানিক রোল'}
                    </p>
                  </div>
                  <div className="px-3 py-1.5 rounded-xl bg-surface border border-border text-xs font-bold text-foreground flex items-center gap-1.5 shrink-0">
                    <Users size={13} className="text-primary" />
                    <span>{item.user_count} জন</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-border space-y-2">
                  <div className="text-[11px] font-bold text-secondary uppercase flex items-center gap-1">
                    <Lock size={12} /> অনুমোদিত পারমিশন স্কোপ ({item.permissions.length})
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {item.permissions.map((perm) => (
                      <span
                        key={perm}
                        className="px-2 py-0.5 rounded-md bg-surface border border-border font-mono text-[11px] text-foreground"
                      >
                        {perm}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
