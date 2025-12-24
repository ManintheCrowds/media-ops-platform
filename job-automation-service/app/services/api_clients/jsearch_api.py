"""JSearch API client for job search (via RapidAPI)."""

import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode
import httpx
from app.config import settings
from app.services.api_clients.base_api_client import BaseAPIClient

logger = logging.getLogger(__name__)


class JSearchAPIClient(BaseAPIClient):
    """JSearch API client (via RapidAPI)."""
    
    BASE_URL = "https://jsearch.p.rapidapi.com/search"
    
    def __init__(self):
        """Initialize JSearch API client."""
        api_key = settings.jsearch_api_key
        super().__init__("jsearch", api_key)
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search JSearch for jobs.
        
        Args:
            query: Job search query
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        # #region agent log
        import json
        import time
        from pathlib import Path
        debug_log_path = Path("c:\\Users\\artin\\software\\.cursor\\debug.log")
        try:
            log_entry = {
                "sessionId": "jsearch-debug",
                "runId": f"jsearch-{int(time.time())}",
                "hypothesisId": "H1",
                "location": "jsearch_api.py:search_jobs",
                "message": "JSearch API search started",
                "data": {
                    "query": query,
                    "location": location,
                    "limit": limit,
                    "api_key_present": bool(self.api_key),
                    "api_key_length": len(self.api_key) if self.api_key else 0,
                    "api_key_prefix": self.api_key[:10] + "..." if self.api_key and len(self.api_key) > 10 else "N/A",
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        if not self.api_key:
            logger.error("JSearch API key not configured")
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "jsearch-debug",
                    "runId": f"jsearch-{int(time.time())}",
                    "hypothesisId": "H1",
                    "location": "jsearch_api.py:search_jobs",
                    "message": "JSearch API key missing",
                    "data": {"error": "API key not configured"},
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            return []
        
        await self.rate_limiter.wait()
        
        params = {
            "query": f"{query} in {location}",
            "page": "1",
            "num_pages": "1",
        }
        
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,  # Try both formats
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        
        # Also try alternative header format (some RapidAPI endpoints use different format)
        # RapidAPI documentation shows both X-RapidAPI-Key and X-RapidAPI-Key formats
        
        # #region agent log
        try:
            log_entry = {
                "sessionId": "jsearch-debug",
                "runId": f"jsearch-{int(time.time())}",
                "hypothesisId": "H5",
                "location": "jsearch_api.py:search_jobs",
                "message": "JSearch API request prepared",
                "data": {
                    "url": url,
                    "base_url": self.BASE_URL,
                    "params": params,
                    "headers_present": bool(headers),
                    "header_keys": list(headers.keys()),
                    "rapidapi_host": headers.get("X-RapidAPI-Host"),
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        try:
            # #region agent log
            request_start = time.time()
            # #endregion agent log
            
            response = await self.client.get(url, headers=headers)
            
            # #region agent log
            request_elapsed = time.time() - request_start
            try:
                log_entry = {
                    "sessionId": "jsearch-debug",
                    "runId": f"jsearch-{int(time.time())}",
                    "hypothesisId": "H2",
                    "location": "jsearch_api.py:search_jobs",
                    "message": "JSearch API response received",
                    "data": {
                        "status_code": response.status_code,
                        "elapsed_time_ms": round(request_elapsed * 1000, 2),
                        "response_headers": dict(response.headers),
                        "response_size": len(response.text) if hasattr(response, 'text') else 0,
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            results = data.get("data", [])
            
            for result in results[:limit]:
                job = self._normalize_job_data({
                    "title": result.get("job_title", ""),
                    "company": result.get("employer_name", ""),
                    "location": result.get("job_city", "") + ", " + result.get("job_state", ""),
                    "description": result.get("job_description", ""),
                    "url": result.get("job_apply_link", ""),
                    "id": result.get("job_id", ""),
                    "posted_date": result.get("job_posted_at_datetime_utc", ""),
                    "salary": result.get("job_min_salary", "") if result.get("job_min_salary") else "",
                })
                jobs.append(job)
            
            logger.info(f"JSearch API returned {len(jobs)} jobs")
            
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "jsearch-debug",
                    "runId": f"jsearch-{int(time.time())}",
                    "hypothesisId": "H2",
                    "location": "jsearch_api.py:search_jobs",
                    "message": "JSearch API success",
                    "data": {
                        "jobs_found": len(jobs),
                        "results_count": len(results),
                        "data_keys": list(data.keys()) if isinstance(data, dict) else [],
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            return jobs
            
        except httpx.HTTPStatusError as e:
            # Extract error message from response
            error_message = f"HTTP {e.response.status_code}"
            try:
                response_json = e.response.json()
                if isinstance(response_json, dict) and "message" in response_json:
                    error_message = response_json["message"]
                    logger.error(f"JSearch API error: {error_message}")
                    
                    # Provide helpful guidance for common errors
                    if "not subscribed" in error_message.lower():
                        logger.warning("JSearch API: You need to subscribe to the JSearch API on RapidAPI")
                        logger.warning("Visit: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
                else:
                    logger.error(f"JSearch API HTTP error: {e.response.status_code}")
            except Exception:
                logger.error(f"JSearch API HTTP error: {e.response.status_code}")
            
            # #region agent log
            try:
                response_text = ""
                response_json = {}
                try:
                    response_text = e.response.text[:500] if hasattr(e.response, 'text') else ""
                    response_json = e.response.json() if hasattr(e.response, 'json') else {}
                except Exception:
                    pass
                
                log_entry = {
                    "sessionId": "jsearch-debug",
                    "runId": f"jsearch-{int(time.time())}",
                    "hypothesisId": "H1,H2,H4",
                    "location": "jsearch_api.py:search_jobs",
                    "message": "JSearch API HTTP error",
                    "data": {
                        "status_code": e.response.status_code,
                        "error_type": "HTTPStatusError",
                        "error_message": error_message,
                        "response_text_preview": response_text,
                        "response_json": response_json,
                        "response_headers": dict(e.response.headers) if hasattr(e.response, 'headers') else {},
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            return []
        except Exception as e:
            logger.error(f"JSearch API error: {e}")
            
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "jsearch-debug",
                    "runId": f"jsearch-{int(time.time())}",
                    "hypothesisId": "H5,H6",
                    "location": "jsearch_api.py:search_jobs",
                    "message": "JSearch API exception",
                    "data": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            return []

