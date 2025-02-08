# Awesome Search for Mountain Project

I’ve been passionate about rock climbing for over ten years, practicing trad, sport, and bouldering. While there are many incredible routes, information is scattered across websites and guidebooks, making searches difficult. This project aims to centralize route data and apply proper tags, enabling climbers to find routes quickly and efficiently with a simple web application.

## Search Scenarios

This is a comprehensive list of search criteria for trad, sport and their areas. Data availability remains a challenge for many tags. Bouldering requires a separate set of search criteria.

| Category | Search Criterion | Tag Name | Trad Route | Sport Route | Area |
|----------|-----------------|----------|------------|------------|------|
| **Weather & Conditions** | **Sun Aspect (AM)** (morning sun exposure) | `sun_am` | ✅ | ✅ | ✅ |
| | **Sun Aspect (PM)** (afternoon sun exposure) | `sun_pm` | ✅ | ✅ | ✅ |
| | **Tree-filtered sun (AM)** (partial morning sun through trees) | `tree_filtered_sun_am` | ✅ | ✅ | ✅ |
| | **Tree-filtered sun (PM)** (partial afternoon sun through trees) | `tree_filtered_sun_pm` | ✅ | ✅ | ✅ |
| | **Sunny most of the day** | `sunny_all_day` | ✅ | ✅ | ✅ |
| | **Shady most of the day** | `shady_all_day` | ✅ | ✅ | ✅ |
| | **Crag dries fast** (good after rain) | `dries_fast` | ✅ | ✅ | ✅ |
| | **Dry in the rain** (stays climbable in light rain) | `dry_in_rain` | ✅ | ✅ | ✅ |
| | **Seepage is a problem** (routes affected by water seepage) | `seepage_problem` | ✅ | ✅ | ✅ |
| | **Windy and exposed** (routes frequently hit by strong winds) | `windy_exposed` | ✅ | ✅ | ✅ |
| **Access & Restrictions** | **Seasonal closure** (due to raptor nesting or wildlife protection) | `seasonal_closure` | ✅ | ✅ | ✅ |
| **Crowds & Popularity** | **Less crowded areas** (avoid high-traffic crags) | `low_crowds` | ✅ | ✅ | ✅ |
| | **Classic routes** (highly-rated, must-do climbs) | `classic_route` | ✅ | ✅ | ✅ |
| | **Development date** (to find newly established routes) | `new_routes` | ✅ | ✅ | ✅ |
| | **Polished rock** (rock has become smooth due to frequent traffic) | `polished_rock` | ✅ | ✅ | ❌ |
| **Difficulty & Safety** | **Good for breaking into a new grade** (first route in a harder grade) | `first_in_grade` | ✅ | ✅ | ❌ |
| | **Runout, dangerous** (long distances between protection) | `runout_dangerous` | ✅ | ✅ | ❌ |
| | **Stick clip advised** (high first bolt or risk of ground fall) | `stick_clip` | ❌ | ✅ | ❌ |
| | **Watch for loose rock** (routes with potential rockfall hazards) | `loose_rock` | ✅ | ✅ | ❌ |
| | **Rope drag warning** (zig-zagging route that requires careful rope management) | `rope_drag_warning` | ✅ | ✅ | ❌ |
| **Approach & Accessibility** | **No approach (<5 min)** | `approach_none` | ✅ | ✅ | ✅ |
| | **Short approach (<30 min)** | `approach_short` | ✅ | ✅ | ✅ |
| | **Moderate approach (30-60 min)** | `approach_moderate` | ✅ | ✅ | ✅ |
| | **Long approach (>60 min)** | `approach_long` | ✅ | ✅ | ✅ |
| | **Can be top-roped** (accessible from above) | `top_rope_possible` | ✅ | ✅ | ❌ |
| **Multi-Pitch, Anchors & Descent** | **Short multi-pitch (≤5 pitches)** | `short_multipitch` | ✅ | ✅ | ❌ |
| | **Long multi-pitch (>5 pitches)** | `long_multipitch` | ✅ | ✅ | ❌ |
| | **Bolted anchor** (fixed anchors at the top) | `bolted_anchor` | ✅ | ✅ | ❌ |
| | **Gear anchor** (trad routes requiring gear for anchors) | `gear_anchor` | ✅ | ❌ | ❌ |
| | **Walk-off descent** (hike down from top) | `walk_off` | ✅ | ✅ | ❌ |
| | **Rappel descent** (requires rappelling) | `rappel_down` | ✅ | ✅ | ❌ |
| **Route Style & Angle** | **Slabby** (thin footwork, delicate movement) | `slab` | ✅ | ✅ | ❌ |
| | **Vertical** (near-vertical face climbing) | `vertical` | ✅ | ✅ | ❌ |
| | **Gently overhanging** (mildly steep climbing) | `gentle_overhang` | ✅ | ✅ | ❌ |
| | **Steep** (physically demanding, pumpy routes) | `steep` | ✅ | ✅ | ❌ |
| | **Tower climbing** (freestanding towers like Castleton Tower) | `tower_climbing` | ✅ | ✅ | ❌ |
| | **Sporty trad** (trad protection, but climbs like a sport route) | `sporty_trad` | ✅ | ❌ | ❌ |
| **Crack Climbing** | **Finger-tip crack** (thin cracks requiring finger tips) | `finger_tip` | ✅ | ❌ | ❌ |
| | **Finger crack** (slightly wider than finger-tip, full finger fits) | `finger` | ✅ | ❌ | ❌ |
| | **Narrow hand crack** (tight hand jams) | `narrow_hand` | ✅ | ❌ | ❌ |
| | **Wide hand crack** (comfortable hand jams, full fist) | `wide_hand` | ✅ | ❌ | ❌ |
| | **Offwidth** (too wide for hands, but not a full chimney) | `offwidth` | ✅ | ❌ | ❌ |
| | **Chimney** (wide cracks where the whole body fits) | `chimney` | ✅ | ❌ | ❌ |
| **Hold & Movement Type** | **Reachy, best if tall** (better suited for taller climbers) | `reachy` | ✅ | ✅ | ❌ |
| | **Dynamic moves** (big movement, explosive climbing) | `dynamic_moves` | ✅ | ✅ | ❌ |
| | **Pumpy or sustained** (endurance-based routes) | `pumpy_sustained` | ✅ | ✅ | ❌ |
| | **Technical moves** (requires precise footwork and body positioning) | `technical_moves` | ✅ | ✅ | ❌ |
| | **Powerful or bouldery** (strength-focused movement) | `powerful_bouldery` | ✅ | ✅ | ❌ |
| | **Pockets and holes** (routes featuring pockets as primary holds) | `pockets_holes` | ✅ | ✅ | ❌ |
| | **Small edges** (crimp-intensive climbing) | `small_edges` | ✅ | ✅ | ❌ |
| | **Slopey holds** (requires compression and body tension) | `slopey_holds` | ✅ | ✅ | ❌ |
| **Rope Length** | **Requires 70m rope** | `rope_70m` | ✅ | ✅ | ❌ |
| | **Requires 80m rope** | `rope_80m` | ✅ | ✅ | ❌ |

## Phase one


1. Scrape areas, routes and their detail information from Mtnpj (done)
1. Scrape data from a guidebook if it is possible. (ambistious, Squamish is relatively easy)
1. Add requird tag information using LLM using area description, route description, comments.
1. Store all data in json or SQL.Store all data in json or SQL.

### Front End
TBD

## Schedule

### Phase 1
* Focus on my local crags or to be visited crags: Squamish, Index, Leavenworth, Indian Creek and Yosemite.
* Focus on high feasibility taggings: crack climbing, multi-pitch/anchors/descent.S