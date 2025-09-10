from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Mini App Backend is Running!"

@app.route("/save_user", methods=["POST"])
def save_user():
    data = request.json
    # Example: user info console te print
    print("User Data:", data)
    return {"status": "ok", "message": "User saved successfully"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
