# Educational System Service API Documentation

## Overview

The Educational System Service provides a comprehensive API for managing educational content, projects, taxonomy, and Raspberry Pi device integration.

**Base URL**: `http://localhost:8003/api/v1`

## Authentication

All API endpoints (except `/health`) require authentication using JWT tokens from the main platform.

**Header Format**:
```
Authorization: Bearer <token>
```

Get a token by authenticating with the main platform:
```bash
curl -X POST http://platform:8000/api/auth/token \
  -d "username=your_username&password=your_password"
```

## Content Management API

### Create Content

**POST** `/education/content`

Create a new content item.

**Request Body**:
```json
{
  "project_id": 1,
  "title": "Introduction to Python",
  "slug": "introduction-to-python",
  "description": "Learn the basics of Python programming",
  "body": "Python is a high-level programming language...",
  "content_type": "lesson",
  "metadata": {},
  "external_refs": {},
  "parent_id": null
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "project_id": 1,
  "title": "Introduction to Python",
  "content_type": "lesson",
  "version": 1,
  "created_by": "user123",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### List Content

**GET** `/education/content?project_id=1&page=1&page_size=20`

List content items with filtering and pagination.

**Query Parameters**:
- `project_id` (optional): Filter by project
- `content_type` (optional): Filter by content type (lesson, video, document, assessment, project_template)
- `search` (optional): Search in title, description, and body
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

### Get Content

**GET** `/education/content/{content_id}`

Get a specific content item.

### Update Content

**PUT** `/education/content/{content_id}`

Update a content item.

### Delete Content

**DELETE** `/education/content/{content_id}`

Delete a content item.

### Content Versions

**GET** `/education/content/{content_id}/versions`

List all versions of a content item.

**GET** `/education/content/{content_id}/versions/{version_number}`

Get a specific version.

**POST** `/education/content/{content_id}/revert/{version_number}`

Revert content to a specific version.

## Project Management API

### Create Project

**POST** `/education/projects`

**Request Body**:
```json
{
  "organization_id": 1,
  "name": "Python Programming Course",
  "slug": "python-programming",
  "description": "Complete Python programming course",
  "status": "draft",
  "metadata": {}
}
```

### List Projects

**GET** `/education/projects?organization_id=1&status=active`

### Get Project Content

**GET** `/education/projects/{project_id}/content`

Get all content items in a project.

## Taxonomy & Tagging API

### Tags

**POST** `/education/tags` - Create tag
**GET** `/education/tags` - List tags
**POST** `/education/content/{content_id}/tags/{tag_id}` - Add tag to content
**DELETE** `/education/content/{content_id}/tags/{tag_id}` - Remove tag from content

### Taxonomy

**POST** `/education/taxonomy` - Create taxonomy node
**GET** `/education/taxonomy` - Get taxonomy tree
**PUT** `/education/taxonomy/{node_id}` - Update taxonomy node
**POST** `/education/content/{content_id}/taxonomy/{node_id}` - Add taxonomy to content

## Integration API

### Link to BookStack

**POST** `/integrations/bookstack/link`

**Request Body**:
```json
{
  "content_id": 1,
  "external_id": "123",
  "metadata": {}
}
```

### Link to Gitea

**POST** `/integrations/gitea/link?owner=user&repo=project&branch=main`

### Link to Seafile

**POST** `/integrations/seafile/link?library_id=abc&file_path=/docs/lesson.pdf`

### Link to Jellyfin

**POST** `/integrations/jellyfin/link`

## Raspberry Pi API

### Device Management

**POST** `/pi/devices/register` - Register new device
**GET** `/pi/devices/{device_id}` - Get device info
**PUT** `/pi/devices/{device_id}` - Update device config
**GET** `/pi/devices/{device_id}/status` - Get sync status

### Content Synchronization

**GET** `/pi/devices/{device_id}/sync/check` - Check for updates
**POST** `/pi/devices/{device_id}/sync/request` - Request sync package
**GET** `/pi/devices/{device_id}/sync/packages/{package_id}/download` - Download package
**POST** `/pi/devices/{device_id}/sync/complete` - Mark sync complete

### Content Delivery

**GET** `/pi/devices/{device_id}/content` - Get content list for device
**GET** `/pi/devices/{device_id}/content/{content_id}` - Get content item
**GET** `/pi/devices/{device_id}/display/config` - Get display configuration

### IoT Integration

**POST** `/pi/devices/{device_id}/sensors/data` - Submit sensor data
**GET** `/pi/devices/{device_id}/sensors/config` - Get sensor configuration
**GET** `/pi/devices/{device_id}/sensors/data` - Query sensor data

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Status Codes**:
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no content
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error



