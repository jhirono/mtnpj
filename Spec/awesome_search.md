# Awesome Search for Mountain Project

I've been passionate about rock climbing for over ten years, practicing trad, sport, and bouldering. While there are many incredible routes, information is scattered across websites and guidebooks, making searches difficult. This project aims to centralize route data and apply proper tags, enabling climbers to find routes quickly and efficiently with a simple web application.

## Search Scenarios

This is a comprehensive list of search criteria for trad, sport and their areas. Data availability remains a challenge for many tags. Bouldering requires a separate set of search criteria.

| Category | Search Criterion | Tag Name | Trad Route | Sport Route | Area |
|----------|-----------------|----------|------------|------------|------|
| Weather & Conditions | Sun Aspect (AM) (morning sun exposure) | `sun_am` | ✅ | ✅ | ✅ |
| | Sun Aspect (PM) (afternoon sun exposure) | `sun_pm` | ✅ | ✅ | ✅ |
| | Tree-filtered sun (AM) (partial morning sun through trees) | `tree_filtered_sun_am` | ✅ | ✅ | ✅ |
| | Tree-filtered sun (PM) (partial afternoon sun through trees) | `tree_filtered_sun_pm` | ✅ | ✅ | ✅ |
| | Sunny most of the day | `sunny_all_day` | ✅ | ✅ | ✅ |
| | Shady most of the day | `shady_all_day` | ✅ | ✅ | ✅ |
| | Crag dries fast (good after rain) | `dries_fast` | ✅ | ✅ | ✅ |
| | Dry in the rain (stays climbable in light rain) | `dry_in_rain` | ✅ | ✅ | ✅ |
| | Seepage is a problem (routes affected by water seepage) | `seepage_problem` | ✅ | ✅ | ✅ |
| | Windy and exposed (routes frequently hit by strong winds) | `windy_exposed` | ✅ | ✅ | ✅ |
| Crowds & Popularity | Less crowded areas (avoid high-traffic crags) | `low_crowds` | ✅ | ✅ | ✅ |
| | Classic routes (highly-rated, must-do climbs) | `classic_route` | ✅ | ✅ | ✅ |
| | Development date (to find newly established routes) | `new_routes` | ✅ | ✅ | ✅ |
| | Polished rock (rock has become smooth due to frequent traffic) | `polished_rock` | ✅ | ✅ | ❌ |
| Difficulty & Safety | Good for breaking into a new grade (first route in a harder grade) | `first_in_grade` | ✅ | ✅ | ❌ |
| | sandbag (many felt harder than actual grade) | `sandbag` | ✅ | ✅ | ❌ |
| | Runout, dangerous (long distances between protection) | `runout_dangerous` | ✅ | ✅ | ❌ |
| | Stick clip advised (high first bolt or risk of ground fall) | `stick_clip` | ❌ | ✅ | ❌ |
| | Watch for loose rock (routes with potential rockfall hazards) | `loose_rock` | ✅ | ✅ | ❌ |
| | Rope drag warning (zig-zagging route that requires careful rope management) | `rope_drag_warning` | ✅ | ✅ | ❌ |
| Approach & Accessibility | No approach (<5 min) | `approach_none` | ✅ | ✅ | ✅ |
| | Short approach (<30 min) | `approach_short` | ✅ | ✅ | ✅ |
| | Moderate approach (30-60 min) | `approach_moderate` | ✅ | ✅ | ✅ |
| | Long approach (>60 min) | `approach_long` | ✅ | ✅ | ✅ |
| | Can be top-roped (accessible from above) | `top_rope_possible` | ✅ | ✅ | ❌ |
| | Seasonal closure (due to raptor nesting or wildlife protection) | `seasonal_closure` | ✅ | ✅ | ✅ |
| Multi-Pitch, Anchors & Descent | Short multi-pitch (≤5 pitches) | `short_multipitch` | ✅ | ✅ | ❌ |
| | Long multi-pitch (>5 pitches) | `long_multipitch` | ✅ | ✅ | ❌ |
| | Bolted anchor (fixed anchors at the top) | `bolted_anchor` | ✅ | ✅ | ❌ |
| | Gear anchor (trad routes requiring gear for anchors) | `gear_anchor` | ✅ | ❌ | ❌ |
| | Walk-off descent (hike down from top) | `walk_off` | ✅ | ✅ | ❌ |
| | Rappel descent (requires rappelling) | `rappel_down` | ✅ | ✅ | ❌ |
| Route Style & Angle | Slabby (thin footwork, delicate movement) | `slab` | ✅ | ✅ | ❌ |
| | Vertical (near-vertical face climbing) | `vertical` | ✅ | ✅ | ❌ |
| | Gently overhanging (mildly steep climbing) | `gentle_overhang` | ✅ | ✅ | ❌ |
| | Steep (physically demanding, pumpy routes) | `steep` | ✅ | ✅ | ❌ |
| | Tower climbing (freestanding towers like Castleton Tower) | `tower_climbing` | ✅ | ✅ | ❌ |
| | Sporty trad (trad protection, but climbs like a sport route) | `sporty_trad` | ✅ | ❌ | ❌ |
| Crack Climbing | Finger-tip crack (thin cracks requiring finger tips) | `finger_tip` | ✅ | ❌ | ❌ |
| | Finger crack (slightly wider than finger-tip, full finger fits) | `finger` | ✅ | ❌ | ❌ |
| | Narrow hand crack (tight hand jams) | `narrow_hand` | ✅ | ❌ | ❌ |
| | Wide hand crack (comfortable hand jams, full fist) | `wide_hand` | ✅ | ❌ | ❌ |
| | Offwidth (too wide for hands, but not a full chimney) | `offwidth` | ✅ | ❌ | ❌ |
| | Chimney (wide cracks where the whole body fits) | `chimney` | ✅ | ❌ | ❌ |
| Hold & Movement Type | Reachy, best if tall (better suited for taller climbers) | `reachy` | ✅ | ✅ | ❌ |
| | Dynamic moves (big movement, explosive climbing) | `dynamic_moves` | ✅ | ✅ | ❌ |
| | Pumpy or sustained (endurance-based routes) | `pumpy_sustained` | ✅ | ✅ | ❌ |
| | Technical moves (requires precise footwork and body positioning) | `technical_moves` | ✅ | ✅ | ❌ |
| | Powerful or bouldery (strength-focused movement) | `powerful_bouldery` | ✅ | ✅ | ❌ |
| | Pockets and holes (routes featuring pockets as primary holds) | `pockets_holes` | ✅ | ✅ | ❌ |
| | Small edges (crimp-intensive climbing) | `small_edges` | ✅ | ✅ | ❌ |
| | Slopey holds (requires compression and body tension) | `slopey_holds` | ✅ | ✅ | ❌ |
| Rope Length | Requires 70m rope | `rope_70m` | ✅ | ✅ | ❌ |
| | Requires 80m rope | `rope_80m` | ✅ | ✅ | ❌ |

## Data Structure

### Scraped from MTNPJ

The JSON output produced by the scraper is an array of area objects. Each area object contains detailed information about a climbing area along with an array of routes found within that area. Below is a breakdown of the JSON structure and an explanation of each key.

---

#### Area Object

Each area object contains the following fields:

- area_id  
  *Type:* String (UUID)  
  *Description:* A unique identifier for the area. This value can serve as a primary key in a SQL database.

- area_url  
  *Type:* String  
  *Description:* The URL of the Mountain Project area page from which the data is scraped.

- area_name  
  *Type:* String  
  *Description:* A short, slug-based name of the area (for example, "dove-creek-wall").

- area_gps  
  *Type:* String (URL)  
  *Description:* A Google Maps URL containing the latitude and longitude of the area. This can be used for mapping or spatial queries.

- area_description  
  *Type:* String  
  *Description:* A narrative description of the climbing area, including its features and notable routes.

- area_getting_there  
  *Type:* String  
  *Description:* Directions or instructions on how to access the area (e.g., hiking directions or trail information).

- area_tags  
  *Type:* Array  
  *Description:* An array reserved for area-specific tags (e.g., weather conditions, exposure, access warnings). This field is initially empty and may be populated later.

- area_hierarchy  
  *Type:* Array of Objects  
  *Description:* A breadcrumb hierarchy showing the area's location within larger regions. Each object in the array contains:  
  - level: *Type:* Integer  
    *Description:* The hierarchy level (e.g., 1 for top-level, 2 for state or region, etc.).  
  - area_hierarchy_name: *Type:* String  
    *Description:* The name of the region or sub-area (e.g., "Utah", "Southeast Utah").  
  - area_hierarchy_url: *Type:* String  
    *Description:* The URL corresponding to that hierarchy level.

- area_access_issues  
  *Type:* String  
  *Description:* A concatenated string of any access issues or warnings scraped from the area page (such as limited facilities or environmental restrictions).

- area_page_views  
  *Type:* String  
  *Description:* The number of page views for the area, as reported by Mountain Project. Although numeric in nature, it is stored as a string.

- area_shared_on  
  *Type:* String  
  *Description:* The month and year when the area was shared, formatted as "Mon, YYYY" (for example, "Aug, 2018").

- area_comments  
  *Type:* Array of Objects  
  *Description:* A list of user comments about the area. Each comment object includes:  
  - comment_author: *Type:* String – The name of the user who commented.  
  - comment_text: *Type:* String – The content of the comment.  
  - comment_time: *Type:* String – The date the comment was posted.

- routes  
  *Type:* Array of Route Objects  
  *Description:* An array of route objects, each representing a climbing route within the area.

---

#### Route Object

Each route object within the "routes" array includes the following fields:

- route_name  
  *Type:* String  
  *Description:* The name of the climbing route as displayed on Mountain Project.

- route_url  
  *Type:* String  
  *Description:* The URL of the individual route page on Mountain Project.

- route_lr  
  *Type:* String  
  *Description:* The left-to-right ordering value of the route in the area's route list. Used for maintaining the original route order.

- route_grade  
  *Type:* String  
  *Description:* The official climbing grade, cleaned to remove any extraneous text such as "YDS" (for example, "5.9YDS" becomes "5.9").

- route_protection_grading  
  *Type:* String  
  *Description:* The protection grading for the route (for example, "PG13", "R", or "X"). This value is extracted from the same heading that contains the route grade.

- route_stars  
  *Type:* Number  
  *Description:* The average star rating of the route.

- route_votes  
  *Type:* Number  
  *Description:* The total number of votes or reviews the route has received.

- route_type  
  *Type:* String  
  *Description:* The climbing style (e.g., "Trad", "Sport") of the route.

- route_length_ft  
  *Type:* Number  
  *Description:* The length of the route in feet. This value is parsed from a combined string (for example, from "70 ft (21 m)").

- route_length_meter  
  *Type:* Number  
  *Description:* The length of the route in meters, extracted from the same string as the feet value.

- route_fa  
  *Type:* String  
  *Description:* Information about the first ascent (FA) of the route, which may include details such as first free ascent (FFA).

- route_description  
  *Type:* String  
  *Description:* A narrative description of the route, including its characteristics, style, and any unique features.

- route_location  
  *Type:* String  
  *Description:* Additional location details for the route. If no extra details are provided, this field may be set to "N/A".

- route_protection  
  *Type:* String  
  *Description:* Information about the protection gear or style required for the route (for example, which cams or nuts to bring).

- route_page_views  
  *Type:* String  
  *Description:* The number of page views for the route, as reported by Mountain Project.

- route_shared_on  
  *Type:* String  
  *Description:* The month and year when the route was shared, formatted as "Mon, YYYY" (for example, "Aug, 2006").

- route_id  
  *Type:* String (UUID)  
  *Description:* A unique identifier for the route, generated by the scraper.

- route_tags  
  *Type:* Array  
  *Description:* Reserved for route-specific tags (e.g., "crack climbing", "sunny", etc.). Initially empty.

- route_comments  
  *Type:* Array of Objects  
  *Description:* A list of user comments about the route. Each comment object includes:  
  - comment_author: *Type:* String – The name of the commenter.  
  - comment_text: *Type:* String – The content of the comment.  
  - comment_time: *Type:* String – The date the comment was posted.

- route_suggested_ratings  
  *Type:* Object  
  *Description:* A dictionary where each key is a suggested grade (for example, "5.9", "5.10b PG13") provided by climbers, and the value is the number of votes for that grade. This data can be used to compare the climbers' input with the official grade and infer if the route is considered soft or hard.

- route_tick_comments  
  *Type:* String  
  *Description:* A concatenated string of user "tick" comments (feedback such as "Lead / Onsight", "TR", etc.). The text is cleaned to remove date patterns and bullet characters so that only descriptive feedback remains.

---

### Scanned from guidebooks

Placeholder. Low priority.

## Tagging

### Tagging json

The tagging system consists of both manual tags (derived from numeric data) and LLM tags (derived from text analysis). Here's the complete tag structure:

```json
{
  "tags": [
    {
      "category": "Weather & Conditions",
      "tags": [
        { "tag": "sun_am", "description": "Morning sun exposure or Shaded in the afternoon" },
        { "tag": "sun_pm", "description": "Afternoon sun exposure, or Shaded in the morning" },
        { "tag": "tree_filtered_sun_am", "description": "Partial morning sun through trees" },
        { "tag": "tree_filtered_sun_pm", "description": "Partial afternoon sun through trees" },
        { "tag": "sunny_all_day", "description": "Sunny most of the day" },
        { "tag": "shady_all_day", "description": "Shady most of the day" },
        { "tag": "dries_fast", "description": "Crag dries fast after rain" },
        { "tag": "dry_in_rain", "description": "Stays climbable in light rain" },
        { "tag": "seepage_problem", "description": "Affected by water seepage" },
        { "tag": "windy_exposed", "description": "Exposed to strong winds" }
      ]
    },
    {
      "category": "Access & Restrictions",
      "tags": [
        { "tag": "seasonal_closure", "description": "Seasonal closure due to wildlife or nesting or wet rock of sand stone" }
      ]
    },
    {
      "category": "Crowds & Popularity",
      "tags": [
        { "tag": "low_crowds", "description": "Less crowded area or route" },
        { "tag": "classic_route", "description": "If route stars >= 3 and route votes >= 5" },        
        { "tag": "new_routes", "description": "If route was shared after January 2022" },
        { "tag": "new_areas", "description": "If area was shared after January 2022" },
        { "tag": "polished_rock", "description": "Rock polished from frequent use" }
      ]
    },
    {
      "category": "Difficulty & Safety",
      "tags": [
        { "tag": "first_in_grade", "description": "If lower grade votes > higher grade votes (min 5 votes)" },
        { "tag": "sandbag", "description": "If higher grade votes > official grade votes (min 5 votes)" },
        { "tag": "runout_dangerous", "description": "If route_protection_grading contains PG13, R, or X" },
        { "tag": "stick_clip", "description": "High first bolt or risk of ground fall (sport routes only)" },
        { "tag": "loose_rock", "description": "Potential rockfall hazards" },
        { "tag": "rope_drag_warning", "description": "Requires careful rope management" }
      ]
    },
    {
      "category": "Approach & Accessibility",
      "tags": [
        { "tag": "approach_none", "description": "No approach required (<5 min) from parking" },
        { "tag": "approach_short", "description": "Short approach (<30 min) from parking" },
        { "tag": "approach_moderate", "description": "Moderate approach (30–60 min) from parking" },
        { "tag": "approach_long", "description": "Long approach (>60 min) from parking" },
        { "tag": "top_rope_possible", "description": "Anchor accessible without rope climbing" }
      ]
    },
    {
      "category": "Multi-Pitch, Anchors & Descent",
      "tags": [
        { "tag": "short_multipitch", "description": "If 1 < route_pitches < 5" },
        { "tag": "long_multipitch", "description": "If route_pitches >= 5" },
        { "tag": "bolted_anchor", "description": "Fixed anchors at the top" },
        { "tag": "walk_off", "description": "Route with a walk-off descent" },
        { "tag": "rappel_down", "description": "Requires rappelling" }
      ]
    },
    {
      "category": "Route Style & Angle",
      "tags": [
        { "tag": "slab", "description": "Thin footwork with delicate movement" },
        { "tag": "vertical", "description": "Near-vertical face climbing" },
        { "tag": "gentle_overhang", "description": "Mildly steep climbing, 90-110 degrees" },
        { "tag": "steep_roof", "description": "Extremely steep section >110 degrees" },
        { "tag": "tower_climbing", "description": "Freestanding tower climbs" },
        { "tag": "sporty_trad", "description": "Trad route with sport-style climbing" }
      ]
    },
    {
      "category": "Crack Climbing",
      "tags": [
        { "tag": "finger_tip", "description": "Ultra-thin cracks (≤0.5 inches)" },
        { "tag": "finger", "description": "Cracks around 0.5–0.75 inches" },
        { "tag": "thin_hand", "description": "Very tight hand jams" },
        { "tag": "wide_hand", "description": "Spacious hand jams" },
        { "tag": "offwidth", "description": "Too wide for hands, not full chimney" },
        { "tag": "chimney", "description": "Wide cracks where body fits" },
        { "tag": "layback", "description": "Leaning off crack with opposing feet" }
      ]
    },
    {
      "category": "Hold & Movement Type",
      "tags": [
        { "tag": "reachy", "description": "Better suited for taller climbers" },
        { "tag": "dynamic_moves", "description": "Explosive, dynamic movements" },
        { "tag": "pumpy_sustained", "description": "Endurance-based, pumpy route" },
        { "tag": "technical_moves", "description": "Precise footwork and body positioning" },
        { "tag": "powerful_bouldery", "description": "Strength-focused movement" },
        { "tag": "pockets_holes", "description": "Features pockets as primary holds" },
        { "tag": "small_edges", "description": "Crimp-intensive climbing" },
        { "tag": "slopey_holds", "description": "Requires compression and body tension" }
      ]
    },
    {
      "category": "Rope Length",
      "tags": [
        { "tag": "rope_70m", "description": "If 30m < route_length_meter <= 35m" },
        { "tag": "rope_80m", "description": "If route_length_meter > 35m" }
      ]
    }
  ]
}

```

## Tagging logics

- Manual vs. LLM Tags:  
  - Manual Tags:  
    These are generated based on the above logic from the scraped numeric and textual data.
  - LLM Tags:  
    These will be generated by an LLM API using the textual content from fields such as `area_description`, `route_description`, and comments.
  - Merging Strategy:  
    - Initially, store manual tags and LLM tags separately in the fields `manual_tags` and `llm_tags` for both areas and routes.
    - After the tagging process is complete, merge these into a final unified field (`area_tags` for areas and `route_tags` for routes).
  
- Hierarchical Format:  
  Tags should be stored as objects with category keys. For example:
  ```json
  "route_tags": {
      "Rope Length": ["rope_70m"],
      "Difficulty & Safety": ["sandbag", "runout_dangerous"],
      "Multipitch": ["short_multipitch"]
  }

### Manual Tagging Logic for MTNPJ Data

This document outlines the manual rules that will be applied to the scraped Mountain Project (MTNPJ) data to generate tags for routes (and areas) before merging them with LLM-provided tags. These rules are intended to create a consistent, hierarchical tag structure that will later be used for flexible searching in the web app.

---

#### 1. Rope Length (Single-Pitch Routes Only)

- Objective:  
  To determine if a single-pitch route requires a rope of 70m or 80m based on its length in meters.

- Logic:  
  - Single-pitch routes only:  
    This rule is applied strictly to single-pitch routes (i.e., routes without a `route_pitches` value).
  - Conditions:
    - If the route's `route_length_meter` is greater than 30m and less than or equal to 35m, add the tag `rope_70m`.
    - If the route's `route_length_meter` is greater than 35m, add the tag `rope_80m`.
  - Mutual Exclusivity:  
    Only one of these tags is applied per route. If the route length qualifies for `rope_80m`, the `rope_70m` tag is not added.

---

#### 2. Protection Grading: First in Grade vs. Sandbag

- Objective:  
  To evaluate how climbers' suggested ratings compare with the official route grade and assign tags accordingly.

- Grading Order:  
  The grading sequence is defined as follows (for example, for 5.11 routes):  
  `5.11a < 5.11b < 5.11c < 5.11d`  
  With rough approximations:  
  - `5.11-` roughly corresponds to 5.11a/b  
  - `5.11` roughly corresponds to 5.11b/c  
  - `5.11+` roughly corresponds to 5.11c/d

- Logic:  
  1. Data Extraction:  
     - From the route, extract the official grade (`route_grade`) and the suggested ratings (`route_suggested_ratings`) from climber votes.
  2. Vote Comparison:  
     - Count the number of votes that exactly match the official grade (A).
     - Count votes that are higher than the official grade (B).
     - Count votes that are lower than the official grade (C).
  3. Tag Assignment:  
     - Sandbag: If the number of votes for a higher grade (B) is larger than the votes for the official grade (A) and there are at least 5 total votes, add the tag `sandbag`.
     - First in Grade: If the number of votes for a lower grade (C) is larger than the votes for a higher grade (B) and there are at least 5 total votes, add the tag `first_in_grade`.
  4. Additional Considerations:  
     - Any suggested ratings that include protection modifiers such as PG13, X, or R should be ignored for this particular comparison.
  
---

#### 3. Runout/Dangerous

- Objective:  
  To flag routes that might be inherently more dangerous due to poor protection.

- Logic:  
  - Direct Check:  
    If the route's `route_protection_grading` (extracted from the header) is one of the values `"PG13"`, `"X"`, or `"R"`, the tag `runout_dangerous` should be added.
  - Indirect Check via Suggested Ratings:  
    Additionally, if more than 50% of the votes in `route_suggested_ratings` contain any of these protection indicators (`"PG13"`, `"X"`, or `"R"`), the tag `runout_dangerous` should also be applied.

---

#### 4. Multipitch Tagging

- Objective:  
  To classify multi-pitch routes based on the number of pitches.

- Logic:  
  - Check the field `route_pitches` (which should have been extracted from the route type).
  - Conditions:
    - If `route_pitches` is larger than1, less than 5, assign the tag `short_multipitch`.
    - If `route_pitches` is 5 or more, assign the tag `long_multipitch`.
  - For routes that do not include any pitch information, no multipitch tag is applied.

#### 5. classic_route

- Objective:  
  Identify routes that are considered classic.
- Rule:  
  - If a route has a star rating of 3 or higher (`route_stars >= 3`) and at least 5 votes (`route_votes >= 5`), add the tag `classic_route` under the Crowds & Popularity category.

#### 6. new_routes

- Objective:  
  Identify routes that have been shared after January 2022.

- Logic:  
  - Parse the `route_shared_on` field, which is in the format "Mon, YYYY".
  - If the year is greater than 2022 or if the year is 2022 and the month is later than January, add the tag `new_routes` under "Crowds & Popularity".

---

### LLM Tagging

#### Area tagging
The area tagging process uses LLM (GPT-4) to analyze area information and assign appropriate tags. Here's how it works:

1. Input Data Processing
   - For each area, the following information is analyzed:
     - Area Description
     - Getting There Information
     - Access Issues
     - Page Views
     - Area Share Date
     - Combined Area Comments

2. Tag Categories
   The LLM assigns tags across 4 main categories:
   - Weather & Conditions
     - Sun exposure tags (e.g., sun_am, sun_pm, sunny_all_day)
     - Weather impact tags (e.g., dries_fast, seepage_problem)
     - Environmental tags (e.g., windy_exposed)
   - Access & Restrictions
     - Seasonal closure tags (dynamically created based on access issues)
   - Crowds & Popularity
     - Crowd level indicators (e.g., low_crowds)
     - Area age tags (e.g., new_areas)
     - Usage impact tags (e.g., polished_rock)
   - Approach & Accessibility
     - Approach distance tags (none, short, moderate, long)
     - Access type tags (e.g., top_rope_possible)

3. Tagging Process
   - Areas are processed in batches using OpenAI's Batch API
   - Each area's information is formatted into a prompt
   - The LLM analyzes the text and returns tags in a structured JSON format
   - Only predefined tags from the prompt template are allowed, except for seasonal closures
   - Tags are stored in the area object under `area_tags`

4. Special Tag Handling
   - Seasonal closures are dynamically generated based on access issues
   - The format is `seasonal_closure_*` where * describes the specific reason
   - Examples: seasonal_closure_birdnesting, seasonal_closure_wetrock

5. Error Handling
   - Failed API calls are retried up to 3 times with exponential backoff
   - Invalid JSON responses are logged and skipped
   - Missing or malformed data is handled gracefully

The system ensures consistent tagging across areas while focusing on key aspects like weather conditions, access restrictions, popularity metrics, and approach characteristics.


#### Route tagging

The route tagging process uses LLM (GPT-4) to analyze route information and assign appropriate tags. Here's how it works:

1. Input Data Processing
   - For each route, the following information is analyzed:
     - Route Description
     - Route Location 
     - Route Type
     - Route Protection
     - Combined Route Comments and Tick Comments

2. Tag Categories
   The LLM assigns tags across 10 main categories:
   - Weather & Conditions
   - Access & Restrictions 
   - Crowds & Popularity
   - Difficulty & Safety
   - Approach & Accessibility
   - Multi-Pitch, Anchors & Descent
   - Route Style & Angle
   - Crack Climbing
   - Hold & Movement Type
   - Rope Length

3. Tagging Process
   - Routes are processed in batches using OpenAI's Batch API
   - Each route's information is formatted into a prompt
   - The LLM analyzes the text and returns tags in a structured JSON format
   - Only predefined tags from the prompt template are allowed
   - Tags are stored in the route object under `llm_tags`

4. Tag Combination
   - Manual tags and LLM tags are combined into a final `route_tags` field
   - If there are conflicts between manual and LLM tags:
     - Manual tags take precedence in their respective categories
     - Categories are mapped appropriately (e.g., "Multipitch" maps to "Multi-Pitch, Anchors & Descent")
     - Duplicate tags are removed during combination

5. Error Handling
   - Failed API calls are retried up to 3 times
   - Invalid JSON responses are logged and skipped
   - Missing or malformed data is handled gracefully

The system ensures consistent tagging across routes while leveraging both rule-based (manual) and AI-powered (LLM) approaches for comprehensive route classification.


#### Finalizing area and route LLM tagging

to be considered.

## Web application

### 📚 Overview
A minimalist climbing route search web app that allows users to:
- Search multiple areas or routes (free-text input)
- Filter by grade, type (Trad/Sport), and tags
- Display a list of routes with meaningful route details
- Work seamlessly across desktop & mobile
- Be fast & lightweight with a clean UI

---

## 🖥️ UI/UX Design

### 🎨 Design Philosophy
✅ Minimal & functional – Focus on usability over clutter  
✅ Fast & responsive – Works smoothly on mobile  
✅ Search-first UX – Users can type areas/routes without friction  
✅ Scalable – Can support future features (e.g., user ratings, maps)  

---

### 🔍 Search & Filter UI

#### Search Bar (Multi-input)
Functionality:
- Users can input multiple areas or routes (comma-separated)
- Autocomplete suggestions for popular climbing locations
- Press Enter or click a pill to add an entry
- Press ❌ to remove an entry  

Example UI:
```
🔍 [ Enter area or route name ]  [ + Add another area/route ]

📍 Yosemite, CA  ❌   📍 Red River Gorge, KY  ❌   📍 Smith Rock, OR  ❌
```

---

#### 📌 Filters
Filter Categories:
- Grade: Dropdown selector (`5.6 - 5.13d`)
  - Format: "5.{number}{letter}" (e.g., "5.10b", "5.11d")
  - Handles variations: simple (5.9), letter grades (5.10a), plus/minus (5.10+)
  - Common range: 5.6 to 5.13d

- Type: Checkboxes
  - `[ ] Trad`
  - `[ ] Sport`

- Tags: Collapsible categories with checkboxes
  ```
  Weather & Conditions ▼
    [ ] sun_am
    [ ] sun_pm
    [ ] sunny_all_day
    [ ] dries_fast
    [ ] seepage_problem
    [ ] windy_exposed

  Access & Restrictions ▼
    [ ] seasonal_closure

  Crowds & Popularity ▼
    [ ] low_crowds
    [ ] classic_route
    [ ] new_routes
    [ ] polished_rock

  Difficulty & Safety ▼
    [ ] first_in_grade
    [ ] sandbag
    [ ] runout_dangerous
    [ ] stick_clip
    [ ] loose_rock
    [ ] rope_drag_warning

  Approach & Accessibility ▼
    [ ] approach_none
    [ ] approach_short
    [ ] approach_moderate
    [ ] approach_long
    [ ] top_rope_possible

  Multi-Pitch, Anchors & Descent ▼
    [ ] short_multipitch
    [ ] long_multipitch
    [ ] bolted_anchor
    [ ] walk_off
    [ ] rappel_down

  Route Style & Angle ▼
    [ ] slab
    [ ] vertical
    [ ] gentle_overhang
    [ ] steep_roof
    [ ] tower_climbing
    [ ] sporty_trad

  Crack Climbing ▼
    [ ] finger_tip
    [ ] finger
    [ ] thin_hand
    [ ] wide_hand
    [ ] offwidth
    [ ] chimney
    [ ] layback

  Hold & Movement Type ▼
    [ ] reachy
    [ ] dynamic_moves
    [ ] pumpy_sustained
    [ ] technical_moves
    [ ] powerful_bouldery
    [ ] pockets_holes
    [ ] small_edges
    [ ] slopey_holds

  Rope Length ▼
    [ ] rope_70m
    [ ] rope_80m
  ```

Example UI State:
```
[ Grade: 5.10a - 5.11d ▼ ]
[ Type: Trad ☑  Sport ☐ ]
[ Tags ▼ ]
  Weather & Conditions ▼
    ☑ sunny_all_day
    ☑ dries_fast
  Route Style & Angle ▼
    ☑ vertical
    ☑ gentle_overhang
  Hold & Movement Type ▼
    ☑ technical_moves
    ☑ pumpy_sustained
```

---

### 💚 Search Results UI
- Display results in a list format with meaningful details
- Minimalist card-based layout
- Clickable for future expansions (route details page)

Example UI:
```
📌 Das Musak
   🌄 Castle Rock, WA | Sport | 5.11d | ⭐3.6 (36 votes)
   📏 60ft | 7 bolts
   🌂 Classic, Gentle Overhang, Pumpy, Bouldery

📌 Angel
   🌄 Castle Rock, WA | Trad | 5.10b | ⭐2.7 (129 votes)
   📏 300ft | 3 pitches
   🌂 Classic, Finger Crack, Technical, Polished

📌 Canary
   🌄 Castle Rock, WA | Trad | 5.8+ | ⭐3.4 (291 votes)
   📏 300ft | 3 pitches
   🌂 Classic, Vertical, Multi-Pitch, Walk-off
```

Key Details Shown:
- Route name
- Location & type
- Grade & star rating (with vote count)
- Length & pitch/bolt info
- Most relevant tags from route_tags categories

Mobile-Friendly Adjustments:
- Filters collapse under a "🔍 Filter" button  
- Results use a single-column layout
- Star ratings may condense to just the number on very small screens

## 🛠️ Technical Stack (Simplified)

### Core Stack
- **Frontend**: React + Vite
  - Fast development & build
  - Simple setup
  - No SSR complexity needed

- **UI**: 
  - TailwindCSS for styling
  - All data can be loaded statically
  - No complex UI libraries needed

- **Search**: Client-side search with Fuse.js
  - No backend needed
  - Works with static JSON data
  - Good fuzzy search capability

### Implementation Example

1. **Data Types**:
```typescript
// src/data/types.ts
interface Route {
  route_name: string;
  route_url: string;  // Link to Mountain Project
  route_grade: string;
  route_type: 'Trad' | 'Sport';
  route_stars: number;
  route_votes: number;
  route_tags: Record<string, string[]>;
  route_length_ft?: number;
  route_pitches?: number;
}
```

2. **Route Card Component**:
```typescript
// src/components/RouteCard.tsx
function RouteCard({ route }: { route: Route }) {
  return (
    <a 
      href={route.route_url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-4 border rounded-lg hover:border-blue-500 transition-colors"
    >
      <div className="flex justify-between items-start">
        <h3 className="font-bold text-lg">{route.route_name}</h3>
        <span className="text-blue-500">↗</span>
      </div>
      
      <div className="text-sm text-gray-600 mt-1">
        {route.route_type} | {route.route_grade} | ⭐{route.route_stars.toFixed(1)} ({route.route_votes})
      </div>
      
      {(route.route_length_ft || route.route_pitches) && (
        <div className="text-sm text-gray-600 mt-1">
          {route.route_length_ft && `${route.route_length_ft}ft`}
          {route.route_pitches && ` | ${route.route_pitches} pitches`}
        </div>
      )}
      
      <div className="mt-2 flex flex-wrap gap-1">
        {Object.values(route.route_tags)
          .flat()
          .slice(0, 4)
          .map(tag => (
            <span 
              key={tag}
              className="px-2 py-0.5 bg-gray-100 rounded-full text-sm"
            >
              {tag}
            </span>
          ))}
      </div>
    </a>
  );
}
```

3. **Main App Component**:
```typescript
// src/App.tsx
import { useState } from 'react';
import { useSearch } from './hooks/useSearch';
import { RouteCard } from './components/RouteCard';

export default function App() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    grades: ['5.6', '5.13d'] as [string, string],
    types: [] as string[],
    tags: [] as string[],
  });

  const results = useSearch(query, filters);

  return (
    <div className="max-w-4xl mx-auto p-4">
      <header className="mb-8 text-center">
        <h1 className="text-2xl font-bold mb-2">Climbing Route Tags</h1>
        <p className="text-gray-600">
          Search and filter routes by tags, then visit them on Mountain Project
        </p>
      </header>

      {/* Search & Filters */}
      <div className="mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search routes..."
          className="w-full p-3 border rounded-lg"
        />
        {/* Filters here */}
      </div>

      {/* Results */}
      <div className="space-y-4">
        {results.map(route => (
          <RouteCard key={route.route_url} route={route} />
        ))}
      </div>

      <footer className="mt-8 text-center text-sm text-gray-500">
        Data sourced from Mountain Project. Click any route to view it there.
      </footer>
    </div>
  );
}
```

### Key Features
- Each route card links directly to Mountain Project
- Focus on tag-based discovery
- Clear attribution and linking to source
- Simple, focused interface
- Fast local search and filtering

### Development
1. Clone repo
2. `npm install`
3. `npm run dev`
4. Open `http://localhost:5173`

### Deployment
- Deploy to GitHub Pages or Netlify
- All static, no backend needed
- Just build and upload