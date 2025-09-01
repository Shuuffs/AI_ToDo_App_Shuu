from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import openai
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

tasks = []
next_id = 1

# ------------------- Routes -------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify(tasks), 200

@app.route("/tasks", methods=["POST"])
def add_task():
    global next_id
    data = request.get_json()
    if not data or "description" not in data:
        return jsonify({"error": "Task description is required"}), 400
    task = {"id": next_id, "description": data["description"], "completed": False}
    tasks.append(task)
    next_id += 1
    return jsonify(task), 201

@app.route("/tasks/<int:task_id>/complete", methods=["PUT"])
def complete_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            return jsonify(task), 200
    return jsonify({"error": "Task not found"}), 404

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    return jsonify({"message": "Task deleted"}), 200

# ------------------- AI Endpoint -------------------
@app.route("/ai", methods=["POST"])
def ai_command():
    user_text = request.json.get("user_text", "")
    if not user_text:
        return jsonify({"error": "No user text provided"}), 400

    system_prompt = f"""
You are a friendly AI assistant for a To-Do List app.

Rules:
- Respond in JSON only for commands related to tasks:
  - addTask(description: string)
  - completeTask(description: string)
  - deleteTask(description: string)
  - viewTasks()
- If input is casual chat, respond naturally in plain text.

Example:
User: "Add buy milk"
AI: {{"function": "addTask", "parameters": {{"description": "buy milk"}}}}

User: "Hello"
AI: "Hello! How can I help you today?"

User: "{user_text}"
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"ai_response": ai_message}), 200
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"}), 500

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True)
