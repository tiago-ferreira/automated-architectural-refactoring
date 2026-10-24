"""Rotas HTTP de Usuários e Autenticação (Camada View/Routes do MVC)."""
from flask import Blueprint, jsonify, request
from controllers.user_controller import UserController

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users():
    body, status = UserController.list_users()
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    body, status = UserController.get_user(user_id)
    return jsonify(body), status


@user_bp.route("/users", methods=["POST"])
def create_user():
    body, status = UserController.create_user(request.get_json(silent=True))
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    body, status = UserController.update_user(
        user_id, request.get_json(silent=True)
    )
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    body, status = UserController.delete_user(user_id)
    return jsonify(body), status


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id: int):
    body, status = UserController.get_user_tasks(user_id)
    return jsonify(body), status


@user_bp.route("/login", methods=["POST"])
def login():
    body, status = UserController.login(request.get_json(silent=True))
    return jsonify(body), status
