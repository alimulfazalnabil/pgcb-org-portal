'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { MemberDataTable, MemberRecord } from '@/components/MemberDataTable';
import { api } from '@/lib/api';

export default function AdminMembersPage() {
  const [members, setMembers] = useState<MemberRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const data = await api.getAdminMembers({ limit: 200 });
      setMembers(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, []);

  const handleMemberAction = async (id: number, action: string) => {
    await api.reviewMember(id, action as any);
    await fetchMembers();
  };

  const handleReviewDoc = async (id: number, action: string) => {
    await fetch(`/backend/api/v1/admin/documents/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    await fetchMembers();
  };

  return (
    <>
      <AdminHeader
        title="সদস্য তালিকা ও বাল্ক ইমপোর্ট (Members Directory)"
        subtitle="সদস্যপদ স্থিতি পরিচালনা, পরিচয়পত্র তৈরি ও সিএসভি ফাইলের মাধ্যমে একযোগে সদস্য সংযোজন"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        <MemberDataTable
          members={members}
          onRefresh={fetchMembers}
          onMemberAction={handleMemberAction}
          onReviewDoc={handleReviewDoc}
        />
      </div>
    </>
  );
}
