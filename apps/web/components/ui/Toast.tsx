'use client';

import React from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface ToastProps {
  message: string;
  type?: ToastType;
  onClose?: () => void;
}

export function Toast({ message, type = 'info', onClose }: ToastProps) {
  const bgColors = {
    success: '#059669',
    error: '#dc2626',
    warning: '#d97706',
    info: '#0284c7',
  };

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        backgroundColor: bgColors[type],
        color: '#ffffff',
        padding: '12px 20px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
        zIndex: 10000,
        fontSize: '14px',
        fontWeight: 500,
        maxWidth: '420px',
        animation: 'slideUpToast 0.2s ease-out',
      }}
    >
      <span style={{ fontWeight: 700, fontSize: '16px' }}>{icons[type]}</span>
      <span style={{ flex: 1 }}>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '16px',
            opacity: 0.8,
            padding: '2px',
          }}
        >
          &times;
        </button>
      )}
      <style jsx>{`
        @keyframes slideUpToast {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
