"""Entry point for the Colony Management tracker.

Run this file to start the web app, then open the printed address
(http://127.0.0.1:5000) in any web browser.
"""
from colony_tracker import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True auto-reloads when you change code and shows helpful errors.
    app.run(host="127.0.0.1", port=5000, debug=True)
