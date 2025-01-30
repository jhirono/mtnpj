# Better Search for Mountain Project

Mtnpj has a premitive search capability just using name, grade, type, rating and number of pitches. However, I as a trad climber, I want to search using crack sizes like finger, hand, off-width, chimney. I as a sport climber in winter, I want to search walls and routes under the sunshine. I as a boulder climber, I want to search slab problems to horn my slab climbing skills. This porject is for providing a better search capability for the data in mtnpj.

## Key User Scenarios

|I want to search for routes by |Trad Climber|Sport Climber|Boulder Climber|
|---|---|---|---|
|crack size so that I can find routes to practice specific widths; finger tips, finger, narrow hand, wide hand, offwidth, chimney|Yes|No|No|
|weather conditions so that I can find routes suitable for different seasons; routes in the sun for winter and routes in the shade for summer.|Yes|Yes|Yes|
|its traffic so that I can avoid less traffic routes which may have loose rocks.|Yes|Yes|No|
|its developed date so that I can find new routes in an area.|Yes|Yes|Yes|
|softer grading so that I can find routes suitable for attempting a new grade for the first time.|Yes|Yes|Yes|

memo
* required equipment (rope length, protection, quick draws)
* anchor
* how to rappel down
* latest route condition

## Not to do
This service only provides a search capability.

## Design

### Data
1. Scrape areas, routes and their detail information from Mtnpj
1. Scrape data from a guidebook if it is possible.
1. Add requird tag information using LLM
1. Store all data in ****(json or SQL)

### Front End
Obey 