'use client';

import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon = '📭',
  title = 'কোনো তথ্য পাওয়া যায়নি',
  description = 'বর্তমানে প্রদর্শনের জন্য কোনো রেকর্ড বিদ্যমান নেই।',
  actionText,
  onAction,
}: EmptyStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '56px 20px',
        textAlign: 'center',
        backgroundColor: '#f8fafc',
        borderRadius: '12px',
        border: '1px dashed #cbd5e1',
        margin: '16px 0',
      }}
    >
      <div style={{ fontSize: '42px', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ margin: '0 0 8px 0', color: '#1e293b', fontSize: '18px', fontWeight: 600 }}>
        {title}
      </h3>
      <p style={{ margin: '0 0 20px 0', color: '#64748b', fontSize: '14px', maxWidth: '420px', lineHeight: 1.5 }}>
        {description}
      </p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="btn btn-primary"
          style={{
            backgroundColor: '#006a4e',
            color: '#fff',
            border: 'none',
            padding: '10px 24px',
            borderRadius: '6px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
