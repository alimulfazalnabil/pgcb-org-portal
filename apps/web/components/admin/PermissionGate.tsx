import React, { ReactNode } from 'react';

interface PermissionGateProps {
  permissions: string[];
  required: string;
  fallback?: ReactNode;
  children: ReactNode;
}

export function PermissionGate({
  permissions,
  required,
  fallback = null,
  children,
}: PermissionGateProps) {
  const hasAccess =
    permissions.includes('*') ||
    permissions.includes(required) ||
    permissions.some((p) => p.endsWith('.*') && required.startsWith(p.replace('.*', '')));

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
