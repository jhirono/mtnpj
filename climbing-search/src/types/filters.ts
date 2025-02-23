export interface GradeRange {
  min: string;
  max: string;
}

export interface RouteFilters {
  grades: GradeRange;
  types: ('Trad' | 'Sport')[];
  tags: {
    category: string;
    selectedTags: string[];
  }[];
}

export const GRADE_ORDER = [
  // 5.6-5.9 with variations
  "5.6-", "5.6", "5.6+",
  "5.7-", "5.7", "5.7+",
  "5.8-", "5.8", "5.8+",
  "5.9-", "5.9", "5.9+",
  
  // 5.10-5.16 with all variations
  "5.10-", "5.10a", "5.10a/b", "5.10b", "5.10b/c", "5.10c", "5.10c/d", "5.10d", "5.10+",
  "5.11-", "5.11a", "5.11a/b", "5.11b", "5.11b/c", "5.11c", "5.11c/d", "5.11d", "5.11+",
  "5.12-", "5.12a", "5.12a/b", "5.12b", "5.12b/c", "5.12c", "5.12c/d", "5.12d", "5.12+",
  "5.13-", "5.13a", "5.13a/b", "5.13b", "5.13b/c", "5.13c", "5.13c/d", "5.13d", "5.13+",
  "5.14-", "5.14a", "5.14a/b", "5.14b", "5.14b/c", "5.14c", "5.14c/d", "5.14d", "5.14+",
  "5.15-", "5.15a", "5.15a/b", "5.15b", "5.15b/c", "5.15c", "5.15c/d", "5.15d", "5.15+",
  "5.16-", "5.16a", "5.16a/b", "5.16b", "5.16b/c", "5.16c", "5.16c/d", "5.16d", "5.16+"
];

// Simplified list for UI
export const SIMPLE_GRADES = [
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

export type SortOption = 'grade' | 'stars' | 'left_to_right' | 'votes';

export interface SortConfig {
  option: SortOption;
  ascending: boolean;
} 