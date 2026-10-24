"""Rotas HTTP de Relatórios Analíticos (Camada View/Routes do MVC)."""
from flask import Blueprint, jsonify
from controllers.report_controller import ReportController

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
def summary_report():
    body, status = ReportController.get_summary_report()
    return jsonify(body), status


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id: int):
    body, status = ReportController.get_user_report(user_id)
    return jsonify(body), status
