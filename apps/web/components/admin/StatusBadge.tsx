import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const norm = (status || '').toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300';

  if (['ACTIVE', 'APPROVED', 'SUCCESS', 'COMPLETED', 'PUBLISHED', 'VERIFIED', 'PAID'].includes(norm)) {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800/50';
  } else if (['PENDING', 'SUBMITTED', 'DRAFT', 'QUEUED', 'PAYMENT_PENDING'].includes(norm)) {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800/50';
  } else if (['UNDER_REVIEW', 'IN_PROGRESS', 'PROCESSING'].includes(norm)) {
    colorClasses = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800/50';
  } else if (['REJECTED', 'FAILED', 'CANCELLED', 'SUSPENDED', 'REVOKED'].includes(norm)) {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800/50';
  } else if (['CORRECTION_REQUIRED', 'DOCUMENTS_REQUIRED', 'NEEDS_INFO', 'ACTION_REQUIRED'].includes(norm)) {
    colorClasses = 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-400 dark:border-purple-800/50';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${colorClasses} ${className}`}
    >
      {status}
    </span>
  );
}
