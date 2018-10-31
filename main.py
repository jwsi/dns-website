from flask import Flask, jsonify

# Define the Flask name as "app".
# Note: EB accepts only "application" so point "app" to this for short hand.
application = Flask(__name__)
app = application


# ----------------------------------------------------------------------------------------------------------------------

# Start the app.
if __name__ == "__main__":
    app.run()
