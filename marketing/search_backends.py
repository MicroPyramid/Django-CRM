from django.conf import settings

from haystack.backends.elasticsearch_backend import (
    ElasticsearchSearchBackend,
    ElasticsearchSearchEngine,
)


class CustomElasticsearchSearchBackend(ElasticsearchSearchBackend):
    def __init__(self, connection_alias, **connection_options):
        super(CustomElasticsearchSearchBackend, self).__init__(
            connection_alias, **connection_options
        )

        setattr(self, "DEFAULT_SETTINGS", settings.ELASTICSEARCH_INDEX_SETTINGS)


class CustomElasticsearchSearchEngine(ElasticsearchSearchEngine):

    backend = CustomElasticsearchSearchBackend
