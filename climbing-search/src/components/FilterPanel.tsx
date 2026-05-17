import { useState, useMemo } from 'react'
import type { RouteFilters, GradeRange, SortConfig, SortOption, GradeSystem } from '../types/filters'
import { GRADE_ORDER, SIMPLE_GRADES, GRADE_LISTS, ROUTE_TYPE_LABELS } from '../types/filters'
import { ROUTE_TYPES } from '../api/types'

interface FilterPanelProps {
  filters: RouteFilters;
  onChange: (filters: RouteFilters) => void;
  sortConfig: SortConfig;
  onSortChange: (sort: SortConfig) => void;
}

// ─── Tag definitions ────────────────────────────────────────────────────────
// Each UI section maps to one or more backend category keys stored in route_tags JSON.
// Backend categories: Route Style | Crack Climbing | Movement | Logistics | Safety | Quality

/** A single selectable tag option shown in the UI. */
interface TagOption {
  /** Value sent to the filter engine (must match exactly what is stored in route_tags). */
  value: string;
  /** Human-readable label shown to the user. */
  label: string;
  /**
   * When true, selecting this tag EXCLUDES routes that have the underlying tag,
   * rather than including only routes that have it.
   */
  exclude?: boolean;
}

/** A UI filter section: groups one or more backend categories under one accordion. */
interface FilterSection {
  /** Unique key used for expand/collapse state. */
  key: string;
  /** Label shown on the accordion button. */
  label: string;
  /**
   * The backend route_tags category these tags belong to.
   * All tags in a section must share the same backend category so the filter
   * engine can group them correctly.
   */
  backendCategory: string;
  tags: TagOption[];
}

const FILTER_SECTIONS: FilterSection[] = [
  // ── Quality & Crowds ──────────────────────────────────────────────────────
  {
    key: 'quality',
    label: 'Quality & Crowds',
    backendCategory: 'Quality',
    tags: [
      { value: 'classic_route', label: 'Classic route' },
      { value: 'first_in_grade', label: 'Good intro to grade' },
    ],
  },
  // ── Route Style & Angle ───────────────────────────────────────────────────
  {
    key: 'style',
    label: 'Style & Angle',
    backendCategory: 'Route Style',
    tags: [
      { value: 'slab',           label: 'Slab' },
      { value: 'vertical',       label: 'Vertical' },
      { value: 'gentle_overhang',label: 'Gentle overhang' },
      { value: 'steep_roof',     label: 'Steep / Roof' },
      { value: 'tower_climbing', label: 'Tower' },
      { value: 'sporty_trad',    label: 'Sporty trad (face moves)' },
    ],
  },
  // ── Crack Climbing ────────────────────────────────────────────────────────
  {
    key: 'crack',
    label: 'Crack Climbing',
    backendCategory: 'Crack Climbing',
    tags: [
      { value: 'finger',     label: 'Finger' },
      { value: 'thin_hand',  label: 'Thin hand' },
      { value: 'wide_hand',  label: 'Wide hand' },
      { value: 'offwidth',   label: 'Offwidth' },
      { value: 'chimney',    label: 'Chimney' },
      { value: 'layback',    label: 'Layback' },
    ],
  },
  // ── Movement & Holds ─────────────────────────────────────────────────────
  {
    key: 'movement',
    label: 'Movement & Holds',
    backendCategory: 'Movement',
    tags: [
      { value: 'technical_moves',   label: 'Technical / Sequency' },
      { value: 'pumpy_sustained',   label: 'Pumpy / Sustained' },
      { value: 'powerful_bouldery', label: 'Powerful / Bouldery' },
      { value: 'dynamic_moves',     label: 'Dynamic moves' },
      { value: 'reachy',            label: 'Reachy (tall climber advantage)' },
      { value: 'small_edges',       label: 'Small edges / Crimps' },
      { value: 'pockets_holes',     label: 'Pockets' },
      { value: 'slopey_holds',      label: 'Slopers' },
    ],
  },
  // ── Pitches & Descent ─────────────────────────────────────────────────────
  // Logistics tags: single_pitch / multi_pitch + anchor / descent info
  {
    key: 'logistics',
    label: 'Pitches & Descent',
    backendCategory: 'Logistics',
    tags: [
      { value: 'single_pitch',  label: 'Single pitch' },
      { value: 'multi_pitch',   label: 'Multi-pitch' },
      { value: 'bolted_anchor', label: 'Bolted anchor (TR-friendly)' },
      { value: 'walk_off',      label: 'Walk-off descent' },
      { value: 'tricky_rappel', label: 'Tricky rappel' },
    ],
  },
  // ── Rope Length ──────────────────────────────────────────────────────────
  // Separate section because filters are mutually exclusive in practice
  {
    key: 'rope',
    label: 'Rope Length Needed',
    backendCategory: 'Logistics',
    tags: [
      { value: 'rope_60m', label: '60 m is enough' },
      { value: 'rope_70m', label: '70 m minimum' },
      { value: 'rope_80m', label: '80 m minimum' },
    ],
  },
  // ── Hazards ───────────────────────────────────────────────────────────────
  // Safety tags; "exclude_*" options filter OUT routes with that tag.
  {
    key: 'hazards',
    label: 'Hazards & Conditions',
    backendCategory: 'Safety',
    tags: [
      { value: 'stick_clip',         label: 'Stick-clip recommended' },
      { value: 'loose_rock',         label: 'Loose rock' },
      { value: 'rope_drag_warning',  label: 'Rope drag warning' },
      { value: 'seasonal_closure',   label: 'Seasonal closure' },
      { value: 'runout_dangerous',   label: 'Runout / Dangerous (PG13+)', exclude: true },
      { value: 'sandbag',            label: 'Sandbag (avoid under-graded)', exclude: true },
    ],
  },
]

// ─── Grade System Picker data ────────────────────────────────────────────────

const GRADE_SYSTEMS: { value: GradeSystem; label: string }[] = [
  { value: 'yds', label: 'YDS' },
  { value: 'boulder', label: 'V' },
  { value: 'aid', label: 'Aid' },
  { value: 'ice', label: 'Ice' },
  { value: 'mixed', label: 'Mixed' },
];

// ─── Component ──────────────────────────────────────────────────────────────

export function FilterPanel({ filters, onChange, sortConfig, onSortChange }: FilterPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [gradeFilterEnabled, setGradeFilterEnabled] = useState(false)

  // ── helpers ──────────────────────────────────────────────────────────────

  const toggleSection = (key: string) =>
    setExpandedSections(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  /**
   * Count how many tags are active in a given filter section.
   * Used to show a badge so users can see active filters at a glance.
   */
  const activeCountForSection = (section: FilterSection): number => {
    const entry = filters.tags.find(t => t.category === section.backendCategory)
    if (!entry) return 0
    return entry.selectedTags.filter(t =>
      section.tags.some(opt => opt.value === t)
    ).length
  }

  /**
   * Total active tag count across all sections (for a summary badge).
   */
  const totalActiveTagCount = useMemo(() =>
    FILTER_SECTIONS.reduce((sum, s) => sum + activeCountForSection(s), 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filters.tags]
  )

  const isTagSelected = (backendCategory: string, value: string): boolean =>
    filters.tags.some(t =>
      t.category === backendCategory && t.selectedTags.includes(value)
    )

  const toggleTag = (backendCategory: string, value: string) => {
    const existing = filters.tags.find(t => t.category === backendCategory)
    const currentSelected = existing?.selectedTags ?? []
    const newSelected = currentSelected.includes(value)
      ? currentSelected.filter(v => v !== value)
      : [...currentSelected, value]

    const newTags = filters.tags
      .filter(t => t.category !== backendCategory)
      .concat(newSelected.length ? [{ category: backendCategory, selectedTags: newSelected }] : [])

    onChange({ ...filters, tags: newTags })
  }

  const updateGradeRange = (range: GradeRange) =>
    onChange({ ...filters, grades: range })

  const handleGradeSystemChange = (newSystem: GradeSystem) => {
    setGradeFilterEnabled(false);
    // Reset grades.min/max to empty — prevents stale values from previous system reaching API (RESEARCH Pitfall 2)
    onChange({ ...filters, gradeSystem: newSystem, grades: { min: '', max: '' } });
  };

  // ── render helpers ────────────────────────────────────────────────────────

  const renderSection = (section: FilterSection) => {
    const isOpen = expandedSections.has(section.key)
    const activeCount = activeCountForSection(section)

    return (
      <div key={section.key} className="filter-group">
        <button
          className="w-full flex justify-between items-center py-1.5 px-2.5 bg-gray-100 rounded text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          onClick={() => toggleSection(section.key)}
          aria-expanded={isOpen}
        >
          <span className="flex items-center gap-1.5">
            {section.label}
            {activeCount > 0 && (
              <span className="inline-flex items-center justify-center w-4 h-4 text-xs font-bold rounded-full bg-blue-500 text-white leading-none">
                {activeCount}
              </span>
            )}
          </span>
          <span className="text-xs opacity-60">{isOpen ? '▼' : '▶'}</span>
        </button>

        {isOpen && (
          <div className="mt-1 space-y-1 pl-2.5 text-gray-700 dark:text-gray-300">
            {section.tags.map(({ value, label, exclude }) => {
              const checked = isTagSelected(section.backendCategory, value)
              return (
                <label
                  key={value}
                  className="flex items-center gap-1.5 cursor-pointer select-none hover:text-gray-900 dark:hover:text-gray-100"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleTag(section.backendCategory, value)}
                    className="flex-shrink-0"
                  />
                  <span className={exclude ? 'text-red-600 dark:text-red-400' : ''}>
                    {label}
                  </span>
                </label>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  // ── main render ───────────────────────────────────────────────────────────

  return (
    <div className="space-y-2.5 p-2.5 bg-white dark:bg-gray-800 rounded-lg shadow text-sm overflow-y-auto max-h-[calc(100vh-120px)]">

      {/* Sort */}
      <div className="filter-group">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap">Sort by</h3>
          <select
            value={sortConfig.option}
            onChange={(e) => onSortChange({ ...sortConfig, option: e.target.value as SortOption })}
            className="flex-1 p-1.5 border rounded text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
          >
            <option value="grade">Grade</option>
            <option value="stars">Stars</option>
            <option value="votes"># of Votes</option>
            <option value="left_to_right">Left to Right</option>
          </select>
          <label className="flex items-center text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
            <input
              type="checkbox"
              checked={sortConfig.ascending}
              onChange={() => onSortChange({ ...sortConfig, ascending: !sortConfig.ascending })}
              className="mr-1.5"
            />
            Reverse
          </label>
        </div>
      </div>

      {/* Route Type */}
      <div className="filter-group">
        <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">Type</h3>
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-gray-700 dark:text-gray-300">
          {ROUTE_TYPES.map(type => (
            <label key={type} className="flex items-center gap-1.5 text-sm cursor-pointer select-none">
              <input
                type="checkbox"
                checked={filters.types.includes(type)}
                onChange={(e) => {
                  const next = e.target.checked
                    ? [...filters.types, type]
                    : filters.types.filter(t => t !== type)
                  onChange({ ...filters, types: next })
                }}
                className="mr-0.5"
              />
              {ROUTE_TYPE_LABELS[type]}
            </label>
          ))}
        </div>
      </div>

      {/* Grade System — dedicated top-level row, above Grade Filter (D-01, D-02) */}
      <div className="filter-group">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 dark:text-gray-100 whitespace-nowrap text-sm">
            Grade System
          </h3>
          <div className="flex flex-1 gap-1 min-w-0" role="group" aria-label="Grade System">
            {GRADE_SYSTEMS.map(({ value, label }) => {
              const isActive = filters.gradeSystem === value;
              return (
                <button
                  key={value}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => handleGradeSystemChange(value)}
                  className={`flex-1 py-2 px-1 text-sm font-medium rounded border transition-colors whitespace-nowrap overflow-hidden text-ellipsis ${
                    isActive
                      ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:text-white dark:border-blue-600'
                      : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Grade Filter */}
      <div className="filter-group">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 dark:text-gray-100">Grade Filter</h3>
          <input
            type="checkbox"
            checked={gradeFilterEnabled}
            onChange={(e) => {
              setGradeFilterEnabled(e.target.checked)
              onChange({
                ...filters,
                grades: e.target.checked ? { min: '5.10a', max: '5.11a' } : { min: '', max: '' },
              })
            }}
          />
        </div>

        {gradeFilterEnabled && (
          <div className="mt-1.5 space-y-1 text-gray-700 dark:text-gray-300">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-0.5">Min Grade</label>
                <select
                  value={filters.grades.min}
                  onChange={(e) => updateGradeRange({
                    ...filters.grades,
                    min: e.target.value,
                    max: GRADE_ORDER.indexOf(e.target.value) <= GRADE_ORDER.indexOf(filters.grades.max)
                      ? filters.grades.max
                      : e.target.value,
                  })}
                  className="w-full p-1.5 border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                >
                  {SIMPLE_GRADES.map(grade => <option key={grade} value={grade}>{grade}</option>)}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium mb-0.5">Max Grade</label>
                <select
                  value={filters.grades.max}
                  onChange={(e) => updateGradeRange({
                    ...filters.grades,
                    max: e.target.value,
                    min: GRADE_ORDER.indexOf(e.target.value) >= GRADE_ORDER.indexOf(filters.grades.min)
                      ? filters.grades.min
                      : e.target.value,
                  })}
                  className="w-full p-1.5 border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
                >
                  {SIMPLE_GRADES.map(grade => <option key={grade} value={grade}>{grade}</option>)}
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="border-t pt-2.5 border-gray-200 dark:border-gray-700">
        <h3 className="font-medium mb-1.5 text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
          Tags
          {totalActiveTagCount > 0 && (
            <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold rounded-full bg-blue-500 text-white leading-none">
              {totalActiveTagCount}
            </span>
          )}
        </h3>
        <div className="space-y-1.5">
          {FILTER_SECTIONS.map(renderSection)}
        </div>
      </div>

    </div>
  )
}
