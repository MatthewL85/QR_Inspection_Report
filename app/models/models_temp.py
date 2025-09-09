from app.extensions import db
from app.models.company import Company  # Needed for FK reflection
from app.models.core.user import User
from app.models.client.client import Client
from app.models.members.unit import Unit
from app.models.members.resident import Resident
from app.models.occupancy_log import OccupancyLog
from app.models.members.tenancy import Tenancy
from app.models.members.resident_request import ResidentRequest
from app.models.core.notification import Notification
from app.models.maintenance.equipment import Equipment
from app.models.maintenance.alert import Alert
from app.models.maintenance.inspection import Inspection
from app.models.maintenance.inspection_schedule import InspectionSchedule
from app.models.core.media_file import MediaFile
from app.models.audit.profile_change_log import ProfileChangeLog
from app.models.audit.password_change_log import PasswordChangeLog
from app.models.core.role import Role
from app.models.core.role_permissions import RolePermission
from app.models.finance.finance_batch import FinanceBatch
from app.models.finance.invoice import Invoice
from app.models.finance.payment_run import PaymentRun
from app.models.finance.service_charge import ServiceCharge
from app.models.finance.payment import Payment
from app.models.finance.reconciliation_batch import ReconciliationBatch
from app.models.finance.account import Account
from app.models.finance.transaction import Transaction
from app.models.finance.reconciliation_status import ReconciliationStatus
from app.models.finance.reconciliation_engine import ReconciliationEngine
from app.models.finance.bank_account import BankAccount
from app.models.finance.levy import Levy
from app.models.finance.bank_transaction import BankTransaction
from app.models.finance.service_charge_payment import ServiceChargePayment
from app.models.finance.levy_payment import LevyPayment
from app.models.client.country_client_config import CountryClientConfig
from app.models.finance.ledger_journal import LedgerJournal
from app.models.finance.chart_of_account import ChartOfAccount
from app.models.finance.general_ledger_entry import GeneralLedgerEntry
from app.models.finance.journal_entry import JournalEntry
from app.models.finance.journal_batch import JournalBatch
from app.models.finance.trial_balance import TrialBalance
from app.models.finance.ledger_entry import LedgerEntry
from app.models.finance.ledger_batch import LedgerBatch
from app.models.finance.ledger_allocation import LedgerAllocation
from app.models.finance.bank_reconciliation import BankReconciliation
from app.models.finance.credit_note import CreditNote
from app.models.finance.refund import Refund
from app.models.finance.debit_note import DebitNote
from app.models.finance.payment_adjustment import PaymentAdjustment
from app.models.finance.balance_sheet import BalanceSheet
from app.models.finance.income import Income
from app.models.finance.income_statement import IncomeStatement
from app.models.finance.cashflow_statement import CashflowStatement
from app.models.finance.budget import Budget
from app.models.finance.budget_forecast import BudgetForecast
from app.models.finance.budget_category import BudgetCategory
from app.models.finance.area_type import AreaType
from app.models.finance.budget_approval import BudgetApproval
from app.models.finance.budget_allocation_log import BudgetAllocationLog
from app.models.finance.generated_report_log import GeneratedReportLog
from app.models.finance.financial_report_config import FinancialReportConfig
from app.models.finance.tax_rate import TaxRate
from app.models.finance.tax_transaction_log import TaxTransactionLog
from app.models.finance.tax_filing_remittance import TaxFilingRemittance
from app.models.finance.withholding_tax_entry import WithholdingTaxEntry
from app.models.finance.cross_border_tax_compliance import CrossBorderTaxCompliance
from app.models.finance.outstanding_supplier_invoice import OutstandingSupplierInvoice
from app.models.finance.aged_debtor import AgedDebtor
from app.models.finance.aged_creditor import AgedCreditor
from app.models.finance.aged_creditor_summary import AgedCreditorSummary
from app.models.finance.aged_debtor_summary import AgedDebtorSummary
from app.models.finance.expenditure import Expenditure
from app.models.finance.apportionment_audit_log import ApportionmentAuditLog
from app.models.finance.annual_service_charge_statements import AnnualServiceChargeStatement
from app.models.finance.supplier_payment_reconciliation import SupplierPaymentReconciliation
from app.models.finance.arrears import Arrears
from app.models.finance.loan import Loan
from app.models.finance.loan_statement import LoanStatement
from app.models.finance.loan_repayment_schedule import LoanRepaymentSchedule
from app.models.finance.loan_interest_rate_history import LoanInterestRateHistory
from app.models.finance.loan_document import LoanDocument
from app.models.finance.late_fee_interest_policy import LateFeeAndInterestPolicy
from app.models.finance.late_fee_transaction_log import LateFeeTransactionLog
from app.models.finance.lease_apportionment_schedule import LeaseApportionmentSchedule
from app.models.finance.creditor import Creditor
from app.models.finance.debtor import Debtor
from app.models.finance.financial_audit_log import FinancialAuditLog
from app.models.finance.outstanding_balance import OutstandingBalance
from app.models.finance.payment_gateway_log import PaymentGatewayLog
from app.models.client.lease import Lease
from app.models.client.agm import AGM
from app.models.client.agm_participant import AGMParticipant
from app.models.client.board_meeting import BoardMeeting
from app.models.client.board_resolution import BoardResolution
from app.models.client.board_meeting_attendee import BoardMeetingAttendee
from app.models.client.meeting_integration import MeetingIntegration
from app.models.client.client_compliance_document import ClientComplianceDocument
from app.models.capex.capex_projects import CapexProject
from app.models.capex.capex_projects import CapexProjectDependency
from app.models.capex.capex_request import CapexRequest
from app.models.capex.capex_response import CapexResponse
from app.models.capex.capex_approval import CapexApproval
from app.models.contractor.contractor import Contractor
from app.models.contractor.contractor_assignment import ContractorAssignment
from app.models.contractor.contractor_compliance_document import ContractorComplianceDocument
from app.models.contractor.contractor_performance import ContractorPerformance
from app.models.contractor.contractor_feedback import ContractorFeedback
from app.models.works.work_order import WorkOrder
from app.models.maintenance.maintenance_request import MaintenanceRequest
from app.models.members.member import Member
from app.models.works.work_order_settings import WorkOrderSettings
from app.models.works.work_order_setting_audit_log import WorkOrderSettingAuditLog
from app.models.works.work_order_policy import WorkOrderPolicy
from app.models.works.work_order_completion import WorkOrderCompletion
from app.models.works.quote_response import QuoteResponse
from app.models.works.quote_recipient import QuoteRecipient
from app.models.maintenance.manual_task import ManualTask
from app.models.maintenance.manual_task_contractor import ManualTaskContractor
from app.models.director.director_area_assignment import DirectorAreaAssignment
from app.models.exports.exported_file_log import ExportedFileLog
from app.models.core.document import Document
from app.models.audit.audit_log import AuditLog
from app.models.members.member_approval import MemberApproval
from app.models.members.access_log import AccessLog
from app.models.hr.hr_policy import HRPolicy
from app.models.hr.hr_audit_log import HRAuditLog
from app.models.hr.hr_settings import HRSettings
from app.models.hr.hr_setting_entry import HRSettingEntry
from app.models.hr.hr_visibility_control import HRVisibilityControl
from app.models.hr.hr_profile import HRProfile
from app.models.hr.department import Department
from app.models.hr.certification import Certification
from app.models.hr.employee_exit_process import EmployeeExitProcess
from app.models.hr.employee_onboarding import EmployeeOnboarding
from app.models.hr.employment_contract import EmploymentContract
from app.models.hr.termination_record import TerminationRecord
from app.models.hr.management_company_review import ManagementCompanyReview
from app.models.hr.pm_review_by_director import PMReviewByDirector
from app.models.hr.performance_review import PerformanceReview
from app.models.hr.salary import Salary
from app.models.hr.leave_request import LeaveRequest
from app.models.hr.leave_balance_ledger import LeaveBalanceLedger
from app.models.hr.user_policy_acknowledgements import UserPolicyAcknowledgements
from app.models.communication.external_email_log import ExternalEmailLog
from app.models.communication.email_attachment import EmailAttachment
from app.models.contractor.contractor_team import ContractorTeam
from app.models.contractor.team_message import TeamMessage
from app.models.contractor.team_schedule import TeamSchedule
from app.models.audit.email_log import EmailLog

db.metadata.clear()

# Reflect both User and its dependency Company
Company.__table__.tometadata(db.metadata)
User.__table__.tometadata(db.metadata)
Client.__table__.tometadata(db.metadata)
Unit.__table__.tometadata(db.metadata)
Resident.__table__.tometadata(db.metadata)
OccupancyLog.__table__.tometadata(db.metadata)
Tenancy.__table__.tometadata(db.metadata)
ResidentRequest.__table__.tometadata(db.metadata)
Notification.__table__.tometadata(db.metadata)
Equipment.__table__.tometadata(db.metadata)
Alert.__table__.tometadata(db.metadata)
Inspection.__table__.tometadata(db.metadata)
InspectionSchedule.__table__.tometadata(db.metadata)
MediaFile.__table__.tometadata(db.metadata)
ProfileChangeLog.__table__.tometadata(db.metadata)
PasswordChangeLog.__table__.tometadata(db.metadata)
Role.__table__.tometadata(db.metadata)
RolePermission.__table__.tometadata(db.metadata)
FinanceBatch.__table__.tometadata(db.metadata)
Invoice.__table__.tometadata(db.metadata)
PaymentRun.__table__.tometadata(db.metadata)
ServiceCharge.__table__.tometadata(db.metadata)
Payment.__table__.tometadata(db.metadata)
ReconciliationBatch.__table__.tometadata(db.metadata)
Account.__table__.tometadata(db.metadata)
Transaction.__table__.tometadata(db.metadata)
ReconciliationStatus.__table__.tometadata(db.metadata)
ReconciliationEngine.__table__.tometadata(db.metadata)
BankAccount.__table__.tometadata(db.metadata)
Levy.__table__.tometadata(db.metadata)
BankTransaction.__table__.tometadata(db.metadata)
ServiceChargePayment.__table__.tometadata(db.metadata)
LevyPayment.__table__.tometadata(db.metadata)
CountryClientConfig.__table__.tometadata(db.metadata)
LedgerJournal.__table__.tometadata(db.metadata)
ChartOfAccount.__table__.tometadata(db.metadata)
GeneralLedgerEntry.__table__.tometadata(db.metadata)
JournalEntry.__table__.tometadata(db.metadata)
JournalBatch.__table__.tometadata(db.metadata)
TrialBalance.__table__.tometadata(db.metadata)
LedgerEntry.__table__.tometadata(db.metadata)
LedgerBatch.__table__.tometadata(db.metadata)
LedgerAllocation.__table__.tometadata(db.metadata)
BankReconciliation.__table__.tometadata(db.metadata)
CreditNote.__table__.tometadata(db.metadata)
Refund.__table__.tometadata(db.metadata)
DebitNote.__table__.tometadata(db.metadata)
PaymentAdjustment.__table__.tometadata(db.metadata)
BalanceSheet.__table__.tometadata(db.metadata)
Income.__table__.tometadata(db.metadata)
IncomeStatement.__table__.tometadata(db.metadata)
CashflowStatement.__table__.tometadata(db.metadata)
Budget.__table__.tometadata(db.metadata)
BudgetForecast.__table__.tometadata(db.metadata)
BudgetCategory.__table__.tometadata(db.metadata)
AreaType.__table__.tometadata(db.metadata)
BudgetApproval.__table__.tometadata(db.metadata)
BudgetAllocationLog.__table__.tometadata(db.metadata)
GeneratedReportLog.__table__.tometadata(db.metadata)
FinancialReportConfig.__table__.tometadata(db.metadata)
TaxRate.__table__.tometadata(db.metadata)
TaxTransactionLog.__table__.tometadata(db.metadata)
TaxFilingRemittance.__table__.tometadata(db.metadata)
WithholdingTaxEntry.__table__.tometadata(db.metadata)
CrossBorderTaxCompliance.__table__.tometadata(db.metadata)
OutstandingSupplierInvoice.__table__.tometadata(db.metadata)
AgedDebtor.__table__.tometadata(db.metadata)
AgedCreditor.__table__.tometadata(db.metadata)
AgedCreditorSummary.__table__.tometadata(db.metadata)
AgedDebtorSummary.__table__.tometadata(db.metadata)
Expenditure.__table__.tometadata(db.metadata)
ApportionmentAuditLog.__table__.tometadata(db.metadata)
AnnualServiceChargeStatement.__table__.tometadata(db.metadata)
SupplierPaymentReconciliation.__table__.tometadata(db.metadata)
Arrears.__table__.tometadata(db.metadata)
Loan.__table__.tometadata(db.metadata)
LoanStatement.__table__.tometadata(db.metadata)
LoanRepaymentSchedule.__table__.tometadata(db.metadata)
LoanInterestRateHistory.__table__.tometadata(db.metadata)
LoanDocument.__table__.tometadata(db.metadata)
LateFeeAndInterestPolicy.__table__.tometadata(db.metadata)
LateFeeTransactionLog.__table__.tometadata(db.metadata)
LeaseApportionmentSchedule.__table__.tometadata(db.metadata)
Creditor.__table__.tometadata(db.metadata)
Debtor.__table__.tometadata(db.metadata)
FinancialAuditLog.__table__.tometadata(db.metadata)
OutstandingBalance.__table__.tometadata(db.metadata)
PaymentGatewayLog.__table__.tometadata(db.metadata)
Lease.__table__.tometadata(db.metadata)
AGM.__table__.tometadata(db.metadata)
AGMParticipant.__table__.tometadata(db.metadata)
BoardMeeting.__table__.tometadata(db.metadata)
BoardResolution.__table__.tometadata(db.metadata)
BoardMeetingAttendee.__table__.tometadata(db.metadata)
MeetingIntegration.__table__.tometadata(db.metadata)
ClientComplianceDocument.__table__.tometadata(db.metadata)
CapexProjects.__table__.tometadata(db.metadata)
CapexRequest.__table__.tometadata(db.metadata)
CapexResponse.__table__.tometadata(db.metadata)
CapexApproval.__table__.tometadata(db.metadata)
Contractor.__table__.tometadata(db.metadata)
ContractorAssignment.__table__.tometadata(db.metadata)
ContractorComplianceDocument.__table__.tometadata(db.metadata)
ContractorPerformance.__table__.tometadata(db.metadata)
ContractorFeedback.__table__.tometadata(db.metadata)
WorkOrder.__table__.tometadata(db.metadata)
MaintenanceRequest.__table__.tometadata(db.metadata)
Member.__table__.tometadata(db.metadata)
WorkOrderSettings.__table__.tometadata(db.metadata)
WorkOrderSettingAuditLog.__table__.tometadata(db.metadata)
WorkOrderPolicy.__table__.tometadata(db.metadata)
WorkOrderCompletion.__table__.tometadata(db.metadata)
QuoteResponse.__table__.tometadata(db.metadata)
QuoteRecipient.__table__.tometadata(db.metadata)
ManualTask.__table__.tometadata(db.metadata)
ManualTaskContractor.__table__.tometadata(db.metadata)
DirectorAreaAssignment.__table__.tometadata(db.metadata)
ExportedFileLog.__table__.tometadata(db.metadata)
Document.__table__.tometadata(db.metadata)
AuditLog.__table__.tometadata(db.metadata)
MemberApproval.__table__.tometadata(db.metadata)
AccessLog.__table__.tometadata(db.metadata)
HRPolicy.__table__.tometadata(db.metadata)
HRAuditLog.__table__.tometadata(db.metadata)
HRSettings.__table__.tometadata(db.metadata)
HRSettingEntry.__table__.tometadata(db.metadata)
HRVisibilityControl.__table__.tometadata(db.metadata)
HRProfile.__table__.tometadata(db.metadata)
Department.__table__.tometadata(db.metadata)
Certification.__table__.tometadata(db.metadata)
EmployeeExitProcess.__table__.tometadata(db.metadata)
EmployeeOnboarding.__table__.tometadata(db.metadata)
EmploymentContract.__table__.tometadata(db.metadata)
TerminationRecord.__table__.tometadata(db.metadata)
ManagementCompanyReview.__table__.tometadata(db.metadata)
PMReviewByDirector.__table__.tometadata(db.metadata)
PerformanceReview.__table__.tometadata(db.metadata)
Salary.__table__.tometadata(db.metadata)
LeaveRequest.__table__.tometadata(db.metadata)
LeaveBalanceLedger.__table__.tometadata(db.metadata)
UserPolicyAcknowledgements.__table__.tometadata(db.metadata)
ExternalEmailLog.__table__.tometadata(db.metadata)
EmailAttachment.__table__.tometadata(db.metadata)
ContractorTeam.__table__.tometadata(db.metadata)
TeamMessage.__table__.tometadata(db.metadata)
TeamSchedule.__table__.tometadata(db.metadata)
EmailLog.__table__.tometadata(db.metadata)

print("Tables in metadata now:", db.metadata.tables.keys())








