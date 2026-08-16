from flask import Blueprint, g, jsonify

from ..auth.utils import require_auth
from .service import build_profile

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("")
@require_auth
def get_profile():
    return jsonify(build_profile(g.user))
