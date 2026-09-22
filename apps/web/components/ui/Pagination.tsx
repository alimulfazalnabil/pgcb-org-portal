'use client';

import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', margin: '24px 0' }}>
      <button
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        style={{
          padding: '6px 14px',
          borderRadius: '6px',
          border: '1px solid #d1d5db',
          backgroundColor: currentPage <= 1 ? '#f3f4f6' : '#ffffff',
          color: currentPage <= 1 ? '#9ca3af' : '#1f2937',
          cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: 500,
        }}
      >
        পূর্ববর্তী (Prev)
      </button>

      <span style={{ fontSize: '13px', color: '#4b5563', padding: '0 8px' }}>
        পৃষ্ঠা {currentPage} / {totalPages}
      </span>

      <button
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        style={{
          padding: '6px 14px',
          borderRadius: '6px',
          border: '1px solid #d1d5db',
          backgroundColor: currentPage >= totalPages ? '#f3f4f6' : '#ffffff',
          color: currentPage >= totalPages ? '#9ca3af' : '#1f2937',
          cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: 500,
        }}
      >
        পরবর্তী (Next)
      </button>
    </div>
  );
}
