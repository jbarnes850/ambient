"""Tools module for wellness agents"""

from .communication import (
    send_sms,
    send_whatsapp,
    approve_action,
    get_pending_approvals,
    generate_approval_id,
    approval_queue,
    schedule_meeting
)

from .health import (
    get_health_metrics,
    optimize_calendar,
    get_sleep_data
)

from .commerce import (
    search_wellness_products,
    commerce_buy
)

from .automation import (
    execute_ios_shortcut,
    web_search
)

__all__ = [
    'send_sms',
    'send_whatsapp',
    'approve_action',
    'get_pending_approvals',
    'generate_approval_id',
    'approval_queue',
    'get_health_metrics',
    'optimize_calendar',
    'get_sleep_data',
    'schedule_meeting',
    'search_wellness_products',
    'commerce_buy',
    'execute_ios_shortcut',
    'web_search'
]