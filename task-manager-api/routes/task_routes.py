"""Rotas HTTP de Tarefas (Camada View/Routes do MVC)."""
from flask import Blueprint, jsonify, request
from controllers.task_controller import TaskController

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    body, status = TaskController.list_tasks()
    return jsonify(body), status


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int):
    body, status = TaskController.get_task(task_id)
    return jsonify(body), status


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    body, status = TaskController.create_task(request.get_json(silent=True))
    return jsonify(body), status


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id: int):
    body, status = TaskController.update_task(
        task_id, request.get_json(silent=True)
    )
    return jsonify(body), status


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int):
    body, status = TaskController.delete_task(task_id)
    return jsonify(body), status


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    body, status = TaskController.search_tasks(
        query_term=request.args.get("q", ""),
        status=request.args.get("status", ""),
        priority_raw=request.args.get("priority", ""),
        user_id_raw=request.args.get("user_id", ""),
    )
    return jsonify(body), status


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    body, status = TaskController.get_task_stats()
    return jsonify(body), status
