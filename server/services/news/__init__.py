# News Service Package
from server.services.news.base import BaseNewsProvider
from server.services.news.rss_provider import LiveRSSNewsProvider
from server.services.news.deduplication import clusterer, NewsClusterer
from server.services.news.briefing import briefing_generator, NewsBriefingGenerator

default_news_provider = LiveRSSNewsProvider()
