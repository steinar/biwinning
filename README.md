Biwinning
=========
Biwinning is an track record system for our bicycle club.



Setup
-----

```sh
mkvirtualenv --no-site-packages --distribute --python=python2.7 biwinning
git clone git://github.com/steinar/biwinning.git
```


Strava API
-----------
### GPS points
```
http://app.strava.com/api/v1/streams/[ride id]
```

### Club members
```
http://app.strava.com/api/v1/clubs/[club id]/members
```

### Rides
```
http://app.strava.com/api/v1/rides?athleteId=[athlete id]&offset=[offset]&startId=[latest id]
```

### Single ride
```
http://www.strava.com/api/v1/rides/[ride id]
```

