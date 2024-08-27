# WPN Proximity service
This is another project based off of Alex Xu and Sahn Lam's System Design Interview volume 2. The goals of this project are to gain valuable skills to tackle the System Design Interview as well as gaining more experience with full stack development.

## The problem
Struggling to find a local WPN game store near you that host your favorite magic events? Look no further! The WPN Proximity Service not only finds game stores near you but also shows a calendar showcasing which day has your favorite event/store to play at.

## Design scope
### FAQ
**Can a user specify a radius?**
- Yes, there will be a drop down of default radii
**What if there are no WPN stores within the radius?**
- The search radius won't be expanded unless the user explicitly updates the radius
**What's the maximum radius?**
- 25 miles as we want to find the closest local game stores
**How are stores going to be found?**
- We're going to hook into Yelp Fushion's API as this provides the basics of what we are looking for (searcy by lat/long/radius)
**How is the application going to determine the location?**
- Ask permission from the user to enable location services

### Functional requirements
- Return local WPN stores based off the users location
- Users will see store information
- Users will see events by store in a calendar format

### Non-functional requirements
- Low latency: Users should be able to see the local game stores quickly
- Data privacy: Location is sensitive data. We will not gather user locale information unless allowed through explicit permission
- High availability and scalability: Out of scope at the moment

### Back of the envelope estimation (exercise)
Assumption: There are 100m DAU and 50m game stores. Each person makes an average of 5 queries a day.
Seconds in a day (users can use at anytime): 24h * 60m * 60s = 86.4k seconds
    - Recommendation is to round up to 10^5 to make the math easier
Search QPS: 100m DAU * 5 queries / 10^5 seconds = 5k queries per second

## Design
### API
I'm going to leverage [Django](https://www.djangoproject.com/) for this project and use the RESTful architecture to keep things simple. The bandwidth of REST is less than SOAP, REST is flexible and easy to scale due to the separation of client and server.

#### Searching
GET /v1/search
This endpoint will fetch all local game stores within a specified radius.

Request parameters are as follows:
- Latitude [decimal]: latitude of current location
- Longitude [decimal]: longitude of current location
- Radius [int]: optional radius, default is 5 miles

This API will hook into Mapbox::Geocoding::reverse by passing the latitude, longitude, type=place.


### High level design
### Search algorithms
### Data model
## Diving deep

## Resources
- ![System Design Interview v2 by Alex Xu & Sahn Lam](https://bytebytego.com/)