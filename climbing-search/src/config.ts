/**
 * Application configuration.
 * Data loading goes through the Worker API (Plan 03) instead of static JSON files.
 */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ??
  'http://localhost:8787';
