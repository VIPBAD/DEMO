from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # HTML load karega

@app.route("/save_user", methods=["POST"])
def save_user():
    data = request.json
    print("User Data:", data)  # Console te print hovega
    return {"status": "ok", "message": "User saved successfully"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
