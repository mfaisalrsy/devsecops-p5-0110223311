"""
Module: app.py
Main entry point for the TaskSecure REST API.
Implements secure routing, input validation, and automated security headers.
"""

import os
from flask import Flask, request, jsonify
from database import Database
from models import Task
from auth import hash_password, verify_password, generate_auth_token, verify_auth_token
from security_utils import sanitize_input, is_valid_username, generate_security_headers


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", "default-insecure-dev-key-change-me")
    db_path = ":memory:" if test_config and test_config.get("TESTING") else "app.db"
    db = Database(db_path=db_path)

    # Attach security headers to every response
    @app.after_request
    def set_security_headers(response):
        headers = generate_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "TaskSecure API",
            "version": "1.0.0"
        }), 200

    @app.route("/api/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}
        username = sanitize_input(data.get("username", ""))
        password = data.get("password", "")

        if not is_valid_username(username):
            return jsonify({"error": "Invalid username format. Must be 3-20 alphanumeric characters."}), 400

        if not password or len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long."}), 400

        pwd_hash = hash_password(password)
        user_id = db.create_user(username=username, password_hash=pwd_hash)
        if not user_id:
            return jsonify({"error": "Username already exists."}), 409

        return jsonify({
            "message": "User registered successfully.",
            "user_id": user_id,
            "username": username
        }), 201

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        username = sanitize_input(data.get("username", ""))
        password = data.get("password", "")

        user = db.get_user_by_username(username)
        if not user or not verify_password(user["password_hash"], password):
            return jsonify({"error": "Invalid username or password."}), 401

        token = generate_auth_token(username, app.config["SECRET_KEY"])
        return jsonify({
            "message": "Login successful.",
            "token": token,
            "username": username
        }), 200

    @app.route("/api/tasks", methods=["GET"])
    def list_tasks():
        tasks = db.get_tasks()
        return jsonify({"tasks": tasks, "count": len(tasks)}), 200

    @app.route("/api/tasks", methods=["POST"])
    def create_task():
        # Optional token verification
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else ""
        user = verify_auth_token(token, app.config["SECRET_KEY"]) if token else None

        data = request.get_json(silent=True) or {}
        title = sanitize_input(data.get("title", ""))
        description = sanitize_input(data.get("description", ""))

        task = Task(id=None, title=title, description=description)
        valid, err_msg = task.validate()
        if not valid:
            return jsonify({"error": err_msg}), 400

        task_id = db.create_task(title=title, description=description, owner_id=1 if user else None)
        return jsonify({
            "message": "Task created successfully.",
            "task_id": task_id,
            "title": title
        }), 201

    @app.route("/api/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id: int):
        task = db.get_task_by_id(task_id)
        if not task:
            return jsonify({"error": "Task not found."}), 404
        return jsonify({"task": task}), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id: int):
        success = db.delete_task(task_id)
        if not success:
            return jsonify({"error": "Task not found or could not be deleted."}), 404
        return jsonify({"message": f"Task {task_id} deleted successfully."}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
