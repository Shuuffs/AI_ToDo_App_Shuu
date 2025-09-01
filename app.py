from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import openai
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Load API key
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

    # Build a simple list of tasks for the AI to reference
    task_list_text = "\n".join([f"{t['description']} (Completed: {t['completed']})" for t in tasks])

    system_prompt = f"""
You are an AI assistant for a To-Do List application.
You have access to the current tasks:
{task_list_text if task_list_text else 'No tasks yet.'}

When the user gives a command, decide if it should:
1. Add a task
2. Complete a task
3. Delete a task
4. Show tasks
Otherwise, reply naturally.

When performing actions, return JSON like this:
{{"function": "addTask", "parameters": {{"description": "Task description"}}}}
{{"function": "completeTask", "parameters": {{"description": "Task description"}}}}
{{"function": "deleteTask", "parameters": {{"description": "Task description"}}}}
{{"function": "viewTasks"}}

If the input is casual chat or greeting, reply naturally without JSON.

User input: "{user_text}"
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.2
        )
        ai_message = response.choices[0].message.content.strip()
        return jsonify({"ai_response": ai_message}), 200
    except Exception as e:
        return jsonify({"ai_response": f"Error: {str(e)}"}), 500

# ------------------- Run -------------------

if __name__ == "__main__":
    app.run(debug=True)
