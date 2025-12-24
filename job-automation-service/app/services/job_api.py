"""Job API integrations and scrapers for different sources."""

import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote
from app.services.job_scraper import BaseJobScraper

logger = logging.getLogger(__name__)


class IndeedScraper(BaseJobScraper):
    """Indeed job scraper."""
    
    def __init__(self):
        super().__init__("indeed")
        self.base_url = "https://www.indeed.com"
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search Indeed for jobs.
        
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
        debug_log_path = Path("C:/Users/artin/software/.cursor/debug.log")
        search_start_time = time.time()
        try:
            log_entry = {
                "sessionId": "scraper-debug",
                "runId": f"search-{int(time.time())}",
                "hypothesisId": "H3",
                "location": "job_api.py:IndeedScraper.search_jobs",
                "message": "Starting Indeed job search",
                "data": {
                    "query": query,
                    "location": location,
                    "limit": limit,
                    "source": "indeed",
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        jobs = []
        start = 0
        
        while len(jobs) < limit:
            # Build search URL
            params = {
                "q": query,
                "l": location,
                "start": start,
            }
            search_url = f"{self.base_url}/jobs?{urlencode(params)}"
            
            logger.info(f"Searching Indeed: {search_url}")
            response = await self._fetch_page(search_url)
            
            if not response:
                logger.warning("Failed to fetch Indeed search page")
                break
            
            soup = self._parse_html(response.text)
            job_cards = soup.find_all("div", class_="job_seen_beacon")
            
            # #region agent log
            try:
                log_entry = {
                    "sessionId": "scraper-debug",
                    "runId": f"search-{int(time.time())}",
                    "hypothesisId": "H4",
                    "location": "job_api.py:IndeedScraper.search_jobs",
                    "message": "Parsed Indeed search page",
                    "data": {
                        "url": search_url,
                        "job_cards_found": len(job_cards),
                        "html_size": len(response.text),
                        "source": "indeed",
                    },
                    "timestamp": int(time.time() * 1000)
                }
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            if not job_cards:
                logger.info("No more job cards found")
                break
            
            for card in job_cards:
                if len(jobs) >= limit:
                    break
                
                job = self._parse_job_card(card)
                if job:
                    jobs.append(job)
            
            # Check for next page
            next_button = soup.find("a", {"aria-label": re.compile(r"Next", re.I)})
            if not next_button:
                break
            
            start += 10  # Indeed shows 10 jobs per page
            
            # Safety limit
            if start > 100:  # Max 100 results
                break
        
        # #region agent log
        search_elapsed = time.time() - search_start_time
        try:
            log_entry = {
                "sessionId": "scraper-debug",
                "runId": f"search-{int(time.time())}",
                "hypothesisId": "H5",
                "location": "job_api.py:IndeedScraper.search_jobs",
                "message": "Completed Indeed job search",
                "data": {
                    "query": query,
                    "location": location,
                    "jobs_found": len(jobs),
                    "elapsed_time_ms": round(search_elapsed * 1000, 2),
                    "source": "indeed",
                    "jobs_with_title": sum(1 for j in jobs if j.get("title")),
                    "jobs_with_url": sum(1 for j in jobs if j.get("url")),
                    "jobs_with_description": sum(1 for j in jobs if j.get("description")),
                },
                "timestamp": int(time.time() * 1000)
            }
            with open(debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        return jobs[:limit]
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a single job card from Indeed.
        
        Args:
            card: BeautifulSoup element for job card
        
        Returns:
            Job dictionary or None
        """
        try:
            # Title and link
            title_elem = card.find("h2", class_="jobTitle")
            if not title_elem:
                return None
            
            title_link = title_elem.find("a")
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            relative_url = title_link.get("href", "")
            url = f"{self.base_url}{relative_url}" if relative_url.startswith("/") else relative_url
            
            # Company
            company_elem = card.find("span", class_="companyName")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find("div", class_="companyLocation")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Salary (optional)
            salary_elem = card.find("span", class_="salary-snippet")
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            # Job type (full-time, contract, etc.)
            job_type_elem = card.find("span", class_="jobType")
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else None
            
            # Remote indicator
            remote = "remote" in location.lower() or "remote" in title.lower()
            
            # Description snippet
            snippet_elem = card.find("div", class_="job-snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Get full description by fetching job page
            description = self._get_full_description(url) if url else snippet
            
            # Generate source_id from URL
            source_id = self._extract_source_id(url)
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": description or snippet,
                "salary_range": salary,
                "job_type": job_type,
                "remote": remote,
                "source_id": source_id,
                "raw_data": {
                    "snippet": snippet,
                    "card_html": str(card),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Indeed job card: {e}")
            return None
    
    async def _get_full_description(self, url: str) -> Optional[str]:
        """Fetch full job description from job page.
        
        Args:
            url: Job URL
        
        Returns:
            Full description text or None
        """
        try:
            response = await self._fetch_page(url)
            if not response:
                return None
            
            soup = self._parse_html(response.text)
            description_elem = soup.find("div", id="jobDescriptionText")
            
            if description_elem:
                return description_elem.get_text(strip=True)
            
            # Fallback: look for other description containers
            description_elem = soup.find("div", class_="jobsearch-jobDescriptionText")
            if description_elem:
                return description_elem.get_text(strip=True)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not fetch full description from {url}: {e}")
            return None
    
    def _extract_source_id(self, url: str) -> str:
        """Extract unique source ID from Indeed URL.
        
        Args:
            url: Job URL
        
        Returns:
            Source ID string
        """
        # Indeed URLs typically have format: /viewjob?jk=JOB_ID
        match = re.search(r"jk=([^&]+)", url)
        if match:
            return f"indeed_{match.group(1)}"
        
        # Fallback: use URL hash
        return f"indeed_{hash(url)}"


class LinkedInScraper(BaseJobScraper):
    """LinkedIn job scraper (basic implementation).
    
    Note: LinkedIn has strict ToS. This is a basic implementation.
    For production, consider using LinkedIn API.
    """
    
    def __init__(self):
        super().__init__("linkedin")
        self.base_url = "https://www.linkedin.com"
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search LinkedIn for jobs.
        
        Note: LinkedIn requires authentication and has anti-scraping measures.
        This is a basic implementation that may not work without proper setup.
        
        Args:
            query: Job search query
            location: Location string
            limit: Maximum number of jobs to return
        
        Returns:
            List of job dictionaries
        """
        # LinkedIn search URL format
        # Note: This may require authentication
        params = {
            "keywords": query,
            "location": location,
        }
        search_url = f"{self.base_url}/jobs/search?{urlencode(params)}"
        
        logger.warning("LinkedIn scraping requires authentication and may violate ToS")
        logger.info(f"Searching LinkedIn: {search_url}")
        
        response = await self._fetch_page(search_url)
        
        if not response:
            logger.warning("Failed to fetch LinkedIn search page")
            return []
        
        # LinkedIn uses dynamic content, so basic scraping may not work
        # This is a placeholder implementation
        soup = self._parse_html(response.text)
        jobs = []
        
        # LinkedIn job cards have class "job-search-card"
        job_cards = soup.find_all("div", class_="job-search-card")
        
        for card in job_cards[:limit]:
            job = self._parse_job_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a LinkedIn job card."""
        try:
            # Title
            title_elem = card.find("h3", class_="base-search-card__title")
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # Link
            link_elem = card.find("a", class_="base-card__full-link")
            url = link_elem.get("href", "") if link_elem else ""
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"
            
            # Company
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find("span", class_="job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Description snippet
            snippet_elem = card.find("p", class_="job-search-card__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            source_id = f"linkedin_{hash(url)}" if url else f"linkedin_{hash(title)}"
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": snippet,
                "source_id": source_id,
                "raw_data": {
                    "card_html": str(card),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job card: {e}")
            return None


class GlassdoorScraper(BaseJobScraper):
    """Glassdoor job scraper."""
    
    def __init__(self):
        super().__init__("glassdoor")
        self.base_url = "https://www.glassdoor.com"
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search Glassdoor for jobs."""
        params = {
            "sc.keyword": query,
            "locT": "C",
            "locId": location,  # This may need to be a location ID
        }
        search_url = f"{self.base_url}/Job/jobs.htm?{urlencode(params)}"
        
        logger.info(f"Searching Glassdoor: {search_url}")
        response = await self._fetch_page(search_url)
        
        if not response:
            logger.warning("Failed to fetch Glassdoor search page")
            return []
        
        soup = self._parse_html(response.text)
        jobs = []
        
        # Glassdoor job listings
        job_cards = soup.find_all("li", class_="react-job-listing")
        
        for card in job_cards[:limit]:
            job = self._parse_job_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a Glassdoor job card."""
        try:
            # Title and link
            title_elem = card.find("a", class_="jobLink")
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"
            
            # Company
            company_elem = card.find("div", class_="d-flex")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find("span", class_="loc")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Salary
            salary_elem = card.find("span", class_="salary")
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            source_id = f"glassdoor_{hash(url)}" if url else f"glassdoor_{hash(title)}"
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": "",
                "salary_range": salary,
                "source_id": source_id,
                "raw_data": {
                    "card_html": str(card),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Glassdoor job card: {e}")
            return None


class ZipRecruiterScraper(BaseJobScraper):
    """ZipRecruiter job scraper."""
    
    def __init__(self):
        super().__init__("ziprecruiter")
        self.base_url = "https://www.ziprecruiter.com"
    
    async def search_jobs(
        self,
        query: str,
        location: str,
        limit: int = 25
    ) -> List[Dict]:
        """Search ZipRecruiter for jobs."""
        params = {
            "search": query,
            "location": location,
        }
        search_url = f"{self.base_url}/jobs/search?{urlencode(params)}"
        
        logger.info(f"Searching ZipRecruiter: {search_url}")
        response = await self._fetch_page(search_url)
        
        if not response:
            logger.warning("Failed to fetch ZipRecruiter search page")
            return []
        
        soup = self._parse_html(response.text)
        jobs = []
        
        # ZipRecruiter job listings
        job_cards = soup.find_all("article", class_="job_result")
        
        for card in job_cards[:limit]:
            job = self._parse_job_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    def _parse_job_card(self, card) -> Optional[Dict]:
        """Parse a ZipRecruiter job card."""
        try:
            # Title and link
            title_elem = card.find("a", class_="job_link")
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"
            
            # Company
            company_elem = card.find("a", class_="company_name")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find("a", class_="company_location")
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Description
            description_elem = card.find("p", class_="job_snippet")
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            source_id = f"ziprecruiter_{hash(url)}" if url else f"ziprecruiter_{hash(title)}"
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": description,
                "source_id": source_id,
                "raw_data": {
                    "card_html": str(card),
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing ZipRecruiter job card: {e}")
            return None

