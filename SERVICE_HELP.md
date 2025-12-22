# Service-Specific Help Documentation

This document provides detailed information about each service available in the platform, including setup requirements, features, and usage tips.

---

## Table of Contents

1. [File Storage (Seafile)](#file-storage-seafile)
2. [Media Server (Jellyfin)](#media-server-jellyfin)
3. [Productivity (Wiki)](#productivity-wiki)
4. [Development Tools (Gitea)](#development-tools-gitea)
5. [Monitoring (Prometheus & Grafana)](#monitoring-prometheus--grafana)
6. [Security (Vaultwarden)](#security-vaultwarden)

---

## File Storage (Seafile)

### Overview

Seafile is an enterprise file hosting platform with file syncing and sharing capabilities. It's designed for teams and organizations that need secure, self-hosted file storage.

### Key Features

- **File Libraries**: Organize files into separate libraries
- **File Syncing**: Sync files across multiple devices
- **File Sharing**: Share files and folders with team members
- **Version Control**: Track file versions and restore previous versions
- **WebDAV Support**: Access files via WebDAV protocol
- **Mobile Apps**: Native apps for iOS and Android
- **Desktop Clients**: Desktop sync clients for Windows, macOS, and Linux

### Prerequisites

- Seafile service must be running and accessible
- Service must be registered in the platform
- User account must be created in Seafile
- API token may be required for some operations

### Accessing the Service

1. Click the "Open" button on the File Storage card
2. Log in with your Seafile credentials (if SSO is not configured)
3. Navigate to your libraries

### Common Tasks

#### Creating a Library

1. Click "New Library" in the Seafile interface
2. Enter a library name and description
3. Choose encryption (optional)
4. Click "Create"

#### Uploading Files

1. Navigate to the library where you want to upload files
2. Click "Upload" button
3. Select files from your computer
4. Wait for upload to complete

#### Sharing Files

1. Right-click on a file or folder
2. Select "Share"
3. Choose sharing method (link, email, etc.)
4. Set permissions and expiration (if needed)

### API Integration

The platform provides API endpoints for Seafile:

- `GET /api/gateway/file-storage/libraries` - List all libraries
- Additional endpoints may be available through the generic proxy

### Troubleshooting

**Problem:** Can't access Seafile
- **Solution:** Check if the service is registered and online
- Verify your credentials
- Check network connectivity

**Problem:** Files not syncing
- **Solution:** Check Seafile client status
- Verify sync settings
- Check available disk space

**Problem:** Can't create library
- **Solution:** Verify you have permissions
- Check Seafile server logs
- Contact administrator

---

## Media Server (Jellyfin)

### Overview

Jellyfin is a media server for organizing and streaming your media collection. It supports movies, TV shows, music, photos, and more.

### Key Features

- **Media Organization**: Automatically organize media by type
- **Metadata Fetching**: Automatic metadata and artwork
- **Multi-Device Streaming**: Stream to any device
- **User Management**: Multiple user accounts with parental controls
- **Transcoding**: On-the-fly media transcoding
- **Live TV**: Support for live TV and DVR (if configured)
- **Plugins**: Extensible with plugins

### Prerequisites

- Jellyfin service must be running and accessible
- Service must be registered in the platform
- Media files must be accessible to Jellyfin
- API key may be required for some operations

### Accessing the Service

1. Click the "Open" button on the Media Server card
2. Log in with your Jellyfin credentials (if SSO is not configured)
3. Browse your media library

### Common Tasks

#### Adding Media

1. Configure media libraries in Jellyfin settings
2. Point libraries to your media folders
3. Jellyfin will scan and organize media automatically

#### Streaming Media

1. Browse to the media you want to watch
2. Click play
3. Choose quality/transcoding options if needed
4. Media streams to your device

#### Creating Users

1. Go to Dashboard → Users
2. Click "Add User"
3. Enter user details
4. Set permissions and restrictions

### API Integration

The platform provides API endpoints for Jellyfin:

- `GET /api/gateway/media-server/libraries` - List media libraries
- `GET /api/gateway/media-server/recent?limit=10` - Get recently added media

### Troubleshooting

**Problem:** Media not showing up
- **Solution:** Check library paths are correct
- Verify file permissions
- Run a library scan manually

**Problem:** Can't stream media
- **Solution:** Check transcoding settings
- Verify network connectivity
- Check available resources (CPU, memory)

**Problem:** Metadata not loading
- **Solution:** Check internet connectivity
- Verify metadata provider settings
- Manually refresh metadata

---

## Productivity (Wiki)

### Overview

The Wiki service provides documentation and knowledge management capabilities. It's perfect for team documentation, knowledge bases, and collaborative writing.

### Key Features

- **Page Creation**: Create and edit wiki pages
- **Hierarchical Organization**: Organize pages in a tree structure
- **Search**: Full-text search across all pages
- **Version History**: Track changes and restore previous versions
- **Markdown Support**: Write in Markdown format
- **Collaboration**: Multiple users can edit pages
- **Attachments**: Attach files to pages

### Prerequisites

- Wiki service must be running and accessible
- Service must be registered in the platform
- User account must be created in the wiki
- API token may be required for some operations

### Accessing the Service

1. Click the "Open" button on the Productivity card
2. Log in with your wiki credentials (if SSO is not configured)
3. Navigate to pages

### Common Tasks

#### Creating a Page

1. Navigate to where you want to create the page
2. Click "New Page" or "Create Page"
3. Enter page title and content
4. Save the page

#### Editing a Page

1. Navigate to the page you want to edit
2. Click "Edit" button
3. Make your changes
4. Save the page

#### Organizing Pages

1. Use the page tree/navigation
2. Create parent and child pages
3. Use categories and tags
4. Link between pages

### API Integration

The platform provides API endpoints for the wiki:

- `GET /api/gateway/productivity/pages` - List all pages
- Additional endpoints may be available through the generic proxy

### Troubleshooting

**Problem:** Can't access wiki
- **Solution:** Check if the service is registered and online
- Verify your credentials
- Check network connectivity

**Problem:** Pages not saving
- **Solution:** Check file permissions
- Verify database connectivity
- Check server logs

**Problem:** Search not working
- **Solution:** Rebuild search index
- Check search service status
- Verify search configuration

---

## Development Tools (Gitea)

### Overview

Gitea is a self-hosted Git service for managing code repositories. It provides Git hosting, issue tracking, and collaboration features.

### Key Features

- **Git Hosting**: Host Git repositories
- **Issue Tracking**: Track bugs and feature requests
- **Pull Requests**: Code review and collaboration
- **Wiki**: Repository wikis for documentation
- **Releases**: Manage software releases
- **Organizations**: Organize repositories and teams
- **Webhooks**: Integrate with other services

### Prerequisites

- Gitea service must be running and accessible
- Service must be registered in the platform
- User account must be created in Gitea
- API token may be required for some operations

### Accessing the Service

1. Click the "Open" button on the Development Tools card
2. Log in with your Gitea credentials (if SSO is not configured)
3. Browse repositories

### Common Tasks

#### Creating a Repository

1. Click "New Repository"
2. Enter repository name and description
3. Choose visibility (public/private)
4. Initialize with README (optional)
5. Click "Create Repository"

#### Cloning a Repository

1. Navigate to the repository
2. Click "Clone" button
3. Copy the clone URL
4. Use `git clone <url>` in your terminal

#### Creating an Issue

1. Navigate to the repository
2. Click "Issues" tab
3. Click "New Issue"
4. Enter title and description
5. Assign labels and assignees
6. Submit the issue

### API Integration

The platform provides API endpoints for Gitea:

- `GET /api/gateway/dev-tools/repositories?page=1&limit=20` - List repositories

### Troubleshooting

**Problem:** Can't access Gitea
- **Solution:** Check if the service is registered and online
- Verify your credentials
- Check network connectivity

**Problem:** Can't push to repository
- **Solution:** Verify SSH keys or credentials
- Check repository permissions
- Verify Git configuration

**Problem:** Issues not showing
- **Solution:** Check repository settings
- Verify issue tracker is enabled
- Check user permissions

---

## Monitoring (Prometheus & Grafana)

### Overview

The monitoring service combines Prometheus (metrics collection) and Grafana (visualization) to provide comprehensive system monitoring and alerting.

### Key Features

- **Metrics Collection**: Collect metrics from various sources
- **Dashboards**: Create custom visualization dashboards
- **Alerting**: Set up alerts based on metrics
- **Query Language**: PromQL for querying metrics
- **Data Sources**: Connect to multiple data sources
- **Templates**: Dashboard templates for common use cases

### Prerequisites

- Prometheus service must be running
- Grafana service must be running
- Services must be registered in the platform
- Metrics exporters must be configured (for Prometheus)
- Data sources must be configured (for Grafana)

### Accessing the Service

1. Click the "Open" button on the Monitoring card
2. This typically opens Grafana
3. Log in with your Grafana credentials (if SSO is not configured)

### Common Tasks

#### Viewing Dashboards

1. Navigate to Dashboards in Grafana
2. Browse available dashboards
3. Select a dashboard to view
4. Customize time range and refresh rate

#### Creating a Dashboard

1. Click "Create" → "Dashboard"
2. Add panels (graphs, tables, etc.)
3. Configure queries and visualizations
4. Save the dashboard

#### Querying Metrics (Prometheus)

1. Access Prometheus query interface
2. Enter PromQL query
3. View results
4. Use query builder for assistance

### API Integration

The platform provides API endpoints for monitoring:

- `GET /api/gateway/monitoring/metrics?query=up` - Query Prometheus metrics
- `GET /api/gateway/monitoring/dashboards` - List Grafana dashboards

### Troubleshooting

**Problem:** Can't access Grafana
- **Solution:** Check if the service is registered and online
- Verify your credentials
- Check network connectivity

**Problem:** No metrics showing
- **Solution:** Check Prometheus targets
- Verify exporters are running
- Check scrape configuration

**Problem:** Dashboards not loading
- **Solution:** Check data source configuration
- Verify data source connectivity
- Check dashboard permissions

---

## Security (Vaultwarden)

### Overview

Vaultwarden is a self-hosted password manager compatible with Bitwarden clients. It provides secure storage for passwords, credit cards, and secure notes.

### Key Features

- **Password Storage**: Securely store passwords
- **Credit Card Storage**: Store payment information
- **Secure Notes**: Store sensitive text information
- **Browser Extensions**: Integrate with web browsers
- **Mobile Apps**: Native mobile applications
- **Two-Factor Authentication**: Additional security layer
- **Sharing**: Share items with other users
- **Organizations**: Team password management

### Prerequisites

- Vaultwarden service must be running and accessible
- Service must be registered in the platform
- User account must be created in Vaultwarden
- Admin token may be required for admin operations

### Accessing the Service

1. Click the "Open" button on the Security card
2. Log in with your Vaultwarden credentials (if SSO is not configured)
3. Access your vault

### Common Tasks

#### Adding a Password

1. Click "Add Item"
2. Select item type (Login, Card, Secure Note, etc.)
3. Enter information
4. Save the item

#### Using Browser Extension

1. Install Bitwarden browser extension
2. Configure extension to point to your Vaultwarden instance
3. Log in through the extension
4. Use auto-fill features

#### Setting Up Two-Factor Authentication

1. Go to Account Settings
2. Enable Two-Factor Authentication
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes

### API Integration

The platform provides API endpoints for Vaultwarden (admin only):

- `GET /api/gateway/security/stats` - Get Vaultwarden statistics

### Troubleshooting

**Problem:** Can't access Vaultwarden
- **Solution:** Check if the service is registered and online
- Verify your credentials
- Check network connectivity

**Problem:** Browser extension not working
- **Solution:** Verify extension is configured correctly
- Check server URL in extension settings
- Verify SSL certificate (if using HTTPS)

**Problem:** Can't sync vault
- **Solution:** Check network connectivity
- Verify server is accessible
- Check sync settings in client

---

## General Service Tips

### Service Status

- Always check service status before trying to access
- Green status means service is online and accessible
- Red status means service has issues
- Gray status means service is not registered

### Authentication

- If SSO is configured, you'll be automatically logged in
- Otherwise, you may need separate credentials for each service
- Contact your administrator for authentication setup

### Service URLs

- Service URLs are configured by administrators
- If a URL is not configured, contact an administrator
- URLs can be changed by administrators without affecting your access

### Getting Help

- Check service-specific documentation
- Review service logs (if you have access)
- Contact your system administrator
- Check the main dashboard help (click `?` button)

---

**Last Updated:** 2024  
**Version:** 1.0




