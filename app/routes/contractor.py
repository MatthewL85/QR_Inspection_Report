from app.helpers.decorators import login_required
from flask import Blueprint, render_template, session
contractor_bp = Blueprint('contractor', __name__)

@contractor_bp.route('/dashboard')
@login_required(role='Contractor')
def contractor_dashboard():
    return render_template('contractor_dashboard.html')

@contractor_bp.route('/settings')
@login_required
def contractor_settings():
    return render_template('contractor/settings.html')

@contractor_bp.route('/upload-compliance-document', methods=['GET', 'POST'], endpoint='upload_compliance_document')

@login_required
def contractor_upload_compliance_document():
    if request.method == 'POST':
        document_type = request.form['document_type']
        expiry_date = request.form['expiry_date']
        file = request.files['document']

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(os.path.join(current_app.root_path, 'static', file_path))

            doc = ContractorComplianceDocument(
                contractor_id=session.get('user')['id'],
                document_type=document_type,
                expiry_date=expiry_date,
                file_name=filename,
                file_path=file_path,
                is_required_for_work_order=False,  # Defaulted for contractor
                uploaded_by_id=session.get('user')['id']
            )
            db.session.add(doc)
            db.session.commit()

            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('contractor.dashboard'))

    return render_template('contractor/upload_compliance_document.html')

