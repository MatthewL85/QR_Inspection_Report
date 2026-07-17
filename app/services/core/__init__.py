"""Core platform services shared by module shells."""

from app.services.core.notification_feed import (
    NotificationFilters,
    build_notification_context,
    notification_feed_payload,
    notification_source_references,
)
from app.services.core.notification_intelligence import (
    build_notification_view,
    build_notification_views,
    notification_module_options,
    notification_stage_options,
    notification_summary,
    notification_view_payload,
)
from app.services.core.document_template_service import (
    build_document_template_context,
    document_template_payload,
    get_document_template_payload,
    resolve_document_template,
)
