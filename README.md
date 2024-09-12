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

#### Business details
GET /v1/businesses/:id
This endpoint will fetch data about the local game store selected.

### Data model
#### Read/write ratio
We are going to infrequently cache fetch results (get LGS's and LGS info) using an LFU caching pattern. Therefore the project is going to be read heavy. In theory an ACID (Consistency+ | Availability-) would be great to ensure that the reads are getting the correct information but since we are reading from Yelp Fushion we can avoid storing the read information in Postgres or MySQL. Vice versa, if we were continually writing to our DB we should leverage a BASE DB (Availability+ | Consistency-). To emulate a quick cache mechanism I will be hooking into MongoDB.

#### Data schema - caching
Business Document:
    - business_id
    - name
    - address
    - city
    - state
    - country
    - latidude
    - longitude
    - events

### High level design
Client - [CACHE] -> [Load Balancer] - /search -> Fushion API
                 |
                 - /businesses/:id -> Fushion API
- Cache: LFU strategy
- Load balancer: Not needed now but would probably use Round Robin [weighted] as it's easy to implement
- Fushion API: Fushion leverages an ACID DB (MySQL). The DB uses a leader-follower pattern with a sharded DB across different servers/nodes.

### Algorithms to fetch nearby businesses
Well I'm not implementing these algorithms so therefore I will be describing them here as per Alex & Sahn's book.

#### Two-dimensional search
Draw a circle from the lat/long position and locate stores within that circle (radius). 
```
SELECT business_id, business_name
FROM businesses
WHERE (latitude BETWEEN {:_lat} - {:_radius} AND {:_lat} + {:_radius})
AND (logitude BETWEEN {:_long} - {:_radius} AND {:_long} + {:_radius})
```

The query will be slow as there could be a lot of information. Using the lat/long as indexes doesn't improve performance much as it would require an intersection of datasets (due to using two-dimsensions [lat/long]).

**What indexing methods are available?**
- Hash: Even grid, Geohash
- Tree: Quadtree

Both divide the 2D map into smaller segments and build indexes off of these segments.

##### Even grid
- Divides the map into cells
- Business distribution is not even as some cells could have a lot more businesses

##### Geohash
- Divide the map into four quadrants
- Assign a binary string to each quadrant
- The segments are now 01, 11, 00, 10 with different latitude and longitude changes
- Recurse to desired point by adding up to '11'

##### QuadTree
- Like geohashing, the grid is divided into quadrants recursively [except represented as a tree instead of a string]

**So what does the memory look like for a leaf?**
For a node it needs to store the top-left and bottom-right coordinates. Each coordinate part is 8 bytes leading to 32 bytes used. An ID of a business can be defined with 8 bytes and if there are 100 within the bounds it implies that there are 800 bytes used. Adding this together leads to each node storing 832 bytes of data.

**So what does the memory look like for a non-leaf?**
For an internal node we need the top-left and bottom-right coordinates (32 bytes). We don't need to store a reference with all the business ids but we do need to point to the four child nodes. Each pointer consumes 8 bytes, implying that this portion takes 32 bytes. Adding these two together we get 64 bytes used by the internal nodes.

**Let's do some math and calculate the space needed for our hypothetical situation**
- We defined that the leaves can only contain 100 business IDs
- If there are 200m businesses then there will be 200m/100 -> 2m leaf nodes
- Number of internal nodes is 2m/3 -> 0.67m (due to large branching factor)
- Total memory = ||leaf nodes|| + ||internal nodes|| = 2m * 832bytes + 0.67m * 32bytes = 2GB
- This is relatively small and easy to store

## Design deep dive
### Scale the database
#### Business table
Since there are a lot of businesses (200m) and our servers are small (I'm broke) we should horizontally scale and shard the database. Shard by business ID. Crude example -> a-m in Shard A, n-z in Shard B.


### Caching
So there's an interesting problem here; should we implement caching via the backend or the frontend? So in reality we could just ignore the backend as a whole and treat Fushion API as our backend. This would allow us to quickly check each request in the Cache before making a request. Doing this defeats the purpose of the System Design exercise so instead I'm going to do the following:
- Check the cache, if there's a hit return the value
- If there's a miss, make a call to the backend service
- The backend service makes a call to Fushion API and caches the information to the Cache

#### Cache key
Leveraging coorindates as cache keys might not be the best. Coordinates from phones aren't accurate and could cache to the wrong location. Users can move (train/car) which could also lead to inaccurately fetched data. 

We could hash based off of geohashing to get a cluster per location that will be consistent. Hash by the nearest cluster per say.

**Should we use Redis or Mongo?**
In terms of availability MongoDB scales well. Apparently ![Redis doesn't support ACID operations](https://tinyurl.com/2hhx4k9n).
I'm going to stick to Mongo because I've used it before.

Frontend
```
async function fetchBusinessData(url, business_id):
    const cached_data = await db.collection.find(
        {
            'business_id': business_id
        }
    );

    if not cached_data:
        const response = await utils.fetchPy(`${Constants.FUSHION_BASE_URL}/businesses/${business_id}');
        const data = response.json();
        if (data.statusCode == 200) {
            return data;
        } else {
            utils.handleThirdPartyError(data);
            return null;            
        }
    else:
        return cached_data;
```

Backend - similar in structure just in python
```
def fetchBusinessData(url):
    # fetch from Yelp
    response = requests.Get(`${Constants.FUSHION_BASE_URL}/businesses/${business_id}');        
    return response.json()
```

### Region and availability zones
### Filter results by time or business type


## Resources
- ![System Design Interview v2 by Alex Xu & Sahn Lam](https://bytebytego.com/)
- ![MongoDB vs Redis by Amazon](https://aws.amazon.com/compare/the-difference-between-redis-and-mongodb/#:~:text=Conversely%2C%20Redis%20does%20not%20provide,alone%20isn't%20a%20solution.)