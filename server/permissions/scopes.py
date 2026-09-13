# ==========================================================================
# JARVIS Centralized Permission Scopes
# ==========================================================================

from enum import Enum

class Scope(str, Enum):
    CONVERSATION_WRITE = "conversation:write"
    CONVERSATION_READ = "conversation:read"
    TASK_READ = "task:read"
    TASK_WRITE = "task:write"
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    RESEARCH_READ = "research:read"
    RESEARCH_WRITE = "research:write"
    NEWS_READ = "news:read"
    NEWS_WRITE = "news:write"
    NEWS_SUBSCRIBE = "news:subscribe"
    NEWS_NOTIFY = "news:notify"
    SOURCE_FETCH = "source:fetch"
    BRIEFING_GENERATE = "briefing:generate"
    EXTERNAL_LINK_OPEN = "external_link:open"
    MARKET_READ = "market:read"
    WATCHLIST_READ = "watchlist:read"
    WATCHLIST_WRITE = "watchlist:write"
    ALERT_READ = "alert:read"
    ALERT_WRITE = "alert:write"
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    DEVICE_READ = "device:read"
    DEVICE_CONTROL = "device:control"
    CODE_EXECUTE = "code:execute"
    BROKER_READ = "broker:read"
    BROKER_TRADE = "broker:trade"   # Disabled in this phase

