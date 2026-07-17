from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.routes.auth import auth_bp


@auth_bp.route("/profile/toggle-sharing", methods=["POST"], endpoint="toggle_sharing")
@login_required
def toggle_sharing():
    current_user.share_profile_with_directors = request.form.get("share_with_directors") == "on"
    db.session.commit()
    flash("Profile sharing preference updated.", "success")
    return redirect(url_for("auth.profile"))
