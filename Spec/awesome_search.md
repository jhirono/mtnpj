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
| **Crowds & Popularity** | **Less crowded areas** (avoid high-traffic crags) | `low_crowds` | ✅ | ✅ | ✅ |
| | **Classic routes** (highly-rated, must-do climbs) | `classic_route` | ✅ | ✅ | ✅ |
| | **Development date** (to find newly established routes) | `new_routes` | ✅ | ✅ | ✅ |
| | **Polished rock** (rock has become smooth due to frequent traffic) | `polished_rock` | ✅ | ✅ | ❌ |
| **Difficulty & Safety** | **Good for breaking into a new grade** (first route in a harder grade) | `first_in_grade` | ✅ | ✅ | ❌ |
| | **sandbag** (many felt harder than actual grade) | `sandbag` | ✅ | ✅ | ❌ |
| | **Runout, dangerous** (long distances between protection) | `runout_dangerous` | ✅ | ✅ | ❌ |
| | **Stick clip advised** (high first bolt or risk of ground fall) | `stick_clip` | ❌ | ✅ | ❌ |
| | **Watch for loose rock** (routes with potential rockfall hazards) | `loose_rock` | ✅ | ✅ | ❌ |
| | **Rope drag warning** (zig-zagging route that requires careful rope management) | `rope_drag_warning` | ✅ | ✅ | ❌ |
| **Approach & Accessibility** | **No approach (<5 min)** | `approach_none` | ✅ | ✅ | ✅ |
| | **Short approach (<30 min)** | `approach_short` | ✅ | ✅ | ✅ |
| | **Moderate approach (30-60 min)** | `approach_moderate` | ✅ | ✅ | ✅ |
| | **Long approach (>60 min)** | `approach_long` | ✅ | ✅ | ✅ |
| | **Can be top-roped** (accessible from above) | `top_rope_possible` | ✅ | ✅ | ❌ |
| | **Seasonal closure** (due to raptor nesting or wildlife protection) | `seasonal_closure` | ✅ | ✅ | ✅ |
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

## Data Structure

### Scraped from MTNPJ

The JSON output produced by the scraper is an array of area objects. Each area object contains detailed information about a climbing area along with an array of routes found within that area. Below is a breakdown of the JSON structure and an explanation of each key.

---

#### Area Object

Each area object contains the following fields:

- **area_id**  
  *Type:* String (UUID)  
  *Description:* A unique identifier for the area. This value can serve as a primary key in a SQL database.

- **area_url**  
  *Type:* String  
  *Description:* The URL of the Mountain Project area page from which the data is scraped.

- **area_name**  
  *Type:* String  
  *Description:* A short, slug-based name of the area (for example, "dove-creek-wall").

- **area_gps**  
  *Type:* String (URL)  
  *Description:* A Google Maps URL containing the latitude and longitude of the area. This can be used for mapping or spatial queries.

- **area_description**  
  *Type:* String  
  *Description:* A narrative description of the climbing area, including its features and notable routes.

- **area_getting_there**  
  *Type:* String  
  *Description:* Directions or instructions on how to access the area (e.g., hiking directions or trail information).

- **area_tags**  
  *Type:* Array  
  *Description:* An array reserved for area-specific tags (e.g., weather conditions, exposure, access warnings). This field is initially empty and may be populated later.

- **area_hierarchy**  
  *Type:* Array of Objects  
  *Description:* A breadcrumb hierarchy showing the area's location within larger regions. Each object in the array contains:  
  - **level:** *Type:* Integer  
    *Description:* The hierarchy level (e.g., 1 for top-level, 2 for state or region, etc.).  
  - **area_hierarchy_name:** *Type:* String  
    *Description:* The name of the region or sub-area (e.g., "Utah", "Southeast Utah").  
  - **area_hierarchy_url:** *Type:* String  
    *Description:* The URL corresponding to that hierarchy level.

- **area_access_issues**  
  *Type:* String  
  *Description:* A concatenated string of any access issues or warnings scraped from the area page (such as limited facilities or environmental restrictions).

- **area_page_views**  
  *Type:* String  
  *Description:* The number of page views for the area, as reported by Mountain Project. Although numeric in nature, it is stored as a string.

- **area_shared_on**  
  *Type:* String  
  *Description:* The month and year when the area was shared, formatted as "Mon, YYYY" (for example, "Aug, 2018").

- **area_comments**  
  *Type:* Array of Objects  
  *Description:* A list of user comments about the area. Each comment object includes:  
  - **comment_author:** *Type:* String – The name of the user who commented.  
  - **comment_text:** *Type:* String – The content of the comment.  
  - **comment_time:** *Type:* String – The date the comment was posted.

- **routes**  
  *Type:* Array of Route Objects  
  *Description:* An array of route objects, each representing a climbing route within the area.

---

#### Route Object

Each route object within the "routes" array includes the following fields:

- **route_name**  
  *Type:* String  
  *Description:* The name of the climbing route as displayed on Mountain Project.

- **route_url**  
  *Type:* String  
  *Description:* The URL of the individual route page on Mountain Project.

- **route_grade**  
  *Type:* String  
  *Description:* The official climbing grade, cleaned to remove any extraneous text such as "YDS" (for example, "5.9YDS" becomes "5.9").

- **route_protection_grading**  
  *Type:* String  
  *Description:* The protection grading for the route (for example, "PG13", "R", or "X"). This value is extracted from the same heading that contains the route grade.

- **route_stars**  
  *Type:* Number  
  *Description:* The average star rating of the route.

- **route_votes**  
  *Type:* Number  
  *Description:* The total number of votes or reviews the route has received.

- **route_type**  
  *Type:* String  
  *Description:* The climbing style (e.g., "Trad", "Sport") of the route.

- **route_length_ft**  
  *Type:* Number  
  *Description:* The length of the route in feet. This value is parsed from a combined string (for example, from "70 ft (21 m)").

- **route_length_meter**  
  *Type:* Number  
  *Description:* The length of the route in meters, extracted from the same string as the feet value.

- **route_fa**  
  *Type:* String  
  *Description:* Information about the first ascent (FA) of the route, which may include details such as first free ascent (FFA).

- **route_description**  
  *Type:* String  
  *Description:* A narrative description of the route, including its characteristics, style, and any unique features.

- **route_location**  
  *Type:* String  
  *Description:* Additional location details for the route. If no extra details are provided, this field may be set to "N/A".

- **route_protection**  
  *Type:* String  
  *Description:* Information about the protection gear or style required for the route (for example, which cams or nuts to bring).

- **route_page_views**  
  *Type:* String  
  *Description:* The number of page views for the route, as reported by Mountain Project.

- **route_shared_on**  
  *Type:* String  
  *Description:* The month and year when the route was shared, formatted as "Mon, YYYY" (for example, "Aug, 2006").

- **route_id**  
  *Type:* String (UUID)  
  *Description:* A unique identifier for the route, generated by the scraper.

- **route_tags**  
  *Type:* Array  
  *Description:* Reserved for route-specific tags (e.g., "crack climbing", "sunny", etc.). Initially empty.

- **route_composite_tags**  
  *Type:* Array  
  *Description:* An array for combining route-specific tags with inherited area tags to simplify searching. Initially empty.

- **route_comments**  
  *Type:* Array of Objects  
  *Description:* A list of user comments about the route. Each comment object includes:  
  - **comment_author:** *Type:* String – The name of the commenter.  
  - **comment_text:** *Type:* String – The content of the comment.  
  - **comment_time:** *Type:* String – The date the comment was posted.

- **route_suggested_ratings**  
  *Type:* Object  
  *Description:* A dictionary where each key is a suggested grade (for example, "5.9", "5.10b PG13") provided by climbers, and the value is the number of votes for that grade. This data can be used to compare the climbers’ input with the official grade and infer if the route is considered soft or hard.

- **route_tick_comments**  
  *Type:* String  
  *Description:* A concatenated string of user “tick” comments (feedback such as "Lead / Onsight", "TR", etc.). The text is cleaned to remove date patterns and bullet characters so that only descriptive feedback remains.

---

### Scanned from guidebooks

Placeholder. Low priority.

## Tagging

### Tagging json

```json
{
  "tags": [
    {
      "category": "Weather & Conditions",
      "tags": [
        {
          "tag": "sun_am",
          "description": "Morning sun exposure"
        },
        {
          "tag": "sun_pm",
          "description": "Afternoon sun exposure"
        },
        {
          "tag": "tree_filtered_sun_am",
          "description": "Partial morning sun through trees"
        },
        {
          "tag": "tree_filtered_sun_pm",
          "description": "Partial afternoon sun through trees"
        },
        {
          "tag": "sunny_all_day",
          "description": "Sunny most of the day"
        },
        {
          "tag": "shady_all_day",
          "description": "Shady most of the day"
        },
        {
          "tag": "dries_fast",
          "description": "Crag dries fast after rain"
        },
        {
          "tag": "dry_in_rain",
          "description": "Stays climbable in light rain"
        },
        {
          "tag": "seepage_problem",
          "description": "Affected by water seepage"
        },
        {
          "tag": "windy_exposed",
          "description": "Exposed to strong winds"
        }
      ]
    },
    {
      "category": "Access & Restrictions",
      "tags": [
        {
          "tag": "seasonal_closure",
          "description": "Seasonal closure due to wildlife or nesting"
        }
      ]
    },
    {
      "category": "Crowds & Popularity",
      "tags": [
        {
          "tag": "low_crowds",
          "description": "Less crowded area"
        },
        {
          "tag": "classic_route",
          "description": "Classic, must-do climb"
        },
        {
          "tag": "new_routes",
          "description": "Newly established routes"
        },
        {
          "tag": "polished_rock",
          "description": "Rock that is polished from frequent use"
        }
      ]
    },
    {
      "category": "Difficulty & Safety",
      "tags": [
        {
          "tag": "first_in_grade",
          "description": "Good for breaking into a new grade"
        },
        {
          "tag": "sandbag",
          "description": "Route perceived as harder than its official grade"
        },
        {
          "tag": "runout_dangerous",
          "description": "Long distances between protection"
        },
        {
          "tag": "stick_clip",
          "description": "High first bolt or risk of ground fall (typically for sport routes)"
        },
        {
          "tag": "loose_rock",
          "description": "Potential rockfall hazards"
        },
        {
          "tag": "rope_drag_warning",
          "description": "Requires careful rope management"
        }
      ]
    },
    {
      "category": "Approach & Accessibility",
      "tags": [
        {
          "tag": "approach_none",
          "description": "No approach required (<5 min)"
        },
        {
          "tag": "approach_short",
          "description": "Short approach (<30 min)"
        },
        {
          "tag": "approach_moderate",
          "description": "Moderate approach (30–60 min)"
        },
        {
          "tag": "approach_long",
          "description": "Long approach (>60 min)"
        },
        {
          "tag": "top_rope_possible",
          "description": "Route can be top-roped from above"
        }
      ]
    },
    {
      "category": "Multi-Pitch, Anchors & Descent",
      "tags": [
        {
          "tag": "short_multipitch",
          "description": "Short multi-pitch (≤5 pitches)"
        },
        {
          "tag": "long_multipitch",
          "description": "Long multi-pitch (>5 pitches)"
        },
        {
          "tag": "bolted_anchor",
          "description": "Fixed anchors at the top"
        },
        {
          "tag": "gear_anchor",
          "description": "Trad routes requiring gear for anchors"
        },
        {
          "tag": "walk_off",
          "description": "Route with a walk-off descent"
        },
        {
          "tag": "rappel_down",
          "description": "Requires rappelling"
        }
      ]
    },
    {
      "category": "Route Style & Angle",
      "tags": [
        {
          "tag": "slab",
          "description": "Thin footwork with delicate movement"
        },
        {
          "tag": "vertical",
          "description": "Near-vertical face climbing"
        },
        {
          "tag": "gentle_overhang",
          "description": "Mildly steep climbing"
        },
        {
          "tag": "steep",
          "description": "Physically demanding, pumpy route"
        },
        {
          "tag": "tower_climbing",
          "description": "Freestanding tower climbs"
        },
        {
          "tag": "sporty_trad",
          "description": "Trad route that climbs like a sport route"
        }
      ]
    },
    {
      "category": "Crack Climbing",
      "tags": [
        {
          "tag": "finger_tip",
          "description": "Thin cracks requiring fingertip protection"
        },
        {
          "tag": "finger",
          "description": "Cracks slightly wider than fingertip size"
        },
        {
          "tag": "narrow_hand",
          "description": "Tight hand jams"
        },
        {
          "tag": "wide_hand",
          "description": "Comfortable hand jams (full fist)"
        },
        {
          "tag": "offwidth",
          "description": "Cracks too wide for hands but not a full chimney"
        },
        {
          "tag": "chimney",
          "description": "Wide cracks where the whole body fits"
        }
      ]
    },
    {
      "category": "Hold & Movement Type",
      "tags": [
        {
          "tag": "reachy",
          "description": "Better suited for taller climbers"
        },
        {
          "tag": "dynamic_moves",
          "description": "Explosive, dynamic movements"
        },
        {
          "tag": "pumpy_sustained",
          "description": "Endurance-based, pumpy route"
        },
        {
          "tag": "technical_moves",
          "description": "Requires precise footwork and body positioning"
        },
        {
          "tag": "powerful_bouldery",
          "description": "Strength-focused movement"
        },
        {
          "tag": "pockets_holes",
          "description": "Features pockets as primary holds"
        },
        {
          "tag": "small_edges",
          "description": "Crimp-intensive climbing"
        },
        {
          "tag": "slopey_holds",
          "description": "Requires compression and body tension"
        }
      ]
    },
    {
      "category": "Rope Length",
      "tags": [
        {
          "tag": "rope_70m",
          "description": "Requires 70m rope"
        },
        {
          "tag": "rope_80m",
          "description": "Requires 80m rope"
        }
      ]
    }
  ]
}

```





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
* Focus on high feasibility taggings: crack climbing, multi-pitch/anchors/descent