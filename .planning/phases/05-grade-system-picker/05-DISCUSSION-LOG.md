# Phase 05: Grade System Picker — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-16
**Phase:** 05-grade-system-picker
**Areas discussed:** Picker control style, Grade filter UX for non-YDS, API filter contract

---

## Picker Location (pre-discussion, user resolved)

| Option | Description | Selected |
|--------|-------------|----------|
| Inside grade accordion | Segmented control at top of existing Grade filter section | |
| Own top-level row | Dedicated row above grade accordion, always visible | ✓ |

**User's choice:** Own top-level row
**Notes:** Answered before formal discuss-phase began — makes grade system choice prominent before opening filters.

---

## Picker Control Style

### Question 1: Visual form factor

| Option | Description | Selected |
|--------|-------------|----------|
| Segmented buttons | 5 horizontal buttons [YDS] [V] [Aid] [Ice] [Mixed] | ✓ |
| Labeled dropdown | 'Grade System: [dropdown]' — saves space, less affordance | |
| Radio pills | Small pill-shaped radio inputs in a row | |

**User's choice:** Segmented buttons

### Question 2: Active/inactive styling

| Option | Description | Selected |
|--------|-------------|----------|
| Filled highlight | Active = solid blue bg-blue-600 text-white; inactive = gray | ✓ |
| Border highlight | Active = blue border + blue text; inactive = borderless | |
| You decide | Claude picks style matching existing UI | |

**User's choice:** Filled highlight

---

## Grade Filter UX for Non-YDS

### Question 1: Filter control type

| Option | Description | Selected |
|--------|-------------|----------|
| Min/max selects (same as YDS) | Replace SIMPLE_GRADES with active system's grade list | ✓ |
| Scrollable checkbox list | Checkboxes for each grade — more flexible, more complex | |
| Min/max selects for all systems | Same as first option (equivalent) | |

**User's choice:** Min/max selects — same UX as YDS, different grade list per system
**Notes:** Todo said "checkboxes" but min/max selects are simpler and sufficient.

### Question 2: Behavior on system switch

| Option | Description | Selected |
|--------|-------------|----------|
| Reset to disabled | Grade filter unchecks; min/max reset | ✓ |
| Keep enabled, reset range | Grade filter stays checked; min/max reset to system extremes | |

**User's choice:** Reset to disabled

---

## API Filter Contract

### Question 1: How to send grade range for non-YDS

| Option | Description | Selected |
|--------|-------------|----------|
| Client expands range → sends grade_list | Client slices grade array, sends grade_list=V4,V5,V6,V7,V8 | ✓ |
| Send grade_system + grade_min_str + grade_max_str | Server holds grade arrays and expands range | |

**User's choice:** Client expands range, sends comma-separated grade_list

### Question 2: Aid grade column coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Both columns (route_grade + route_protection_grading) | Catches more routes; aid/mixed grades appear in both | ✓ |
| route_grade only | Simpler SQL; misses some routes | |

**User's choice:** Both columns — applies to Aid and Mixed; Ice and Boulder filter route_grade only

---

## Claude's Discretion

- Exact handling of dual-scale systems in min/max selects (A-vs-C for Aid, WI-vs-AI for Ice) — show A/WI labels in selects, LIKE catches both variants
- Dark mode class names for segmented buttons
- Label truncation if buttons overflow on narrow viewports

## Deferred Ideas

- Snow grade sorting (no numeric scale in DB)
- Alpine/commitment grade sorting (NCCS grades)
- Conditional sort options based on active type filter
- Tooltip/helper text for null-last behavior
