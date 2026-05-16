import type { RouteType } from '../api/types';
export type { RouteType };

export const ROUTE_TYPE_LABELS: Record<RouteType, string> = {
  sport: 'Sport', trad: 'Trad', aid: 'Aid', ice: 'Ice', alpine: 'Alpine',
  mixed: 'Mixed', tr: 'Top Rope', boulder: 'Boulder', snow: 'Snow',
};

export interface GradeRange {
  min: string;
  max: string;
}

export interface RouteFilters {
  grades: {
    min: string;
    max: string;
  };
  types: RouteType[];
  tags: { category: string; selectedTags: string[] }[];
}

export const GRADE_ORDER = [
  // 5.3-5.9 with variations
  "Easy",
  "1st",
  "2nd",
  "3rd",
  "4th",
  "5th",
  "5.0",
  "5.1",
  "5.2",
  "5.3",
  "5.4",
  "5.5",
  "5.6-", "5.6", "5.6+",
  "5.7-", "5.7", "5.7+",
  "5.8-", "5.8", "5.8+",
  "5.9-", "5.9", "5.9+",
  
  // 5.10-5.16 with all variations
  "5.10-", "5.10a", "5.10a/b", "5.10", "5.10b", "5.10b/c", "5.10c", "5.10c/d", "5.10d", "5.10+",
  "5.11-", "5.11a", "5.11a/b", "5.11", "5.11b", "5.11b/c", "5.11c", "5.11c/d", "5.11d", "5.11+",
  "5.12-", "5.12a", "5.12a/b", "5.12", "5.12b", "5.12b/c", "5.12c", "5.12c/d", "5.12d", "5.12+",
  "5.13-", "5.13a", "5.13a/b", "5.13", "5.13b", "5.13b/c", "5.13c", "5.13c/d", "5.13d", "5.13+",
  "5.14-", "5.14a", "5.14a/b", "5.14", "5.14b", "5.14b/c", "5.14c", "5.14c/d", "5.14d", "5.14+",
  "5.15-", "5.15a", "5.15a/b", "5.15", "5.15b", "5.15b/c", "5.15c", "5.15c/d", "5.15d", "5.15+",
  "5.16-", "5.16a", "5.16a/b", "5.16", "5.16b", "5.16b/c", "5.16c", "5.16c/d", "5.16d", "5.16+"
];

// Simplified list for UI
export const SIMPLE_GRADES = [
  "5.3",
  "5.4",
  "5.5",
  "5.6", "5.7", "5.8", "5.9",
  "5.10a", "5.10b", "5.10c", "5.10d",
  "5.11a", "5.11b", "5.11c", "5.11d",
  "5.12a", "5.12b", "5.12c", "5.12d",
  "5.13a", "5.13b", "5.13c", "5.13d",
  "5.14a", "5.14b", "5.14c", "5.14d",
  "5.15a", "5.15b", "5.15c", "5.15d",
  "5.16a", "5.16b", "5.16c", "5.16d"
];

// Helper function to normalize grade
export function normalizeGrade(grade: string): string {
  if (!grade || grade === '') return '';

  // Handle base grades without letters (e.g., "5.10" -> "5.10b")
  const baseGradeMatch = grade.match(/^5\.(\d+)$/);
  if (baseGradeMatch) {
    const number = parseInt(baseGradeMatch[1]);
    if (number >= 10) {
      return `${grade}b`; // Convert "5.10" to "5.10b" for middle difficulty
    }
    return grade;
  }

  // Handle minus grades
  if (grade.endsWith('-')) {
    const base = grade.slice(0, -1);
    if (base === '5.6' || base === '5.7' || base === '5.8' || base === '5.9') {
      return base; // For 5.6-5.9, minus is easier than the base grade
    }
    return `${base}a`; // For 5.10 and up, minus means 'a' grade
  }
  
  // Handle plus grades
  if (grade.endsWith('+')) {
    const base = grade.slice(0, -1);
    if (base === '5.6' || base === '5.7' || base === '5.8' || base === '5.9') {
      return base; // For 5.6-5.9, plus is harder than the base grade
    }
    return `${base}d`; // For 5.10 and up, plus means 'd' grade
  }

  // Handle in-between grades (e.g., "5.10a/b")
  if (grade.includes('/')) {
    const [first] = grade.split('/');
    return first; // Use the lower of the two grades
  }

  return grade;
}

/**
 * Extract a numeric sort key for aid grade from route_grade and/or route_protection_grading.
 * Regex: /([AC])(\d+)(\+?)/ — matches A0-A6+, C0-C6+.
 * A and C share the same numeric scale (C2 ≈ A2, gear style differs only).
 * Returns level + 0.5 for + suffix (e.g. A3+ → 3.5).
 * Returns null if no aid grade found in either field.
 */
export function extractAidGradeNumeric(routeGrade: string | null, protectionGrading: string | null): number | null {
  const AID_RE = /([AC])(\d+)(\+?)/;
  for (const src of [routeGrade, protectionGrading]) {
    if (!src) continue;
    const m = src.match(AID_RE);
    if (m) return parseInt(m[2]) + (m[3] === '+' ? 0.5 : 0);
  }
  return null;
}

/**
 * Extract a numeric sort key for ice grade from route_grade.
 * Regex: /(WI|AI)(\d+)(\+?)/ — matches WI1-WI7+, AI1-AI5+.
 * WI and AI share the same numeric scale.
 * Returns level + 0.5 for + suffix (e.g. WI4+ → 4.5).
 * Returns null if no ice grade found.
 */
export function extractIceGradeNumeric(routeGrade: string | null): number | null {
  const ICE_RE = /(WI|AI)(\d+)(\+?)/;
  if (!routeGrade) return null;
  const m = routeGrade.match(ICE_RE);
  if (m) return parseInt(m[2]) + (m[3] === '+' ? 0.5 : 0);
  return null;
}

/**
 * Extract a numeric sort key for mixed grade from route_grade and/or route_protection_grading.
 * Regex: /M(\d+)(\+?)/ — matches M1-M12+.
 * Returns level + 0.5 for + suffix (e.g. M6+ → 6.5).
 * Returns null if no mixed grade found in either field.
 */
export function extractMixedGradeNumeric(routeGrade: string | null, protectionGrading: string | null): number | null {
  const MIXED_RE = /M(\d+)(\+?)/;
  for (const src of [routeGrade, protectionGrading]) {
    if (!src) continue;
    const m = src.match(MIXED_RE);
    if (m) return parseInt(m[1]) + (m[2] === '+' ? 0.5 : 0);
  }
  return null;
}

export type SortOption = 'grade' | 'stars' | 'left_to_right' | 'votes' | 'aid_grade' | 'ice_grade' | 'mixed_grade';

export interface SortConfig {
  option: SortOption;
  ascending: boolean;
} 