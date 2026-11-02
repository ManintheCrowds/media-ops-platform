"""Static acceptance checks for nginx Pi sync + auth rate-limit config."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NGINX_CONF = REPO_ROOT / "nginx" / "nginx.conf"


def test_nginx_auth_limit_and_pi_proxy():
    text = NGINX_CONF.read_text(encoding="utf-8")
    assert "zone=auth_limit" in text
    assert "location /api/auth/" in text
    # auth_limit must be applied (not only defined)
    auth_block_start = text.index("location /api/auth/")
    auth_slice = text[auth_block_start : auth_block_start + 400]
    assert "limit_req zone=auth_limit" in auth_slice

    assert "location /api/v1/pi/" in text
    pi_start = text.index("location /api/v1/pi/")
    pi_slice = text[pi_start : pi_start + 400]
    assert "proxy_pass http://education-service" in pi_slice
    assert "upstream education-service" in text
