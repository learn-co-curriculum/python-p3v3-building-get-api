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