"""Rotas HTTP de Categorias (Camada View/Routes do MVC) — separadas de relatórios."""
from flask import Blueprint, jsonify, request
from controllers.category_controller import CategoryController

category_bp = Blueprint("categories", __name__)


@category_bp.route("/categories", methods=["GET"])
def get_categories():
    body, status = CategoryController.list_categories()
    return jsonify(body), status


@category_bp.route("/categories", methods=["POST"])
def create_category():
    body, status = CategoryController.create_category(
        request.get_json(silent=True)
    )
    return jsonify(body), status


@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id: int):
    body, status = CategoryController.update_category(
        cat_id, request.get_json(silent=True)
    )
    return jsonify(body), status


@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id: int):
    body, status = CategoryController.delete_category(cat_id)
    return jsonify(body), status
