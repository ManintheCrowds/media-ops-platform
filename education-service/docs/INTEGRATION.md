# Integration Guide

## Overview

The Educational System Service integrates with existing self-hosted services to provide a unified educational content management platform.

## Supported Services

- **BookStack**: Documentation and wiki pages
- **Gitea**: Code repositories and project files
- **Seafile**: File storage and document libraries
- **Jellyfin**: Media streaming for educational videos

## Configuration

### BookStack Integration

1. **Create OAuth2 Client in BookStack**:
   - Go to BookStack Settings > API
   - Create new OAuth2 client
   - Note the Client ID and Client Secret

2. **Configure in Educational Service**:
   ```env
   BOOKSTACK_URL=http://bookstack:80
   BOOKSTACK_API_ID=your-client-id
   BOOKSTACK_API_SECRET=your-client-secret
   ```

### Gitea Integration

1. **Generate API Token in Gitea**:
   - Go to Gitea Settings > Applications
   - Generate new token with appropriate permissions

2. **Configure in Educational Service**:
   ```env
   GITEA_URL=http://gitea:3000
   GITEA_API_TOKEN=your-api-token
   ```

### Seafile Integration

1. **Get API Token from Seafile**:
   - Login to Seafile admin panel
   - Generate API token

2. **Configure in Educational Service**:
   ```env
   SEAFILE_URL=http://seafile:8000
   SEAFILE_API_TOKEN=your-api-token
   ```

### Jellyfin Integration

1. **Get API Key from Jellyfin**:
   - Login to Jellyfin admin panel
   - Go to API Keys section
   - Generate new API key

2. **Configure in Educational Service**:
   ```env
   JELLYFIN_URL=http://jellyfin:8096
   JELLYFIN_API_KEY=your-api-key
   ```

## Linking Content

### Link Content to BookStack Page

```bash
curl -X POST http://localhost:8003/api/v1/integrations/bookstack/link \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "external_id": "123",
    "metadata": {}
  }'
```

### Link Content to Gitea Repository

```bash
curl -X POST "http://localhost:8003/api/v1/integrations/gitea/link?owner=user&repo=project&branch=main" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "external_id": "repo-id",
    "metadata": {}
  }'
```

### Link Content to Seafile File

```bash
curl -X POST "http://localhost:8003/api/v1/integrations/seafile/link?library_id=abc&file_path=/docs/lesson.pdf" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "external_id": "file-id",
    "metadata": {}
  }'
```

### Link Content to Jellyfin Media

```bash
curl -X POST http://localhost:8003/api/v1/integrations/jellyfin/link \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": 1,
    "external_id": "item-id",
    "metadata": {}
  }'
```

## Fetching External Resources

### Get BookStack Page

```bash
curl -X GET http://localhost:8003/api/v1/integrations/external/bookstack/123 \
  -H "Authorization: Bearer <token>"
```

### Get Seafile Library

```bash
curl -X GET http://localhost:8003/api/v1/integrations/external/seafile/library-id \
  -H "Authorization: Bearer <token>"
```

### Get Jellyfin Item

```bash
curl -X GET http://localhost:8003/api/v1/integrations/external/jellyfin/item-id \
  -H "Authorization: Bearer <token>"
```

## Content Aggregation

When fetching content items, external references are included in the `external_refs` field:

```json
{
  "id": 1,
  "title": "Python Tutorial",
  "external_refs": {
    "bookstack": {
      "page_id": 123,
      "book_id": 45
    },
    "gitea": {
      "owner": "user",
      "repo": "project",
      "branch": "main"
    },
    "seafile": {
      "library_id": "abc",
      "file_path": "/docs/tutorial.pdf"
    },
    "jellyfin": {
      "item_id": "xyz",
      "media_type": "video"
    }
  }
}
```

## Best Practices

1. **Verify External Resources**: Always verify that external resources exist before linking
2. **Handle Errors Gracefully**: External services may be unavailable
3. **Cache External Data**: Consider caching frequently accessed external resources
4. **Monitor Integration Health**: Regularly check integration service health
5. **Use Metadata**: Store additional metadata in the `metadata` field for custom use cases


