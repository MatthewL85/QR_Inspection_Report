import os
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_LOGO_EXTS = {"png","jpg","jpeg","svg"}

def _allowed(filename: str) -> bool:
    ext = (filename.rsplit(".", 1)[-1] or "").lower()
    return ext in ALLOWED_LOGO_EXTS

def _company_upload_dir(company_id: int) -> str:
    root = os.path.join(current_app.static_folder, "uploads", "company", str(company_id))
    os.makedirs(root, exist_ok=True)
    return root

def save_company_logo(company_id: int, file_storage) -> str:
    """
    Validates and stores a logo under static/uploads/company/<id>/logo.<ext>
    Returns a path relative to /static for easy url_for('static', filename=...)
    """
    filename = secure_filename(file_storage.filename or "")
    if not filename or not _allowed(filename):
        raise ValueError("Unsupported file type. Use SVG, PNG or JPG.")

    ext = filename.rsplit(".",1)[-1].lower()
    dest_dir = _company_upload_dir(company_id)

    # SVG: store as-is (light sanitize is out of scope here)
    if ext == "svg":
        dest = os.path.join(dest_dir, "logo.svg")
        file_storage.save(dest)
        return f"uploads/company/{company_id}/logo.svg"

    # Raster: verify & normalize to PNG
    try:
        img = Image.open(file_storage.stream)
        img.verify()  # verify integrity
    except Exception:
        raise ValueError("Invalid image file.")
    file_storage.stream.seek(0)
    img = Image.open(file_storage.stream).convert("RGBA")
    # Optionally resize very large images
    max_side = 1024
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        img = img.resize((int(w*scale), int(h*scale)))
    dest = os.path.join(dest_dir, "logo.png")
    img.save(dest, format="PNG", optimize=True)
    return f"uploads/company/{company_id}/logo.png"
