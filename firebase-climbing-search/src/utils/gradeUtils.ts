// YDS (Yosemite Decimal System) grades for rock climbing
export const GRADE_ORDER = [
  '5.0', '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.7', '5.8', '5.9',
  '5.10a', '5.10b', '5.10c', '5.10d',
  '5.11a', '5.11b', '5.11c', '5.11d',
  '5.12a', '5.12b', '5.12c', '5.12d',
  '5.13a', '5.13b', '5.13c', '5.13d',
  '5.14a', '5.14b', '5.14c', '5.14d',
  '5.15a', '5.15b', '5.15c', '5.15d',
];

// The full detailed grade order used during data migration
// This matches the grades stored in Firestore
export const FULL_GRADE_ORDER = [
  // 5.3-5.9 with variations
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

// Mapping from simplified UI grades to the full grade order
const GRADE_MAPPING: { [key: string]: string } = {
  '5.3': '5.3',
  '5.4': '5.4',
  '5.5': '5.5',
  '5.6': '5.6',
  '5.7': '5.7',
  '5.8': '5.8',
  '5.9': '5.9',
  '5.10a': '5.10a',
  '5.10b': '5.10b',
  '5.10c': '5.10c',
  '5.10d': '5.10d',
  '5.11a': '5.11a',
  '5.11b': '5.11b',
  '5.11c': '5.11c',
  '5.11d': '5.11d',
  '5.12a': '5.12a',
  '5.12b': '5.12b',
  '5.12c': '5.12c',
  '5.12d': '5.12d',
  '5.13a': '5.13a',
  '5.13b': '5.13b',
  '5.13c': '5.13c',
  '5.13d': '5.13d',
  '5.14a': '5.14a',
  '5.14b': '5.14b',
  '5.14c': '5.14c',
  '5.14d': '5.14d',
  '5.15a': '5.15a',
  '5.15b': '5.15b',
  '5.15c': '5.15c',
  '5.15d': '5.15d',
  '5.16a': '5.16a',
  '5.16b': '5.16b',
  '5.16c': '5.16c',
  '5.16d': '5.16d'
};

/**
 * Normalizes a grade string to a standard format
 * @param grade The grade string to normalize
 * @returns The normalized grade string
 */
export function normalizeGrade(grade: string | undefined): string {
  if (!grade) return '5.0'; // Default to easiest grade if undefined
  
  // Strip whitespace and convert to lowercase for consistent comparison
  const cleanGrade = grade.trim().toLowerCase();
  
  // Handle common variations and typos
  if (cleanGrade.includes('5.10')) {
    if (cleanGrade.includes('a')) return '5.10a';
    if (cleanGrade.includes('b')) return '5.10b';
    if (cleanGrade.includes('c')) return '5.10c';
    if (cleanGrade.includes('d')) return '5.10d';
    return '5.10a'; // Default to 'a' if no letter specified
  }
  
  if (cleanGrade.includes('5.11')) {
    if (cleanGrade.includes('a')) return '5.11a';
    if (cleanGrade.includes('b')) return '5.11b';
    if (cleanGrade.includes('c')) return '5.11c';
    if (cleanGrade.includes('d')) return '5.11d';
    return '5.11a';
  }
  
  if (cleanGrade.includes('5.12')) {
    if (cleanGrade.includes('a')) return '5.12a';
    if (cleanGrade.includes('b')) return '5.12b';
    if (cleanGrade.includes('c')) return '5.12c';
    if (cleanGrade.includes('d')) return '5.12d';
    return '5.12a';
  }
  
  if (cleanGrade.includes('5.13')) {
    if (cleanGrade.includes('a')) return '5.13a';
    if (cleanGrade.includes('b')) return '5.13b';
    if (cleanGrade.includes('c')) return '5.13c';
    if (cleanGrade.includes('d')) return '5.13d';
    return '5.13a';
  }
  
  if (cleanGrade.includes('5.14')) {
    if (cleanGrade.includes('a')) return '5.14a';
    if (cleanGrade.includes('b')) return '5.14b';
    if (cleanGrade.includes('c')) return '5.14c';
    if (cleanGrade.includes('d')) return '5.14d';
    return '5.14a';
  }
  
  if (cleanGrade.includes('5.15')) {
    if (cleanGrade.includes('a')) return '5.15a';
    if (cleanGrade.includes('b')) return '5.15b';
    if (cleanGrade.includes('c')) return '5.15c';
    if (cleanGrade.includes('d')) return '5.15d';
    return '5.15a';
  }
  
  // Handle single digit grades (5.0 - 5.9)
  for (let i = 0; i <= 9; i++) {
    if (cleanGrade.includes(`5.${i}`)) {
      return `5.${i}`;
    }
  }
  
  // If we couldn't match a known pattern, return a default
  return '5.0';
}

/**
 * Converts a grade string to a numeric value for sorting
 * @param grade The grade to convert
 * @returns A numeric value representing the grade's difficulty
 */
export function gradeToNumeric(grade: string): number {
  // First, normalize the grade to our standard format
  const normalized = normalizeGrade(grade);
  
  // Map the normalized grade to the full grade system used in the database
  const mappedGrade = GRADE_MAPPING[normalized] || normalized;
  
  // Find the index in the FULL grade order (same as used during migration)
  const index = FULL_GRADE_ORDER.indexOf(mappedGrade);
  
  // If found, return the index, otherwise try a fallback search
  if (index >= 0) {
    console.log(`Grade ${grade} normalized to ${normalized}, mapped to ${mappedGrade}, index: ${index}`);
    return index;
  }
  
  // Fallback: try to find the closest match in the full grade order
  // This helps with grades that might not have a direct mapping
  for (let i = 0; i < FULL_GRADE_ORDER.length; i++) {
    if (FULL_GRADE_ORDER[i].startsWith(normalized.split('/')[0])) {
      console.log(`Grade ${grade} normalized to ${normalized}, fallback match: ${FULL_GRADE_ORDER[i]}, index: ${i}`);
      return i;
    }
  }
  
  // If all else fails, return 0 (easiest grade)
  console.log(`Grade ${grade} normalized to ${normalized}, no match found, defaulting to 0`);
  return 0;
}

/**
 * Compares two grades and returns whether the first is harder than the second
 * @param grade1 The first grade to compare
 * @param grade2 The second grade to compare
 * @returns True if grade1 is harder than grade2, false otherwise
 */
export function isHarderGrade(grade1: string, grade2: string): boolean {
  return gradeToNumeric(grade1) > gradeToNumeric(grade2);
}

/**
 * Checks if a grade is within a specified range (inclusive)
 * @param grade The grade to check
 * @param minGrade The minimum grade in the range
 * @param maxGrade The maximum grade in the range
 * @returns True if the grade is within the range, false otherwise
 */
export function isGradeInRange(grade: string, minGrade: string, maxGrade: string): boolean {
  const gradeNumeric = gradeToNumeric(grade);
  const minNumeric = gradeToNumeric(minGrade);
  const maxNumeric = gradeToNumeric(maxGrade);
  
  return gradeNumeric >= minNumeric && gradeNumeric <= maxNumeric;
} 