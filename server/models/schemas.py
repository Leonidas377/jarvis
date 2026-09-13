# ==========================================================================
# JARVIS Pydantic Models & Schemas
# ==========================================================================

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from enum import Enum

class RiskLevel(str, Enum):
    R0_SAFE = "R0_SAFE"
    R1_LOW = "R1_LOW"
    R2_MEDIUM = "R2_MEDIUM"
    R3_HIGH = "R3_HIGH"
    R4_CRITICAL = "R4_CRITICAL"

# ----------------- Auth Schemas -----------------
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = "Stark Administrator"

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    created_at: str
    status: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ----------------- Conversation Schemas -----------------
class ConversationCreate(BaseModel):
    title: Optional[str] = "General Dialogue"
    mode: Optional[str] = "assistant"

class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: str
    mode: str
    created_at: str
    updated_at: str

class MessageCreate(BaseModel):
    content: str
    conversation_id: Optional[str] = None

class MessageOut(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    citations: Optional[List[str]] = None
    uncertainty: Optional[str] = None
    created_at: str

# ----------------- Task Schemas -----------------
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2)
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    category: Optional[str] = "general"
    due_date: Optional[str] = "Tomorrow"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    due_date: Optional[str] = None

class TaskOut(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    priority: str
    category: str
    status: str
    progress: int
    due_date: Optional[str]
    created_at: str
    updated_at: str

# ----------------- Memory Schemas -----------------
class MemoryCreate(BaseModel):
    category: str = "General"
    key: str
    value: str

class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None

class MemoryOut(BaseModel):
    id: str
    user_id: str
    category: str
    key: str
    value: str
    user_approved: bool
    created_at: str
    updated_at: str

# ----------------- Approval Schemas -----------------
class ApprovalOut(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str]
    tool_name: str
    summary: str
    parameters: Dict[str, Any]
    risk_level: str
    status: str
    created_at: str
    expires_at: str

class ApprovalDecision(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = None

# ----------------- Audit Schemas -----------------
class AuditEventOut(BaseModel):
    id: str
    user_id: str
    event_type: str
    actor: str
    resource_type: str
    resource_id: Optional[str]
    summary: str
    status: str
    correlation_id: str
    timestamp: str

# ----------------- Phase 3: Research & Search Schemas -----------------
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=250)
    category: Optional[str] = "all"
    region: Optional[str] = "us-en"
    limit: Optional[int] = Field(default=8, ge=1, le=25)

class SearchResultItem(BaseModel):
    id: str
    title: str
    url: str
    canonical_url: Optional[str] = None
    domain: str
    publisher: Optional[str] = None
    snippet: str
    published_date: Optional[str] = "Date unavailable"
    rank: int = 1
    provider: str
    retrieval_timestamp: str
    saved: bool = False

class SearchResponseOut(BaseModel):
    query_id: str
    query: str
    provider: str
    total_results: int
    results: List[SearchResultItem]
    status: str = "completed"

class SourceFetchRequest(BaseModel):
    url: str

class SourceDocumentOut(BaseModel):
    id: str
    url: str
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    access_timestamp: str
    extraction_status: str
    extracted_text: Optional[str] = None
    headings: Optional[List[str]] = []
    content_expiry: str

class CitationItem(BaseModel):
    id: str
    source_id: str
    title: str
    publisher: Optional[str] = None
    url: str
    published_date: Optional[str] = None
    excerpt: Optional[str] = None
    source_type: str = "web"

class ResearchReportCreate(BaseModel):
    query: str
    source_urls: Optional[List[str]] = []
    max_sources: Optional[int] = Field(default=3, ge=1, le=5)

class ResearchReportOut(BaseModel):
    id: str
    user_id: str
    title: str
    request_query: str
    executive_summary: str
    key_facts: List[str]
    source_comparison: Optional[List[Dict[str, Any]]] = []
    analysis: Optional[str] = None
    unknowns_and_limitations: Optional[str] = None
    citations: List[CitationItem]
    status: str
    saved: bool = True
    created_at: str
    updated_at: str

# ----------------- Research Brief Schemas (10-15 Line Syntheses) -----------------
class ResearchCitationItem(BaseModel):
    id: str
    title: str
    publisher: Optional[str] = "Web"
    url: str
    publication_date: Optional[str] = Field(default=None, alias="publicationDate")
    accessed_at: str = Field(default="", alias="accessedAt")
    source_type: str = Field(default="web", alias="sourceType")
    excerpt: Optional[str] = None

    model_config = {"populate_by_name": True}

class KeyPointItem(BaseModel):
    text: str
    citation_ids: List[str] = Field(default=[], alias="citationIds")

    model_config = {"populate_by_name": True}

class ResearchBriefRequest(BaseModel):
    query: str
    answer_mode: Optional[str] = Field(default="brief", alias="answerMode") # quick | brief | detailed | full
    topic_type: Optional[str] = Field(default=None, alias="topicType")
    source_count: Optional[int] = Field(default=4, alias="sourceCount", ge=1, le=10)
    include_sources: Optional[bool] = Field(default=True, alias="includeSources")
    save_result: Optional[bool] = Field(default=False, alias="saveResult")
    conversation_context_id: Optional[str] = Field(default=None, alias="conversationContextId")
    parent_brief_id: Optional[str] = Field(default=None, alias="parentBriefId")
    follow_up_action: Optional[str] = Field(default=None, alias="followUpAction")

    @field_validator("answer_mode")
    @classmethod
    def validate_answer_mode(cls, v: Optional[str]) -> str:
        if v and v.lower() not in {"quick", "brief", "detailed", "full"}:
            raise ValueError("answer_mode must be one of: quick, brief, detailed, full")
        return v.lower() if v else "brief"

    model_config = {"populate_by_name": True}

class ResearchBriefOut(BaseModel):
    id: str
    user_id: str = Field(..., alias="userId")
    query: str
    answer_mode: str = Field(default="brief", alias="answerMode")
    topic_type: str = Field(default="general", alias="topicType")
    title: str
    direct_answer: str = Field(..., alias="directAnswer")
    brief_paragraphs: List[str] = Field(..., alias="briefParagraphs")
    key_points: List[KeyPointItem] = Field(default=[], alias="keyPoints")
    takeaway: str
    citations: List[ResearchCitationItem]
    citation_ids: List[str] = Field(default=[], alias="citationIds")
    limitations: List[str] = []
    source_count: int = Field(default=0, alias="sourceCount")
    source_coverage: str = Field(default="complete", alias="sourceCoverage")
    coverage_status: str = Field(default="FULL", alias="coverageStatus")
    provider_name: Optional[str] = Field(default=None, alias="providerName")
    model_name: Optional[str] = Field(default=None, alias="modelName")
    status: str = "ready"
    saved: bool = False
    generated_at: str = Field(default="", alias="generatedAt")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}

class ResearchBriefActionRequest(BaseModel):
    action: str
    follow_up_query: Optional[str] = None

class ResearchBriefRenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class ResearchBriefExportOut(BaseModel):
    brief_id: str = Field(..., alias="briefId")
    format: str = "markdown"
    content: str
    title: str

    model_config = {"populate_by_name": True}


# ----------------- Phase 5: Real-Time News Intelligence & Topic Tracking -----------------
class NewsTopicCreate(BaseModel):
    topic_name: str = Field(..., min_length=2, max_length=100)
    query: str = Field(..., min_length=2, max_length=100)
    topic_type: Optional[str] = "keyword" # company | ticker | industry | country | region | keyword
    entity_id: Optional[str] = None
    ticker: Optional[str] = None
    category: Optional[str] = "General"
    region: Optional[str] = "Global"
    notifications_enabled: Optional[bool] = False
    notification_frequency: Optional[str] = "immediate"
    importance_threshold: Optional[str] = "all"
    refresh_preference: Optional[str] = "auto"

    model_config = {"populate_by_name": True}

class NewsTopicUpdate(BaseModel):
    topic_name: Optional[str] = None
    query: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    notification_frequency: Optional[str] = None
    importance_threshold: Optional[str] = None
    refresh_preference: Optional[str] = None
    is_active: Optional[bool] = None

class NewsTopicOut(BaseModel):
    id: str
    user_id: str
    topic_name: str
    query: str
    topic_type: str = "keyword"
    entity_id: Optional[str] = None
    ticker: Optional[str] = None
    category: str = "General"
    region: str = "Global"
    notifications_enabled: bool = False
    notification_frequency: str = "immediate"
    importance_threshold: str = "all"
    refresh_preference: str = "auto"
    is_active: bool = True
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"populate_by_name": True}

class NewsItemOut(BaseModel):
    id: str
    headline: str
    summary: str
    url: str
    canonical_url: Optional[str] = None
    publisher: str
    author: Optional[str] = None
    published_at: str
    retrieval_timestamp: str
    category: str
    region: str
    related_entities: Optional[List[str]] = []
    ticker: Optional[str] = None
    importance_label: str = "normal" # low | moderate | high | critical
    relevance_score: float = 1.0
    extraction_status: str = "PENDING"
    source_quality: str = "verified"
    cluster_id: Optional[str] = None
    is_read: bool = False
    is_saved: bool = False
    is_breaking: bool = False

    model_config = {"populate_by_name": True}

class NewsClusterOut(BaseModel):
    id: str
    representative_headline: str
    summary: str
    first_observed_at: str
    last_observed_at: str
    category: str = "General"
    importance_level: str = "normal"
    publisher_count: int = 1
    source_count: int = 1
    conflicting_coverage: bool = False
    member_item_ids: List[str] = []
    related_entities: List[str] = []
    sources: List[str] = []
    last_summarized_at: Optional[str] = None

    model_config = {"populate_by_name": True}

class NewsCitationItem(BaseModel):
    id: str
    title: str
    publisher: str
    url: str
    published_at: str

class NewsBriefingCreate(BaseModel):
    type: Optional[str] = "on_demand" # on_demand | morning | evening | weekly | breaking
    category: Optional[str] = "all"
    topic_id: Optional[str] = None
    time_window: Optional[str] = "24h"
    save_result: Optional[bool] = False

class NewsBriefingOut(BaseModel):
    id: Optional[str] = None
    briefing_id: str
    user_id: Optional[str] = None
    type: str = "on_demand"
    time_window: str = "24h"
    title: str
    summary: str
    key_events: List[Dict[str, Any]] = []
    citations: List[NewsCitationItem] = []
    market_implications: Optional[str] = None
    uncertainty_notes: Optional[str] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    source_coverage: str = "complete"
    saved: bool = False
    timestamp: str
    created_at: Optional[str] = None

    model_config = {"populate_by_name": True}

class NotificationRuleCreate(BaseModel):
    topic_id: Optional[str] = None
    notification_type: str = "breaking" # breaking | high_importance | daily_briefing | cluster_update
    frequency: str = "immediate" # immediate | hourly | daily
    importance_threshold: str = "high" # low | moderate | high | critical
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "07:00"
    is_enabled: bool = True

class NotificationRuleUpdate(BaseModel):
    notification_type: Optional[str] = None
    frequency: Optional[str] = None
    importance_threshold: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    is_enabled: Optional[bool] = None

class NotificationRuleOut(BaseModel):
    id: str
    user_id: str
    topic_id: Optional[str] = None
    notification_type: str
    frequency: str
    importance_threshold: str
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    is_enabled: bool
    created_at: str
    updated_at: str

    model_config = {"populate_by_name": True}

class NewsNotificationOut(BaseModel):
    id: str
    user_id: str
    cluster_id: Optional[str] = None
    topic_id: Optional[str] = None
    title: str
    message: str
    importance: str
    sent_at: str

    model_config = {"populate_by_name": True}


# ==========================================================================
# Phase 6: Real Market Data & Financial Telemetry Schemas
# ==========================================================================

class AssetOut(BaseModel):
    id: str
    provider_id: Optional[str] = None
    symbol: str
    name: str
    asset_type: str = "equity"
    exchange: str
    mic: Optional[str] = None
    country: str = "US"
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    timezone: str = "America/New_York"
    is_active: bool = True
    provider: str = "yahoo"
    identity_confidence: str = "confirmed"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"populate_by_name": True}

class AssetSearchIn(BaseModel):
    query: str
    asset_type: Optional[str] = None
    exchange: Optional[str] = None
    limit: int = 10

class MarketQuoteOut(BaseModel):
    id: Optional[str] = None
    asset_id: str
    symbol: str
    name: str
    price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int = 0
    market_cap: Optional[float] = None
    currency: str = "USD"
    exchange: str
    market_status: str = "OPEN" # OPEN | CLOSED | PRE_MARKET | AFTER_HOURS
    data_status: str = "LIVE DATA" # LIVE DATA | DELAYED DATA | SIMULATED DATA | MARKET CLOSED | STALE DATA
    timestamp: str
    provider: str = "yahoo"
    retrieved_at: Optional[str] = None

    model_config = {"populate_by_name": True}

class PriceBarOut(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    is_adjusted: bool = True
    currency: str = "USD"

class MarketHistoryOut(BaseModel):
    asset_id: str
    symbol: str
    interval: str = "1d"
    range: str = "1mo"
    bars: List[PriceBarOut] = []
    provider: str = "yahoo"
    data_status: str = "LIVE DATA"

class WatchlistCreate(BaseModel):
    name: str

class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None

class WatchlistItemAdd(BaseModel):
    asset_id: str

class WatchlistItemOut(BaseModel):
    id: str
    watchlist_id: str
    asset_id: str
    sort_order: int
    added_at: str
    asset: Optional[AssetOut] = None
    quote: Optional[MarketQuoteOut] = None

    model_config = {"populate_by_name": True}

class WatchlistOut(BaseModel):
    id: str
    user_id: str
    name: str
    sort_order: int = 0
    items: List[WatchlistItemOut] = []
    created_at: str
    updated_at: str

    model_config = {"populate_by_name": True}

class WatchlistReorderIn(BaseModel):
    item_ids: List[str]

class MarketAlertCreate(BaseModel):
    asset_id: str
    condition_type: str = "price_above" # price_above | price_below | pct_change_above | pct_change_below
    threshold: float
    cooldown_minutes: int = 60
    is_enabled: bool = True

class MarketAlertUpdate(BaseModel):
    condition_type: Optional[str] = None
    threshold: Optional[float] = None
    cooldown_minutes: Optional[int] = None
    is_enabled: Optional[bool] = None

class MarketAlertOut(BaseModel):
    id: str
    user_id: str
    asset_id: str
    symbol: Optional[str] = None
    condition_type: str
    threshold: float
    cooldown_minutes: int = 60
    is_enabled: bool = True
    last_triggered_at: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"populate_by_name": True}

class MarketOverviewOut(BaseModel):
    market_status: str = "OPEN"
    timestamp: str
    provider_status: str = "LIVE DATA"
    indices: List[MarketQuoteOut] = []
    gainers: List[MarketQuoteOut] = []
    losers: List[MarketQuoteOut] = []
    sectors: List[Dict[str, Any]] = []
    related_news: List[Dict[str, Any]] = []

class MarketCitationItem(BaseModel):
    id: str
    title: str
    source_type: str = "market_data" # market_data | news_wire | press_release
    url: Optional[str] = None
    publisher: Optional[str] = None
    timestamp: Optional[str] = None

class MarketInsightCreate(BaseModel):
    question: str
    asset_id: Optional[str] = None
    time_window: str = "24h"

class MarketInsightOut(BaseModel):
    id: str
    user_id: str
    question: str
    direct_answer: str
    observed_data: Dict[str, Any] = {}
    possible_explanations: List[str] = []
    uncertainty_notes: Optional[str] = None
    scenarios: List[str] = []
    citations: List[MarketCitationItem] = []
    market_disclaimer: str
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    created_at: str

    model_config = {"populate_by_name": True}

class ReadOnlyPortfolioOut(BaseModel):
    status: str = "BROKER_READ_ONLY_NOT_CONFIGURED"
    message: str = "Broker read-only telemetry is not configured. Live broker order placement and trading write operations are disabled."
    is_configured: bool = False
    holdings: List[Dict[str, Any]] = []
    buying_power: Optional[float] = None
    cash_balance: Optional[float] = None
    account_id_masked: Optional[str] = None


