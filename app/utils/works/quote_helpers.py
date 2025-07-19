from datetime import datetime
from app.extensions import db
from app.models.work_order import WorkOrder
from app.models.quote_response import QuoteResponse
from app.models.quote_recipient import QuoteRecipient
from app.models.core.user import User  # Optional: for audit trail
from sqlalchemy.exc import SQLAlchemyError

def process_quote_selection(quote_response_id, approved_by_user_id):
    try:
        approved_quote = QuoteResponse.query.get(quote_response_id)
        if not approved_quote:
            return {"success": False, "message": "Quote response not found."}

        work_order = approved_quote.work_order
        if not work_order:
            return {"success": False, "message": "Related work order not found."}

        # ✅ Approve selected quote
        approved_quote.status = 'Approved'
        approved_quote.is_selected = True
        approved_quote.decision_note = "Approved by system"

        # 📦 Archive other responses
        other_quotes = QuoteResponse.query.filter(
            QuoteResponse.work_order_id == work_order.id,
            QuoteResponse.id != approved_quote.id
        ).all()
        for q in other_quotes:
            q.status = 'Archived'
            q.decision_note = "Not selected – alternative approved"

        # ❌ Update recipients
        quote_recipients = QuoteRecipient.query.filter_by(work_order_id=work_order.id).all()
        for recipient in quote_recipients:
            if recipient.contractor_id == approved_quote.contractor_id:
                recipient.status = 'Responded'
                recipient.response_status = 'Approved'
            elif recipient.contractor_id in [q.contractor_id for q in other_quotes]:
                recipient.status = 'Responded'
                recipient.response_status = 'Not Selected'
            else:
                recipient.status = 'Closed'
                recipient.response_status = 'No Response'

        # 🔄 Update work order
        work_order.status = 'Quote Approved'
        work_order.converted_to_work_order = True
        work_order.quote_status = 'Approved'
        work_order.quote_approved_by_id = approved_by_user_id
        work_order.quote_approved_at = datetime.utcnow()
        work_order.accepted_contractor_id = approved_quote.contractor_id

        db.session.commit()
        return {"success": True, "message": "Quote approved and system updated."}

    except SQLAlchemyError as e:
        db.session.rollback()
        return {"success": False, "message": f"DB error: {str(e)}"}

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
