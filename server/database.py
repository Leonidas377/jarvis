# ==========================================================================
# JARVIS Database Management: SQLite WAL Mode with aiosqlite
# ==========================================================================

import aiosqlite
from pathlib import Path
from server.config import settings

class DBContextManager:
    async def __aenter__(self):
        self.db = await aiosqlite.connect(str(settings.DATABASE_FILE))
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode = WAL;")
        await self.db.execute("PRAGMA foreign_keys = ON;")
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db.close()

class _DBConnectionAwaitable:
    def __await__(self):
        async def _f():
            return DBContextManager()
        return _f().__await__()

    async def __aenter__(self):
        self._cm = DBContextManager()
        return await self._cm.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cm.__aexit__(exc_type, exc_val, exc_tb)

def get_db_connection():
    """Provides an active async SQLite connection configured with WAL and foreign keys."""
    return _DBConnectionAwaitable()

async def init_db():
    """Initializes all required normalized database tables."""
    async with await get_db_connection() as db:
        # 1. Users Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            );
        """)

        # 2. Conversations Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'assistant',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 3. Messages Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                citations_json TEXT,
                uncertainty TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 4. Tasks Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                category TEXT NOT NULL DEFAULT 'general',
                status TEXT NOT NULL DEFAULT 'active',
                progress INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 5. Memories Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                user_approved INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 6. Tool Executions Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT,
                tool_name TEXT NOT NULL,
                tool_version TEXT NOT NULL DEFAULT '1.0.0',
                parameters_json TEXT NOT NULL,
                result_json TEXT,
                risk_level TEXT NOT NULL DEFAULT 'R0_SAFE',
                execution_status TEXT NOT NULL DEFAULT 'success',
                duration_ms INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 7. Approval Requests Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT,
                tool_name TEXT NOT NULL,
                summary TEXT NOT NULL,
                parameters_json TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                rejection_reason TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 8. Audit Events Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                summary TEXT NOT NULL,
                status TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 9. Search Queries Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                filters_json TEXT,
                provider TEXT NOT NULL,
                result_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'completed',
                correlation_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 10. Search Results Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id TEXT PRIMARY KEY,
                query_id TEXT NOT NULL,
                provider_result_id TEXT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                canonical_url TEXT,
                domain TEXT NOT NULL,
                publisher TEXT,
                snippet TEXT,
                published_date TEXT,
                rank INTEGER NOT NULL DEFAULT 0,
                retrieval_timestamp TEXT NOT NULL,
                saved INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (query_id) REFERENCES search_queries (id) ON DELETE CASCADE
            );
        """)

        # 11. Source Documents Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS source_documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                canonical_url TEXT,
                title TEXT,
                publisher TEXT,
                author TEXT,
                published_date TEXT,
                access_timestamp TEXT NOT NULL,
                extraction_status TEXT NOT NULL,
                content_hash TEXT,
                extracted_text TEXT,
                headings_json TEXT,
                content_expiry TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 12. Research Reports Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS research_reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                request_query TEXT NOT NULL,
                executive_summary TEXT NOT NULL,
                key_facts_json TEXT NOT NULL,
                source_comparison_json TEXT,
                analysis TEXT,
                unknowns_and_limitations TEXT,
                citations_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                saved INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 12b. Research Briefs Table (10-15 line structured briefs with verified citations)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS research_briefs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                query TEXT NOT NULL,
                answer_mode TEXT NOT NULL DEFAULT 'brief',
                topic_type TEXT NOT NULL DEFAULT 'general',
                title TEXT NOT NULL,
                direct_answer TEXT NOT NULL,
                brief_paragraphs_json TEXT NOT NULL,
                key_points_json TEXT,
                takeaway TEXT NOT NULL,
                citations_json TEXT NOT NULL,
                limitations_json TEXT,
                source_count INTEGER NOT NULL DEFAULT 0,
                coverage_status TEXT NOT NULL DEFAULT 'FULL',
                source_coverage TEXT NOT NULL DEFAULT 'complete',
                provider_name TEXT,
                model_name TEXT,
                status TEXT NOT NULL DEFAULT 'ready',
                saved INTEGER NOT NULL DEFAULT 0,
                conversation_context_id TEXT,
                parent_brief_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Migration: Ensure new Phase 4 columns exist in existing SQLite databases
        cur = await db.execute("PRAGMA table_info(research_briefs)")
        rb_cols = {row["name"] for row in await cur.fetchall()}
        if "provider_name" not in rb_cols:
            await db.execute("ALTER TABLE research_briefs ADD COLUMN provider_name TEXT")
        if "model_name" not in rb_cols:
            await db.execute("ALTER TABLE research_briefs ADD COLUMN model_name TEXT")
        if "source_coverage" not in rb_cols:
            await db.execute("ALTER TABLE research_briefs ADD COLUMN source_coverage TEXT NOT NULL DEFAULT 'complete'")



        # 13. News Topics Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_topics (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_name TEXT NOT NULL,
                query TEXT NOT NULL,
                topic_type TEXT NOT NULL DEFAULT 'keyword',
                entity_id TEXT,
                ticker TEXT,
                category TEXT,
                region TEXT,
                notifications_enabled INTEGER NOT NULL DEFAULT 0,
                notification_frequency TEXT NOT NULL DEFAULT 'immediate',
                importance_threshold TEXT NOT NULL DEFAULT 'all',
                refresh_preference TEXT NOT NULL DEFAULT 'auto',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Migration: Ensure new news_topics columns exist
        cur = await db.execute("PRAGMA table_info(news_topics)")
        nt_cols = [r["name"] for r in await cur.fetchall()]
        if "topic_type" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN topic_type TEXT NOT NULL DEFAULT 'keyword'")
        if "entity_id" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN entity_id TEXT")
        if "ticker" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN ticker TEXT")
        if "notification_frequency" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN notification_frequency TEXT NOT NULL DEFAULT 'immediate'")
        if "importance_threshold" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN importance_threshold TEXT NOT NULL DEFAULT 'all'")
        if "refresh_preference" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN refresh_preference TEXT NOT NULL DEFAULT 'auto'")
        if "updated_at" not in nt_cols:
            await db.execute("ALTER TABLE news_topics ADD COLUMN updated_at TEXT")

        # 14. News Event Clusters Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_event_clusters (
                id TEXT PRIMARY KEY,
                representative_headline TEXT NOT NULL,
                summary TEXT NOT NULL,
                first_observed_at TEXT NOT NULL,
                last_observed_at TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                importance_level TEXT NOT NULL DEFAULT 'normal',
                publisher_count INTEGER NOT NULL DEFAULT 1,
                source_count INTEGER NOT NULL DEFAULT 1,
                conflicting_coverage INTEGER NOT NULL DEFAULT 0,
                member_item_ids_json TEXT DEFAULT '[]',
                related_entities_json TEXT DEFAULT '[]',
                last_summarized_at TEXT
            );
        """)

        # Migration: Ensure new news_event_clusters columns exist
        cur = await db.execute("PRAGMA table_info(news_event_clusters)")
        nec_cols = [r["name"] for r in await cur.fetchall()]
        if "publisher_count" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN publisher_count INTEGER NOT NULL DEFAULT 1")
        if "source_count" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN source_count INTEGER NOT NULL DEFAULT 1")
        if "conflicting_coverage" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN conflicting_coverage INTEGER NOT NULL DEFAULT 0")
        if "member_item_ids_json" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN member_item_ids_json TEXT DEFAULT '[]'")
        if "related_entities_json" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN related_entities_json TEXT DEFAULT '[]'")
        if "last_summarized_at" not in nec_cols:
            await db.execute("ALTER TABLE news_event_clusters ADD COLUMN last_summarized_at TEXT")

        # 15. News Items Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id TEXT PRIMARY KEY,
                provider_item_id TEXT,
                headline TEXT NOT NULL,
                summary TEXT,
                url TEXT NOT NULL,
                canonical_url TEXT,
                publisher TEXT NOT NULL,
                author TEXT,
                published_at TEXT NOT NULL,
                retrieval_timestamp TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'General',
                region TEXT DEFAULT 'Global',
                related_entities_json TEXT,
                ticker TEXT,
                importance_label TEXT NOT NULL DEFAULT 'normal',
                relevance_score REAL NOT NULL DEFAULT 1.0,
                extraction_status TEXT NOT NULL DEFAULT 'PENDING',
                source_quality TEXT NOT NULL DEFAULT 'verified',
                cluster_id TEXT,
                is_read INTEGER NOT NULL DEFAULT 0,
                is_saved INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (cluster_id) REFERENCES news_event_clusters (id) ON DELETE SET NULL
            );
        """)

        # Migration: Ensure new news_items columns exist
        cur = await db.execute("PRAGMA table_info(news_items)")
        ni_cols = [r["name"] for r in await cur.fetchall()]
        if "ticker" not in ni_cols:
            await db.execute("ALTER TABLE news_items ADD COLUMN ticker TEXT")
        if "importance_label" not in ni_cols:
            await db.execute("ALTER TABLE news_items ADD COLUMN importance_label TEXT NOT NULL DEFAULT 'normal'")
        if "relevance_score" not in ni_cols:
            await db.execute("ALTER TABLE news_items ADD COLUMN relevance_score REAL NOT NULL DEFAULT 1.0")
        if "extraction_status" not in ni_cols:
            await db.execute("ALTER TABLE news_items ADD COLUMN extraction_status TEXT NOT NULL DEFAULT 'PENDING'")
        if "source_quality" not in ni_cols:
            await db.execute("ALTER TABLE news_items ADD COLUMN source_quality TEXT NOT NULL DEFAULT 'verified'")

        # 16. News Briefings Table (Persistent LLM-Synthesized Briefings)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_briefings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'on_demand',
                time_window TEXT NOT NULL DEFAULT '24h',
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_events_json TEXT NOT NULL DEFAULT '[]',
                citations_json TEXT NOT NULL DEFAULT '[]',
                market_implications TEXT,
                uncertainty_notes TEXT,
                provider_name TEXT,
                model_name TEXT,
                saved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 17. Notification Rules Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notification_rules (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic_id TEXT,
                notification_type TEXT NOT NULL DEFAULT 'breaking',
                frequency TEXT NOT NULL DEFAULT 'immediate',
                importance_threshold TEXT NOT NULL DEFAULT 'high',
                quiet_hours_start TEXT DEFAULT '22:00',
                quiet_hours_end TEXT DEFAULT '07:00',
                is_enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES news_topics (id) ON DELETE CASCADE
            );
        """)

        # 18. News Notifications Table (Dispatched History & Deduplication Track)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                cluster_id TEXT,
                topic_id TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                importance TEXT NOT NULL DEFAULT 'normal',
                sent_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 16. User LLM Provider Configurations Table (Bring Your Own Key)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_llm_configs (
                id TEXT PRIMARY KEY,
                user_id TEXT UNIQUE NOT NULL,
                provider TEXT NOT NULL DEFAULT 'openai-compatible',
                display_name TEXT NOT NULL,
                base_url TEXT,
                model TEXT NOT NULL,
                organization_id TEXT,
                project_id TEXT,
                encrypted_api_key TEXT NOT NULL,
                key_fingerprint TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'untested',
                is_enabled INTEGER NOT NULL DEFAULT 1,
                temperature REAL NOT NULL DEFAULT 0.7,
                max_output_tokens INTEGER NOT NULL DEFAULT 1024,
                last_tested_at TEXT,
                last_error_code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 19. Phase 6 Market Intelligence Tables
        # Assets Table (Normalized financial instrument identities)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                provider_id TEXT,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL DEFAULT 'equity',
                exchange TEXT NOT NULL,
                mic TEXT,
                country TEXT NOT NULL DEFAULT 'US',
                currency TEXT NOT NULL DEFAULT 'USD',
                sector TEXT,
                industry TEXT,
                timezone TEXT NOT NULL DEFAULT 'America/New_York',
                is_active INTEGER NOT NULL DEFAULT 1,
                provider TEXT NOT NULL DEFAULT 'yahoo',
                identity_confidence TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Watchlists Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Watchlist Items Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id TEXT PRIMARY KEY,
                watchlist_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                added_at TEXT NOT NULL,
                FOREIGN KEY (watchlist_id) REFERENCES watchlists (id) ON DELETE CASCADE,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE
            );
        """)

        # Market Quotes Table (Historical & Latest Quotes Cache)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_quotes (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                price REAL NOT NULL,
                previous_close REAL NOT NULL,
                change REAL NOT NULL,
                change_percent REAL NOT NULL,
                volume INTEGER NOT NULL DEFAULT 0,
                market_cap REAL,
                currency TEXT NOT NULL DEFAULT 'USD',
                exchange TEXT NOT NULL,
                market_status TEXT NOT NULL DEFAULT 'OPEN',
                data_status TEXT NOT NULL DEFAULT 'LIVE DATA',
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'yahoo',
                retrieved_at TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE
            );
        """)

        # Price Bars Table (OHLCV Time Series)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_bars (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                interval TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL DEFAULT 0,
                is_adjusted INTEGER NOT NULL DEFAULT 1,
                currency TEXT NOT NULL DEFAULT 'USD',
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'yahoo',
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE
            );
        """)

        # Market Alerts Table (Informational Price & Volatility Notifications)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_alerts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                cooldown_minutes INTEGER NOT NULL DEFAULT 60,
                is_enabled INTEGER NOT NULL DEFAULT 1,
                last_triggered_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE
            );
        """)

        # Market Insights Table (Cited LLM Market Explanations with Observational Disclaimer)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_insights (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                asset_ids_json TEXT NOT NULL DEFAULT '[]',
                related_news_cluster_ids_json TEXT NOT NULL DEFAULT '[]',
                question TEXT NOT NULL,
                direct_answer TEXT NOT NULL,
                observed_data_json TEXT NOT NULL DEFAULT '{}',
                possible_explanations_json TEXT NOT NULL DEFAULT '[]',
                uncertainty_notes TEXT,
                scenarios_json TEXT NOT NULL DEFAULT '[]',
                citations_json TEXT NOT NULL DEFAULT '[]',
                market_disclaimer TEXT NOT NULL,
                provider_name TEXT,
                model_name TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast lookup
        await db.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages (conversation_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_approvals_user_status ON approval_requests (user_id, status);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_queries_user ON search_queries (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_results_query ON search_results (query_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_source_docs_url ON source_documents (url);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_reports_user ON research_reports (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_items_cat ON news_items (category);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_topics_user ON news_topics (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_briefings_user ON news_briefings (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_notif_user ON news_notifications (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_notif_rules_user ON notification_rules (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_llm_user ON user_llm_configs (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_assets_symbol_ex ON assets (symbol, exchange);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_items_wl ON watchlist_items (watchlist_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_quotes_asset ON market_quotes (asset_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_bars_asset_interval ON price_bars (asset_id, interval);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_market_alerts_user ON market_alerts (user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_market_insights_user ON market_insights (user_id);")

        # Seed default user for demo / offline operation
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, email, hashed_password, display_name, status, created_at)
            VALUES ('default-tony-stark', 'tony_stark', 'tony@starkindustries.com', 'seeded_default_hash', 'Tony Stark', 'active', datetime('now'))
        """)

        # Seed Core Reference Assets
        seed_assets = [
            ("asset-nvda", "NVDA", "NVIDIA Corporation", "equity", "NASDAQ", "XNAS", "US", "USD", "Technology", "Semiconductors", "America/New_York"),
            ("asset-aapl", "AAPL", "Apple Inc.", "equity", "NASDAQ", "XNAS", "US", "USD", "Technology", "Consumer Electronics", "America/New_York"),
            ("asset-tsm", "TSM", "Taiwan Semiconductor Manufacturing Co.", "equity", "NYSE", "XNYS", "Taiwan", "USD", "Technology", "Semiconductors", "America/New_York"),
            ("asset-msft", "MSFT", "Microsoft Corporation", "equity", "NASDAQ", "XNAS", "US", "USD", "Technology", "Software", "America/New_York"),
            ("asset-spy", "SPY", "SPDR S&P 500 ETF Trust", "etf", "NYSE Arca", "ARCX", "US", "USD", "Financials", "Broad Market ETF", "America/New_York"),
            ("asset-qqq", "QQQ", "Invesco QQQ Trust Series 1", "etf", "NASDAQ", "XNAS", "US", "USD", "Technology", "Index ETF", "America/New_York"),
            ("asset-btc", "BTC-USD", "Bitcoin / US Dollar", "crypto", "CRYPTO", "CRYP", "Global", "USD", "Digital Assets", "Cryptocurrency", "UTC")
        ]
        now_str = "2026-09-10 09:30:00"
        for a_id, sym, name, a_type, exch, mic, ctry, curr, sec, ind, tz in seed_assets:
            await db.execute("""
                INSERT OR IGNORE INTO assets (
                    id, provider_id, symbol, name, asset_type, exchange, mic,
                    country, currency, sector, industry, timezone, is_active,
                    provider, identity_confidence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'yahoo', 'confirmed', ?, ?)
            """, (a_id, sym, sym, name, a_type, exch, mic, ctry, curr, sec, ind, tz, now_str, now_str))

        # Seed Default Watchlist for Tony Stark
        wl_id = "wl-core-telemetry"
        await db.execute("""
            INSERT OR IGNORE INTO watchlists (id, user_id, name, sort_order, created_at, updated_at)
            VALUES (?, 'default-tony-stark', 'Core Telemetry Radar', 0, ?, ?)
        """, (wl_id, now_str, now_str))

        # Seed items in default watchlist
        for idx, (a_id, *_) in enumerate(seed_assets[:4]):
            await db.execute("""
                INSERT OR IGNORE INTO watchlist_items (id, watchlist_id, asset_id, sort_order, added_at)
                VALUES (?, ?, ?, ?, ?)
            """, (f"wli-{a_id}", wl_id, a_id, idx, now_str))

        await db.commit()
