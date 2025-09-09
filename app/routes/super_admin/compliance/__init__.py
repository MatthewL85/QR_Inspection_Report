# app/routes/super_admin/compliance/__init__.py

# 📁 Client Compliance Routes
#from app.routes.super_admin.compliance.client.client_compliance_documents import *
from app.routes.super_admin.compliance.client.compliance_documents_index import *
from app.routes.super_admin.compliance.client.compliance_review import *
from app.routes.super_admin.compliance.client.delete_client_compliance import *
from app.routes.super_admin.compliance.client.delete_selected_client_compliance import *
from app.routes.super_admin.compliance.client.download_client_compliance_document import *
from app.routes.super_admin.compliance.client.edit_client_compliance import *
from app.routes.super_admin.compliance.client.upload_client_compliance import *
from app.routes.super_admin.compliance.client.view_client_compliance import *
from app.routes.super_admin.compliance.client.expiring_documents import *

# 📁 Contractor Compliance Routes
from app.routes.super_admin.compliance.contractor.compliance_documents import *
