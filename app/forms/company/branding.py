from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from wtforms.validators import Optional, Length, Regexp

HEX = Regexp(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", message="Use a HEX color like #3f51b5")

class CompanyBrandingForm(FlaskForm):
    # keep legacy brand_color if you want; we’ll focus on primary/secondary
    brand_primary_color = StringField("Primary Color", validators=[Optional(), HEX, Length(max=20)])
    brand_secondary_color = StringField("Secondary Color", validators=[Optional(), HEX, Length(max=20)])
    # logo upload (PNG/SVG/JPG)
    logo_file = FileField("Company Logo (SVG/PNG/JPG)", validators=[Optional()])
