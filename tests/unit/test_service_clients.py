"""Unit tests for service clients."""

import pytest
import respx
import httpx
import re
from services.file_storage.seafile_client import SeafileClient
from services.media_server.jellyfin_client import JellyfinClient
from services.productivity.wiki_client import WikiClient
from services.dev_tools.gitea_client import GiteaClient
from services.monitoring.prometheus_client import PrometheusClient
from services.monitoring.grafana_client import GrafanaClient
from services.security.vaultwarden_client import VaultwardenClient
from tests.fixtures.mock_responses import (
    mock_seafile_libraries_response,
    mock_jellyfin_libraries_response,
    mock_jellyfin_recent_items_response,
    mock_bookstack_pages_response,
    mock_gitea_repositories_response,
    mock_prometheus_query_response,
    mock_prometheus_metrics_response,
    mock_grafana_dashboards_response,
    mock_vaultwarden_stats_response
)


def mock_get(respx_mock, pattern: str, **kwargs):
    """Register a regex-based GET mock."""
    respx_mock.get(re.compile(pattern)).mock(**kwargs)


@pytest.mark.unit
class TestSeafileClient:
    """Test Seafile client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://seafile:8000/api2/ping/.*", return_value=httpx.Response(200))
        async with SeafileClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_ping_failure(self, respx_mock):
        """Test failed ping."""
        mock_get(respx_mock, r"http://seafile:8000/api2/ping/.*", return_value=httpx.Response(500))
        async with SeafileClient() as client:
            result = await client.ping()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_libraries(self, respx_mock):
        """Test getting libraries."""
        mock_libraries = mock_seafile_libraries_response()
        mock_get(
            respx_mock,
            r"http://seafile:8000/api2/repos/.*",
            return_value=httpx.Response(200, json=mock_libraries)
        )
        async with SeafileClient() as client:
            libraries = await client.get_libraries()
            assert len(libraries) == 2
            assert libraries[0]["name"] == "My Library"
    
    @pytest.mark.asyncio
    async def test_get_library_info(self, respx_mock):
        """Test getting library info."""
        mock_library = {"id": "abc123", "name": "My Library"}
        mock_get(
            respx_mock,
            r"http://seafile:8000/api2/repos/abc123/.*",
            return_value=httpx.Response(200, json=mock_library)
        )
        async with SeafileClient() as client:
            library = await client.get_library_info("abc123")
            assert library is not None
            assert library["name"] == "My Library"


@pytest.mark.unit
class TestJellyfinClient:
    """Test Jellyfin client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://jellyfin:8096/System/Ping.*", return_value=httpx.Response(200))
        async with JellyfinClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_libraries(self, respx_mock):
        """Test getting libraries."""
        mock_libraries = mock_jellyfin_libraries_response()
        mock_get(
            respx_mock,
            r"http://jellyfin:8096/Library/VirtualFolders.*",
            return_value=httpx.Response(200, json=mock_libraries)
        )
        async with JellyfinClient() as client:
            libraries = await client.get_libraries()
            assert len(libraries) == 2
            assert libraries[0]["Name"] == "Movies"
    
    @pytest.mark.asyncio
    async def test_get_recent_items(self, respx_mock):
        """Test getting recent items."""
        mock_items = mock_jellyfin_recent_items_response(limit=5)
        mock_get(
            respx_mock,
            r"http://jellyfin:8096/Items/Latest.*",
            return_value=httpx.Response(200, json=mock_items)
        )
        async with JellyfinClient() as client:
            items = await client.get_recent_items(5)
            assert len(items) == 5
            assert items[0]["Type"] == "Movie"


@pytest.mark.unit
class TestWikiClient:
    """Test BookStack wiki client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://bookstack:80/.*", return_value=httpx.Response(200))
        async with WikiClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_pages(self, respx_mock):
        """Test getting pages."""
        mock_response = mock_bookstack_pages_response()
        mock_get(
            respx_mock,
            r"http://bookstack:80/api/pages.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        async with WikiClient() as client:
            pages = await client.get_pages()
            assert len(pages) == 2
            assert pages[0]["name"] == "Getting Started"
    
    @pytest.mark.asyncio
    async def test_get_books(self, respx_mock):
        """Test getting books."""
        mock_books = {"data": [{"id": 1, "name": "Test Book"}]}
        mock_get(
            respx_mock,
            r"http://bookstack:80/api/books.*",
            return_value=httpx.Response(200, json=mock_books)
        )
        async with WikiClient() as client:
            books = await client.get_books()
            assert len(books) == 1
            assert books[0]["name"] == "Test Book"


@pytest.mark.unit
class TestGiteaClient:
    """Test Gitea client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://gitea:3000/api/v1/version.*", return_value=httpx.Response(200))
        async with GiteaClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_repositories(self, respx_mock):
        """Test getting repositories."""
        mock_response = mock_gitea_repositories_response()
        mock_get(
            respx_mock,
            r"http://gitea:3000/api/v1/repos/search.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        async with GiteaClient() as client:
            repos = await client.get_repositories(page=1, limit=20)
            assert len(repos) == 2
            assert repos[0]["name"] == "my-repo"
    
    @pytest.mark.asyncio
    async def test_get_user_repositories(self, respx_mock):
        """Test getting user repositories."""
        mock_repos = [{"id": 1, "name": "user-repo"}]
        mock_get(
            respx_mock,
            r"http://gitea:3000/api/v1/users/testuser/repos.*",
            return_value=httpx.Response(200, json=mock_repos)
        )
        async with GiteaClient() as client:
            repos = await client.get_user_repositories("testuser")
            assert len(repos) == 1
            assert repos[0]["name"] == "user-repo"


@pytest.mark.unit
class TestPrometheusClient:
    """Test Prometheus client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://prometheus:9090/-/healthy.*", return_value=httpx.Response(200))
        async with PrometheusClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_query(self, respx_mock):
        """Test PromQL query."""
        mock_response = mock_prometheus_query_response()
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/query.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        async with PrometheusClient() as client:
            result = await client.query("up")
            assert result is not None
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, respx_mock):
        """Test getting metrics list."""
        mock_response = mock_prometheus_metrics_response()
        mock_get(
            respx_mock,
            r"http://prometheus:9090/api/v1/label/__name__/values.*",
            return_value=httpx.Response(200, json=mock_response)
        )
        async with PrometheusClient() as client:
            metrics = await client.get_metrics()
            assert len(metrics) == 4
            assert "up" in metrics


@pytest.mark.unit
class TestGrafanaClient:
    """Test Grafana client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://grafana:3000/api/health.*", return_value=httpx.Response(200))
        async with GrafanaClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_dashboards(self, respx_mock):
        """Test getting dashboards."""
        mock_dashboards = mock_grafana_dashboards_response()
        mock_get(
            respx_mock,
            r"http://grafana:3000/api/search.*",
            return_value=httpx.Response(200, json=mock_dashboards)
        )
        async with GrafanaClient() as client:
            dashboards = await client.get_dashboards()
            assert len(dashboards) == 2
            assert dashboards[0]["title"] == "System Overview"


@pytest.mark.unit
class TestVaultwardenClient:
    """Test Vaultwarden client."""
    
    @pytest.mark.asyncio
    async def test_ping_success(self, respx_mock):
        """Test successful ping."""
        mock_get(respx_mock, r"http://vaultwarden:80/.*", return_value=httpx.Response(200))
        async with VaultwardenClient() as client:
            result = await client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_stats(self, respx_mock):
        """Test getting stats."""
        mock_stats = mock_vaultwarden_stats_response()
        mock_get(
            respx_mock,
            r"http://vaultwarden:80/admin/stats.*",
            return_value=httpx.Response(200, json=mock_stats)
        )
        async with VaultwardenClient() as client:
            stats = await client.get_stats()
            assert stats is not None
            assert stats["users"] == 10
            assert stats["items"] == 150


@pytest.mark.unit
class TestServiceClientErrorHandling:
    """Test error handling in service clients."""
    
    @pytest.mark.asyncio
    async def test_seafile_client_timeout(self, respx_mock):
        """Test Seafile client handles timeout."""
        mock_get(respx_mock, r"http://seafile:8000/api2/repos/.*", side_effect=httpx.TimeoutException("Timeout"))
        async with SeafileClient() as client:
            libraries = await client.get_libraries()
            assert libraries == []
    
    @pytest.mark.asyncio
    async def test_jellyfin_client_connection_error(self, respx_mock):
        """Test Jellyfin client handles connection error."""
        mock_get(
            respx_mock,
            r"http://jellyfin:8096/Library/VirtualFolders.*",
            side_effect=httpx.ConnectError("Connection failed")
        )
        async with JellyfinClient() as client:
            libraries = await client.get_libraries()
            assert libraries == []
    
    @pytest.mark.asyncio
    async def test_gitea_client_http_error(self, respx_mock):
        """Test Gitea client handles HTTP error."""
        mock_get(
            respx_mock,
            r"http://gitea:3000/api/v1/repos/search.*",
            return_value=httpx.Response(500)
        )
        async with GiteaClient() as client:
            repos = await client.get_repositories()
            assert repos == []
