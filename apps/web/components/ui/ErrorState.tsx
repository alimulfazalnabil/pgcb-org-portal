'use client';

import React from 'react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = 'তথ্য লোড করতে সমস্যা হয়েছে। অনুগ্রহ করে পুনরায় চেষ্টা করুন।',
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        textAlign: 'center',
        backgroundColor: '#fef2f2',
        borderRadius: '10px',
        border: '1px solid #fecaca',
        margin: '16px 0',
      }}
    >
      <div style={{ fontSize: '36px', marginBottom: '8px' }}>⚠️</div>
      <h4 style={{ margin: '0 0 6px 0', color: '#991b1b', fontSize: '16px', fontWeight: 600 }}>
        ত্রুটি ঘটেছে (Error Occurred)
      </h4>
      <p style={{ margin: '0 0 16px 0', color: '#7f1d1d', fontSize: '13px', maxWidth: '400px' }}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            backgroundColor: '#dc2626',
            color: '#fff',
            border: 'none',
            padding: '8px 20px',
            borderRadius: '6px',
            fontWeight: 500,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          পুনরায় চেষ্টা করুন (Retry)
        </button>
      )}
    </div>
  );
}
