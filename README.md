Biwinning
=========
Biwinning is an track record system for our bicycle club.


Setup
-----

```sh
mkvirtualenv --no-site-packages --distribute --python=python2.7 biwinning
git clone git://github.com/steinar/biwinning.git
cd biwinning
pip install -r requirements.txt
```

### Development server

```sh
python scripts/http.py 0.0.0.0 debug
```
For PyCharm settings, refer to [this screenshot](http://oi50.tinypic.com/6zvx8j.jpg).

Add Gagnavarslan club by opening [http://localhost:5000/7459/weeks](http://localhost:5000/7459/weeks).

### Interacative shell

```sh
python scripts/shell.py
```
Data methods and models are pre-imported.

```python
list(Club.all())
```

### Fetch data from Strava
```sh
python scripts/update.py
```

Todo
----

