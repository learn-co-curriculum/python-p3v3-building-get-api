# Building a GET API with Flask-Smorest: Code-Along

## Learning Goals

- Define a marshmallow schema to serialize and deserialize a model class.
- Define a Blueprint to organize information in API documentation.
- Define MethodView classes to dispatch request methods to corresponding
  instance methods.
- Decorate methods with `Blueprint.arguments` and `Blueprint.response` to
  specify request deserialization and response serialization respectively.

---

## Introduction

We will use Flask-Smorest to implement an API for a sports team data model. This
lesson will demonstrate how to build an API that allows the user to:

- Retrieve a list of all sports teams.
- Retrieve an individual sports team by id.

| Method | Endpoint                  | Description                             |
| ------ | ------------------------- | --------------------------------------- |
| GET    | `/api/v1/teams`           | Get a list of all teams.                |
| GET    | `/api/v1/teams/{team_id}` | Get a single team, given its unique id. |

Thus, given the following GET request:

```text
GET /api/v1/teams
```

The response will be the serialized team data as a JSON-formatted array:

```text
[
  {
    "division": "pacific",
    "id": 1,
    "losses": 2,
    "name": "San Jose Swifts",
    "wins": 10
  },
  {
    "division": "central",
    "id": 2,
    "losses": 1,
    "name": "Chicago Chickadees",
    "wins": 7
  },
  {
    "division": "atlantic",
    "id": 3,
    "losses": 3,
    "name": "Boston Buffleheads",
    "wins": 8
  }
]
```

The request to retrieve the team with id `1` is as shown:

```text
GET /api/v1/teams/1
```

The response contains the team data serialized as a JSON-formatted string:

```text
{
  "division": "pacific",
  "id": 1,
  "losses": 2,
  "name": "San Jose Swifts",
  "wins": 10
}
```

We'll handle a request for a non-existent team by returning a `404` HTTP status
code, along with an error message. and message:

Request:

```text
GET /api/v1/teams/100
```

Response:

```text
{
  "code": 404,
  "message": "Team 100 not found.",
  "status": "Not Found"
}
```

## Setup

> This lesson is a code-along, so fork and clone the repo.

Run `pipenv install && pipenv shell` to generate and enter your virtual
environment.

```console
$ pipenv install && pipenv shell
```

Change into the `server` directory:

```console
$ cd server
```

You can run the application as a script within the `server/` directory:

```console
$ python app.py
```

If you prefer working in a Flask environment, remember to configure it with the
following commands within the `server/` directory:

```console
$ export FLASK_APP=app.py
$ export FLASK_RUN_PORT=5555
$ flask run
```

When you complete this lesson, commit and push your work using `git` to submit.

---

## Flask-Smorest project structure

The `server` directory contains initial files for the flask application:

- `app.py` - flask application.
- `default_config.py` - default application settings.
- `models.py` - data model classes.
- `schemas.py` - marshmallow schemas.
- `resources.py` - `Blueprint` and `Methodview` resources.

The default flask application settings are stored in `server/default_config.py`:

```py
# server/default_config.py
"""Default application settings"""

class DefaultConfig:
    """Default configuration"""
    API_TITLE = "Team API"
    API_VERSION = 1.0
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
```

The file `server/app.py` configures the flask application from an instance of
`DefaultConfig`. The application implements a base route `/` to display a
welcome message.

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask
from flask_smorest import Api
from default_config import DefaultConfig

app = Flask(__name__)
app.config.from_object(DefaultConfig)
app.json.compact = False

# Create the API
api = Api(app)

@app.route('/')
def index():
    return f'<p>Welcome</p>'

if __name__ == '__main__':
    app.run(port=5555, debug=True)
```

Run the application, then navigate to `http://127.0.0.1:5555` to confirm the
welcome message is displayed.

Let's update the base route to display the application's default API title. If
you look in `default_config.py`, you'll see the variable `API_TITLE` assigned to
the value "Team API". We access the title from the application configuration as
`{app.config["API_TITLE"]}`. Update the base route to display the API title in a
paragraph as shown:

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask
from flask_smorest import Api
from default_config import DefaultConfig

app = Flask(__name__)
app.config.from_object(DefaultConfig)
app.json.compact = False

# Create the API
api = Api(app)

@app.route('/')
def index():
    return f'<p>{app.config["API_TITLE"]}</p>'

if __name__ == '__main__':
    app.run(port=5555, debug=True)
```

Reload `http://127.0.0.1:5555` to confirm the webpage displays `Team API`.

## Define a data store

A Flask application usually manages data in a database. For simplicity, we'll
temporarily store data in a Python dictionary and seed (i.e. initialize) the
dictionary with some sample data so we can test our API.

The `server/models.py` file contains a `Team` model class, along with an enum
named `Division`:

```py
# server/models.py

from enum import StrEnum, auto

class Division(StrEnum):
    Pacific = auto()    # "pacific"
    Central = auto()    # "central"
    Atlantic = auto()   # "atlantic"

class Team:
    all = {}  # dictionary with id as key

    def __init__(self, name, wins, losses, division):
        self.id = len(type(self).all.keys())+1
        self.name = name
        self.wins = wins
        self.losses = losses
        self.division = division
        type(self).all[self.id] = self

    @classmethod
    def seed(cls):
        """Initialize the dictionary with sample data"""
        Team(name="San Jose Swifts", wins=10, losses=2, division=Division.Pacific)
        Team(name="Chicago Chickadees", wins=7, losses=1, division=Division.Central)
        Team(name="Boston Buffleheads", wins=8, losses=3, division=Division.Atlantic)
```

- The `all` class variable is defines as a dictionary that will store instances
  with `id` as the key.
- The `Team` initializer method assigns `id` to an integer sequence based on the
  dictionary size.
- Each team is in a division, represented by the `Division` enum. Python 3.11
  introduced the
  [StrEnum](https://docs.python.org/3/library/enum.html#enum.StrEnum) class,
  which is the same as `Enum`, but its members can also be used as strings.
- The class method `seed()` initializes the dictionary with data for 3 sample
  teams.

Let's update the flask application to import the `Team` model and seed the
dictionary with sample data.

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask
from flask_smorest import Api

from default_config import DefaultConfig
from models import Team

app = Flask(__name__)
app.config.from_object(DefaultConfig)
app.json.compact = False

# Create the API
api = Api(app)

# Initialize the data store with sample data
Team.seed()

@app.route('/')
def index():
    return f'<p>{app.config["API_TITLE"]}</p>'
```

We can use the Flask shell to confirm the dictionary contents. Stop running the
flask application, then launch the shell in the `server` directory from the
console, and confirm the class variable `Team.all` references a dictionary with
3 key/value pairs:

```console
$ flask shell
>>> from models import Team
>>> Team.all
{1: <models.Team object at 0x106a360d0>, 2: <models.Team object at 0x106a35550>, 3: <models.Team object at 0x106a35650>}
>>> exit()
```

## Blueprint and MethodView classes

The `server/schemas.py` file contains a schema named `TeamSchema` with fields
based on the `Team` model:

```py
# server/schemas.py

from marshmallow import Schema, fields
from models import Team

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int()
    name = fields.Str()
    wins = fields.Int()
    losses = fields.Int()
    division = fields.Str()
```

We will define a blueprint in the file `server/resources.py`.

- A `Blueprint` is a collection of routes and other app-related functions that
  can be registered on a Flask application. We use a blueprint to map routes to
  `MethodView` classes.
- A `MethodView` class dispatches request methods to the corresponding instance
  methods. For example, if you implement a `get` method, it will be used to
  handle `GET` requests. The methods are decorated with `Blueprint.arguments`
  and `Blueprint.response` to specify request deserialization and response
  serialization respectively.

Edit `resources.py` and create a blueprint for the `Team` resource as shown.

```py
# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

blp = Blueprint("teams", __name__, url_prefix="/api/v1")
```

- `teams` is the blueprint name, which is shown in documentation and prepended
  to the endpoint names when you use `url_for`.
- `__name__` is the "import name".
- `url_prefix` is prepended to all routes associated with the blueprint.

Now that we've define a blueprint, let's add a class named `Teams` that is a
subclass of `MethodView`.

```py
# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team
from schemas import TeamSchema

blp = Blueprint("Team API", __name__, url_prefix="/api/v1")

@blp.route("/teams")
class Teams(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()
```

- The endpoint `/api/v1/teams` is associated with the `Teams` class (/api/v1 is
  prepended to the specified route).
- The `get(self)` method handles GET requests to the endpoint.
- The `get(self)` method is decorated with
  `@blp.response(200, TeamSchema(many=True))`.
  - The status code `200` indicates a successful request.
  - The response contains all `Team` class instances, each serialized using the
    schema `TeamSchema`.

By default, request and response bodies are serialized as JSON.

Edit `server/app.py` to (1) import the blueprint and (2) register it with the
flask application as shown:

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask
from flask_smorest import Api

from default_config import DefaultConfig
from resources import blp as TeamBlueprint
from models import Team

app = Flask(__name__)
app.config.from_object(DefaultConfig)
app.json.compact = False

# Create the API
api = Api(app)
api.register_blueprint(TeamBlueprint)

# Initialize the data store with sample data
Team.seed()

@app.route('/')
def index():
    return f'<p>{app.config["API_TITLE"]}</p>'

if __name__ == '__main__':
    app.run(port=5555, debug=True)

```

Run the flask application, then navigate to `http://127.0.0.1:5555/api/v1/teams`
and confirm the application returns a JSON array containing the serialized team
data:

```text
[
  {
    "division": "pacific",
    "id": 1,
    "losses": 2,
    "name": "San Jose Swifts",
    "wins": 10
  },
  {
    "division": "central",
    "id": 2,
    "losses": 1,
    "name": "Chicago Chickadees",
    "wins": 7
  },
  {
    "division": "atlantic",
    "id": 3,
    "losses": 3,
    "name": "Boston Buffleheads",
    "wins": 8
  }
]
```

Let's add another subclass of `MethodView` named `TeamsById` to retrieve an
individual sports team by id.

```py
@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team
```

Note the route takes an integer parameter `team_id`. The `get()` method takes
`team_id` as a parameter as well, and returns the corresponding team from the
dictionary, or raises an HTTPException with the status code `404` if the team is
not found.

- It is considered best practice to use the flask-smorest `abort()` method to
  raise a HTTPException for the given status code.

Let's test the new endpoint with a valid team id using the URL
`http://127.0.0.1:5555/api/v1/teams/1`. You should see the data for team #1:

```text
{
  "division": "pacific",
  "id": 1,
  "losses": 2,
  "name": "San Jose Swifts",
  "wins": 10
}
```

Try an id that does not correspond to any of the dictionary keys, such as
`http://127.0.0.1:5555/api/v1/teams/100`, and confirm the application returns an
error response:

```text
{
  "code": 404,
  "message": "Team 100 not found.",
  "status": "Not Found"
}
```

## OpenAPI

The flask-smorest library automatically generates
[OpenAPI](https://spec.openapis.org/oas/latest.html) documentation (formerly
known as Swagger) for the API. The documentation makes it easy to test our REST
APIs using a browser interface.

The default configuration in `server/default_config.py` sets up some required
environment variables, including `OPENAPI_SWAGGER_UI_PATH = = "/swagger-ui"`.

Make sure you are running the flask application, then navigate to
[http://127.0.0.1:5555/swagger-ui](http://127.0.0.1:5555/swagger-ui). You should
see a page that lets us test the two `GET` endpoints. This documentation is
automatically generated from the Blueprint and MethodView classes defined in
`server/resources.py`.

![swagger ui](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/swagger-ui.png)

Click on the first endpoint `GET /api/v1/teams`, then click the "Try it out"
button.
![try out get endpoint](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/get_try_it_out.png)

Click the "Execute" button to execute the GET request. The Flask application
generates a response with HTTP status code `200`, along with a response body
containing the JSON-formatted data for the 3 teams.

![execute get request](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/execute.png)

Now let's test the other endpoint to retrieve a team by id. Scroll down to the
`GET /api/v1/teams` endpoint. Click the "Try it out" button. You will need to
provide a value for `team_id`, since the route requires an integer parameter
`@blp.route("/teams/<int:team_id>")`. Let's try an id that corresponds to one of
the dictionary keys, such as `1`. The flask application returns a response
containing the serialized data for that team:

![execute get by id request](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/get_by_id.png)

However, attempting to get an id that does not exist such as `100` results in an
error response:

![execute get by id error](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/get_by_id_error.png)

Finally, let's update `server/app.py` to automatically redirect the base route
to `[http://127.0.0.1:5555/swagger-ui](http://127.0.0.1:5555/swagger-ui)`. If
you look at `server/default_config.py`, the variable `OPENAPI_SWAGGER_UI_PATH`
is assigned the value `/swagger-ui`.

Edit `server/app.py` to import the `redirect` function and update the base route
to redirect to the swagger-ui path as shown:

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask, redirect

# ... other code

@app.route('/')
def index():
    return redirect(app.config["OPENAPI_SWAGGER_UI_PATH"])

if __name__ == '__main__':
    app.run(port=5555, debug=True)
```

Now we can access the API documentation through the base URL
[http://localhost:5555/](http://localhost:5555/).

## Conclusion

We learned how to use the Flask-smorest library to implement the following API:

| Method | Endpoint                  | Description                             |
| ------ | ------------------------- | --------------------------------------- |
| GET    | `/api/v1/teams`           | Get a list of all teams.                |
| GET    | `/api/v1/teams/{team_id}` | Get a single team, given its unique id. |

We implement a `Blueprint` to map routes to `MethodView` classes, which dispatch
request methods to the corresponding instance methods.

Flask-smorest uses marshmallow for serialization and deserialization, which
makes it easy to document request and response bodies.

Flask-smorest also provides Swagger (with Swagger UI) and other documentation
out of the box by using simple decorators in the code to generate the
documentation.

## Solution Code

```py
# server/app.py
#!/usr/bin/env python3

from flask import Flask, redirect
from flask_smorest import Api

from default_config import DefaultConfig
from resources import blp as TeamBlueprint
from models import Team

app = Flask(__name__)
app.config.from_object(DefaultConfig)
app.json.compact = False

# Create the API
api = Api(app)
api.register_blueprint(TeamBlueprint)

# Initialize the data store with sample data
Team.seed()

@app.route('/')
def index():
    return redirect(app.config["OPENAPI_SWAGGER_UI_PATH"])

if __name__ == '__main__':
    app.run(port=5555, debug=True)
```

```py
# server/default_config.py
"""Default application settings"""

class DefaultConfig:
    """Default configuration"""
    API_TITLE = "Team API"
    API_VERSION = 1.0
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True
    DEBUG = True
```

```py
# server/models.py

from enum import StrEnum, auto

class Division(StrEnum):
    Pacific = auto()    # "pacific"
    Central = auto()    # "central"
    Atlantic = auto()   # "atlantic"

class Team:
    all = {}  # dictionary with id as key

    def __init__(self, name, wins, losses, division):
        self.id = len(type(self).all.keys())+1
        self.name = name
        self.wins = wins
        self.losses = losses
        self.division = division
        type(self).all[self.id] = self

    @classmethod
    def seed(cls):
        """Initialize the dictionary with sample data"""
        Team(name="San Jose Swifts", wins=10, losses=2, division=Division.Pacific)
        Team(name="Chicago Chickadees", wins=7, losses=1, division=Division.Central)
        Team(name="Boston Buffleheads", wins=8, losses=3, division=Division.Atlantic)
```

```py
# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team
from schemas import TeamSchema

blp = Blueprint("Team API", __name__, url_prefix="/api/v1")

@blp.route("/teams")
class Teams(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()

@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team
```

```py
# server/schemas.py

from marshmallow import Schema, fields
from models import Team

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int()
    name = fields.Str()
    wins = fields.Int()
    losses = fields.Int()
    division = fields.Str()
```

---

## Resources

- [Flask-smorest documentation](https://flask-smorest.readthedocs.io/en/latest/)
- [Flask-smorest Blueprint](https://flask-smorest.readthedocs.io/en/latest/api_reference.html#blueprint)
- [Flask MethodView](https://flask.palletsprojects.com/en/3.0.x/api/#flask.views.MethodView)
- [Python 3.11 StrEnum](https://docs.python.org/3/library/enum.html#enum.StrEnum)
- [OpenAPI](https://spec.openapis.org/oas/latest.html)
