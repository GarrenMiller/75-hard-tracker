from flask import Blueprint, jsonify

from .registry import all_types

goal_types_bp = Blueprint("goal_types", __name__)


@goal_types_bp.get("")
def list_goal_types():
    return jsonify({"goal_types": [t.to_dict() for t in all_types()]})
