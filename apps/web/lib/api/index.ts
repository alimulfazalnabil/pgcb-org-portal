/**
 * Centralized Typed API Client for PGCB Organization Portal.
 * Consolidates all domain API modules into an ergonomic, type-safe interface.
 */

import { authApi } from './auth';
import { noticesApi } from './notices';
import { documentsApi } from './documents';
import { membersApi } from './members';
import { applicationsApi } from './applications';
import { eventsApi } from './events';
import { adminApi } from './admin';
import { publicApi } from './public';

export * from './types';
export * from './client';

export const api = {
  ...authApi,
  ...noticesApi,
  ...documentsApi,
  ...membersApi,
  ...applicationsApi,
  ...eventsApi,
  ...adminApi,
  ...publicApi,
};
