from datetime import datetime, timedelta
from app.extensions import db
from app.models.finance.ledger_entry import LedgerEntry
from app.models.finance.ledger_journal import LedgerJournal
from app.models.finance.account import Account
from app.models.core.user import User
from sqlalchemy.exc import SQLAlchemyError
from app.models.audit.audit_log import log_audit_change  # 🧠 future hook
import logging

class PostingEngine:
    def __init__(self, journal_id, created_by_id, preview_mode=False):
        self.journal_id = journal_id
        self.created_by_id = created_by_id
        self.preview_mode = preview_mode
        self.journal = LedgerJournal.query.get(journal_id)
        self.errors = []
        self.entries_preview = []

    def validate_journal(self):
        total_debits = sum(e['amount'] for e in self.journal.entries if e['type'] == 'debit')
        total_credits = sum(e['amount'] for e in self.journal.entries if e['type'] == 'credit')
        return round(total_debits, 2) == round(total_credits, 2)

    def detect_recurring_imbalance(self):
        recent_flagged = LedgerJournal.query.filter(
            LedgerJournal.created_by_id == self.created_by_id,
            LedgerJournal.flagged_by_gar == True,
            LedgerJournal.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        return recent_flagged >= 3

    def post(self):
        if not self.journal:
            self.errors.append("Journal not found.")
            return False

        if self.journal.status == 'Posted':
            self.errors.append("Journal already posted.")
            return False

        if not self.validate_journal():
            self.journal.flagged_by_gar = True
            self.journal.gar_notes = "Imbalance detected in journal."
            if self.detect_recurring_imbalance():
                self.journal.gar_notes += " Recurring imbalance pattern detected by AI."

            db.session.commit()
            self.errors.append("Debits and credits do not balance.")
            return False

        try:
            for entry_data in self.journal.entries:
                entry = LedgerEntry(
                    journal_id=self.journal.id,
                    account_id=entry_data['account_id'],
                    entry_type=entry_data['type'],
                    amount=entry_data['amount'],
                    entry_description=entry_data.get('description'),
                    created_by_id=self.created_by_id,
                    created_at=datetime.utcnow(),
                    gar_context_reference=self.journal.gar_context_reference,
                    external_reference_id=entry_data.get('external_reference_id'),
                    external_system_name=entry_data.get('external_system_name'),
                    sync_status=entry_data.get('sync_status', 'Pending')
                )

                if self.preview_mode:
                    self.entries_preview.append(entry)
                else:
                    db.session.add(entry)

            if self.preview_mode:
                return {
                    "status": "Preview Only",
                    "journal_id": self.journal.id,
                    "entries": [e.__repr__() for e in self.entries_preview]
                }

            self.journal.status = 'Posted'
            self.journal.posted_at = datetime.utcnow()
            self.journal.posted_by_id = self.created_by_id

            db.session.commit()

            # 🧠 Optional: audit log
            log_audit_change(
                user_id=self.created_by_id,
                action='journal_posted',
                context='PostingEngine',
                object_id=self.journal.id,
                details={'entries_count': len(self.journal.entries)}
            )

            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.exception("PostingEngine DB error:")
            self.errors.append(str(e))
            return False

    def get_errors(self):
        return self.errors
