'use client';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'তথ্য লোড হচ্ছে...' }: LoadingStateProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 16px', minHeight: '200px' }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid #e2e8f0',
        borderTop: '4px solid #006a4e',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <p style={{ marginTop: '16px', color: '#64748b', fontSize: '14px', fontWeight: 500 }}>
        {message}
      </p>
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
