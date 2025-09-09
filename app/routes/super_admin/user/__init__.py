# app/routes/super_admin/user/__init__.py

# ✅ This imports each user view module so its routes are registered
from .add_user import *
from .edit_user import *
from .delete_user import *
from .manage_user import *
from .bulk_deactivate_users import *
from .bulk_user_action import *
from .reactivate_user import *
from .manage_contractors import *   
from .manage_pms import * 
