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
    task = {
        "id": next_id,
        "description": data["description"],
        "completed": False,
        "due_time": data.get("due_time", None)
    }
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

# ------------------- Complete All / Delete All -------------------
@app.route("/tasks/complete_all", methods=["PUT"])
def complete_all_tasks():
    for task in tasks:
        task["completed"] = True
    return jsonify({"message": "All tasks completed"}), 200

@app.route("/tasks/delete_all", methods=["DELETE"])
def delete_all_tasks():
    global tasks
    tasks = []
    return jsonify({"message": "All tasks deleted"}), 200

# ------------------- AI Endpoint -------------------
@app.route("/ai", methods=["POST"])
def ai_command():
    user_text = request.json.get("user_text", "")
    if not user_text:
        return jsonify({"error": "No user text provided"}), 400

    system_prompt = f"""
You are a friendly AI assistant for a To-Do List app.

Rules:
1. Respond in JSON for task commands:
   - addTask(description: string, due_time: string optional)
   - completeTask(description: string)
   - completeAllTasks()
   - deleteTask(description: string)
   - deleteAllTasks()
   - viewTasks()
2. Handle multiple tasks in one request.
3. Generate creative tasks if user asks for random tasks.
4. Include optional due times if mentioned.
5. Respond naturally in plain text for casual chat.

Examples:
User: "Add buy milk"
AI: {{"function": "addTask", "parameters": {{"description": "buy milk"}}}}

User: "Add dinner and gaming"
AI: [
  {{"function": "addTask", "parameters": {{"description": "dinner"}}}},
  {{"function": "addTask", "parameters": {{"description": "gaming"}}}}
]

User: "Add 3 random tasks"
AI: [
  {{"function": "addTask", "parameters": {{"description": "Go for a morning run"}}}},
  {{"function": "addTask", "parameters": {{"description": "Read a book chapter"}}}},
  {{"function": "addTask", "parameters": {{"description": "Clean your workspace"}}}}
]

User: "Complete all tasks"
AI: {{"function": "completeAllTasks", "parameters": {{}}}}

User: "Delete all tasks?"
AI: {{"function": "deleteAllTasks", "parameters": {{}}}}

User: "Hello"
AI: "Hello! How can I help you today?"

User: "{user_text}"
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.3
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"ai_response": ai_message}), 200
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"}), 500

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True)
