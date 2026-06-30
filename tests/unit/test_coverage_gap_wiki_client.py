"""Targeted tests for services.productivity.wiki_client to improve coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from services.productivity.wiki_client import WikiClient
from services.productivity.config import WikiConfig
from app.exceptions import WikiError


def _json_response(data, status_code: int = 200):
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=data)
    return response


@pytest.mark.unit
class TestWikiClient:
    """Cover WikiClient OAuth, pages, books, and create flows."""

    @pytest.mark.asyncio
    async def test_get_access_token_missing_credentials_raises(self):
        client = WikiClient(config=WikiConfig(base_url="http://bookstack:80"))
        with pytest.raises(WikiError, match="API credentials"):
            await client._get_access_token()

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                return_value=_json_response({"access_token": "tok123"})
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            config = WikiConfig(
                base_url="http://bookstack:80",
                api_id="id",
                api_secret="secret",
            )
            client = WikiClient(config=config)
            token = await client._get_access_token()
        assert token == "tok123"
        assert client._access_token == "tok123"

    @pytest.mark.asyncio
    async def test_get_access_token_cached_short_circuit(self):
        config = WikiConfig(
            base_url="http://bookstack:80",
            api_id="id",
            api_secret="secret",
        )
        client = WikiClient(config=config)
        client._access_token = "cached"
        token = await client._get_access_token()
        assert token == "cached"

    @pytest.mark.asyncio
    async def test_get_access_token_http_status_error(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=_json_response({}, status_code=401))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            client = WikiClient(
                config=WikiConfig(
                    base_url="http://bookstack:80", api_id="id", api_secret="secret"
                )
            )
            with pytest.raises(WikiError, match="Failed to get access token"):
                await client._get_access_token()

    @pytest.mark.asyncio
    async def test_get_access_token_http_error(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.RequestError("network down"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            client = WikiClient(
                config=WikiConfig(
                    base_url="http://bookstack:80", api_id="id", api_secret="secret"
                )
            )
            with pytest.raises(WikiError, match="HTTP error while getting access token"):
                await client._get_access_token()

    @pytest.mark.asyncio
    async def test_get_access_token_timeout(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            client = WikiClient(
                config=WikiConfig(
                    base_url="http://bookstack:80", api_id="id", api_secret="secret"
                )
            )
            with pytest.raises(WikiError, match="Timeout while getting access token"):
                await client._get_access_token()

    @pytest.mark.asyncio
    async def test_get_access_token_unexpected_error(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=RuntimeError("boom"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            client = WikiClient(
                config=WikiConfig(
                    base_url="http://bookstack:80", api_id="id", api_secret="secret"
                )
            )
            with pytest.raises(WikiError, match="Unexpected error while getting access token"):
                await client._get_access_token()

    @pytest.mark.asyncio
    async def test_aenter_with_oauth_token(self):
        with patch.object(WikiClient, "_get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "tok123"
            config = WikiConfig(
                base_url="http://bookstack:80",
                api_id="id",
                api_secret="secret",
            )
            async with WikiClient(config=config) as client:
                assert client._session is not None
                assert client._session.headers["Authorization"] == "Bearer tok123"

    @pytest.mark.asyncio
    async def test_aenter_with_api_token(self):
        config = WikiConfig(base_url="http://bookstack:80", api_token="static-token")
        async with WikiClient(config=config) as client:
            assert client._session.headers["Authorization"] == "Bearer static-token"

    @pytest.mark.asyncio
    async def test_get_pages_dict_response(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({"data": [{"id": 1}]}))
            pages = await client.get_pages()
        assert pages == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_get_pages_list_response(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            with patch.object(
                WikiClient, "_handle_request", new_callable=AsyncMock, return_value=[{"id": 2}]
            ):
                pages = await client.get_pages()
        assert pages == [{"id": 2}]

    @pytest.mark.asyncio
    async def test_get_pages_empty_fallback(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            with patch.object(
                WikiClient, "_handle_request", new_callable=AsyncMock, return_value={"unexpected": True}
            ):
                pages = await client.get_pages()
        assert pages == []

    @pytest.mark.asyncio
    async def test_get_page_success(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({"data": {"id": 5}}))
            page = await client.get_page("5")
        assert page == {"id": 5}

    @pytest.mark.asyncio
    async def test_get_page_not_found(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({}, status_code=404))
            page = await client.get_page("missing")
        assert page is None

    @pytest.mark.asyncio
    async def test_get_books_success(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({"data": [{"id": 9}]}))
            books = await client.get_books()
        assert books == [{"id": 9}]

    @pytest.mark.asyncio
    async def test_create_page_with_book_id(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.post = AsyncMock(return_value=_json_response({"data": {"id": 99}}, status_code=201))
            page = await client.create_page("Title", "<p>body</p>", book_id=9)
        assert page == {"id": 99}

    @pytest.mark.asyncio
    async def test_create_page_uses_first_book(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({"data": [{"id": 3}]}))
            client._session.post = AsyncMock(return_value=_json_response({"data": {"id": 100}}, status_code=201))
            page = await client.create_page("Title", "<p>body</p>")
        assert page == {"id": 100}

    @pytest.mark.asyncio
    async def test_create_page_no_books_raises(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.get = AsyncMock(return_value=_json_response({"data": []}))
            with pytest.raises(WikiError, match="No book_id"):
                await client.create_page("Title", "<p>body</p>")

    @pytest.mark.asyncio
    async def test_create_page_http_error(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.post = AsyncMock(return_value=_json_response({}, status_code=500))
            with pytest.raises(WikiError, match="Failed to create page"):
                await client.create_page("Title", "<p>body</p>", book_id=1)

    @pytest.mark.asyncio
    async def test_create_page_unexpected_error(self):
        async with WikiClient(config=WikiConfig(base_url="http://bookstack:80", api_token="t")) as client:
            client._session.post = AsyncMock(side_effect=RuntimeError("post failed"))
            with pytest.raises(WikiError, match="Error creating page"):
                await client.create_page("Title", "<p>body</p>", book_id=1)
