## TODO

- all config using file? to be consistend and reduce edge cases that need to be covered ? 


### Note from ai for creating server 
Gotcha 😎 — in that case, you can just parameterize the host and port so the user can choose how they want to run it.

Here’s a clean way:

python
Copy
Edit
from flask import Flask
import argparse

app = Flask(__name__)

@app.route("/")
def home():
    return "hello"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port)