import asyncio
import sys
from app.api.jobs import search_jobs
from app.schemas.job import JobSearchRequest
from app.database import SessionLocal

async def test():
    db = SessionLocal()
    try:
        request = JobSearchRequest(
            query=\"Python developer\",
            location=\"Minneapolis, MN\",
            sources=[\"adzuna\"],
            limit=10,
            min_match_score=0.0
        )
        print(\"Calling search_jobs...\")
        result = await search_jobs(request, db)
        print(f\"Result: {result.count} jobs, sources: {result.sources_searched}\")
    except Exception as e:
        print(f\"ERROR: {type(e).__name__}: {e}\", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == \"__main__\":
    asyncio.run(test())
