# Dashboard User Guide

Welcome to the Self-Hosted Platform Dashboard! This guide will help you understand and use all the features available in the dashboard.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Service Cards](#service-cards)
4. [Service Status Indicators](#service-status-indicators)
5. [System Information](#system-information)
6. [Using Services](#using-services)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Getting Started

### First Login

1. Navigate to the dashboard URL (typically `http://localhost/dashboard`)
2. Enter your username and password
3. Click "Login"
4. You'll be redirected to the main dashboard

### Dashboard Layout

The dashboard consists of:
- **Header**: Platform title, user info, help button, refresh button, and logout
- **Service Cards**: Grid of available services
- **System Information**: Overview of service health

---

## Dashboard Overview

### Header Section

The header contains:

- **Platform Title**: "Self-Hosted Platform"
- **Help Button** (`?`): Click to open the help modal with documentation
- **Username**: Your current logged-in username
- **Refresh Button**: Manually refresh service health status
- **Logout Button**: Sign out of the platform

### Service Cards Grid

The main area displays service cards in a responsive grid. Each card shows:
- Service icon
- Service name
- Brief description
- Detailed help text
- Health status indicator
- "Open" button

---

## Service Cards

### File Storage (Seafile)

**What it does:**
Enterprise file hosting with file syncing and sharing capabilities. Organize files into libraries and access them from anywhere.

**Features:**
- Create and manage file libraries
- Sync files across devices
- Share files with team members
- Access files from web, desktop, or mobile

**How to use:**
1. Click the "Open" button on the File Storage card
2. The service opens in a new tab
3. Log in with your credentials (if SSO is not configured)
4. Create libraries and start uploading files

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

### Media Server (Jellyfin)

**What it does:**
Organize and stream your media collection including movies, TV shows, music, and photos. Automatic metadata fetching and multi-device support.

**Features:**
- Organize media libraries
- Stream to any device
- Automatic metadata and artwork
- User management and parental controls

**How to use:**
1. Click the "Open" button on the Media Server card
2. Access your media library
3. Browse by type (Movies, TV Shows, Music, etc.)
4. Stream content to your devices

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

### Productivity (Wiki)

**What it does:**
Create and organize documentation, knowledge bases, and wiki pages. Perfect for team collaboration and documentation.

**Features:**
- Create and edit wiki pages
- Organize content hierarchically
- Search functionality
- Version history

**How to use:**
1. Click the "Open" button on the Productivity card
2. Navigate to your wiki
3. Create new pages or edit existing ones
4. Organize content using categories and tags

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

### Development Tools (Gitea)

**What it does:**
Self-hosted Git service for managing code repositories. Create repositories, track issues, and collaborate on projects.

**Features:**
- Git repository hosting
- Issue tracking
- Pull requests
- Code collaboration

**How to use:**
1. Click the "Open" button on the Development Tools card
2. Access your Git service
3. Create repositories or clone existing ones
4. Manage issues and pull requests

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

### Monitoring (Prometheus & Grafana)

**What it does:**
Monitor system health, performance metrics, and create custom dashboards. Includes Prometheus for metrics collection and Grafana for visualization.

**Features:**
- System metrics collection
- Custom dashboards
- Alerting
- Performance monitoring

**How to use:**
1. Click the "Open" button on the Monitoring card
2. Access Grafana dashboards
3. View system metrics and performance data
4. Create custom dashboards for your needs

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

### Security (Vaultwarden)

**What it does:**
Self-hosted password manager compatible with Bitwarden clients. Securely store passwords, credit cards, and secure notes.

**Features:**
- Password storage and management
- Secure note storage
- Credit card information storage
- Browser extension support
- Mobile app support

**How to use:**
1. Click the "Open" button on the Security card
2. Access your password vault
3. Add, edit, or view stored credentials
4. Use browser extensions or mobile apps for easy access

**Status Indicators:**
- 🟢 **Online**: Service is running and accessible
- 🔴 **Offline**: Service is not responding
- ⚪ **Not Registered**: Service is not configured in the system

---

## Service Status Indicators

Each service card displays a status indicator showing the current health of that service:

### Status Types

1. **🟢 Online (Healthy)**
   - Service is running and responding correctly
   - You can access the service normally
   - Green indicator dot

2. **🔴 Offline (Unhealthy)**
   - Service is not responding or has errors
   - You may not be able to access the service
   - Red indicator dot
   - Contact an administrator if this persists

3. **⚪ Not Registered (Unknown)**
   - Service is not registered in the system
   - Service may not be configured yet
   - Gray indicator dot
   - Contact an administrator to register the service

### Status Updates

- Status is automatically checked every 30 seconds
- Click the "Refresh" button to manually update status
- Status updates happen in the background without page reload

---

## System Information

The System Information section provides an overview of all registered services:

### Metrics Displayed

1. **Services**
   - Total number of services registered in the system
   - Includes all service types

2. **Healthy**
   - Number of services currently online and responding
   - These services are accessible

3. **Unhealthy**
   - Number of services with issues or not responding
   - These services may not be accessible

### Understanding the Metrics

- **All Healthy**: All services are running correctly
- **Some Unhealthy**: Some services have issues - check individual service cards
- **All Unhealthy**: System-wide issue - contact administrator
- **Zero Services**: No services are registered - contact administrator

---

## Using Services

### Opening a Service

1. Find the service card you want to access
2. Check the status indicator (should be green/online)
3. Click the "Open" button
4. The service opens in a new browser tab

### Service Authentication

- If Single Sign-On (SSO) is configured, you'll be automatically logged in
- If SSO is not configured, you may need to log in separately to each service
- Contact your administrator for authentication setup

### Service URLs

- Service URLs are configured by administrators
- If a service URL is not configured, you'll see an error message
- Contact an administrator to configure service URLs

---

## Keyboard Shortcuts

The dashboard supports the following keyboard shortcuts:

| Shortcut | Action |
|----------|--------|
| `?` or `H` | Show/hide help modal |
| `R` | Refresh service status |
| `Esc` | Close any open modals |

**Note:** Shortcuts don't work when typing in input fields.

---

## Troubleshooting

### Service Won't Open

**Problem:** Clicking "Open" doesn't open the service.

**Solutions:**
1. Check if pop-ups are blocked in your browser
2. Verify the service status is "Online" (green)
3. Check if the service URL is configured
4. Try refreshing the page
5. Contact an administrator

### Service Shows as Offline

**Problem:** Service status shows as "Offline" (red).

**Solutions:**
1. Wait a few moments - status updates every 30 seconds
2. Click the "Refresh" button to manually check
3. Verify the service is actually running
4. Check network connectivity
5. Contact an administrator if the issue persists

### Service Shows as "Not Registered"

**Problem:** Service status shows as "Not Registered" (gray).

**Solutions:**
1. The service may not be configured yet
2. Contact an administrator to register the service
3. Check if the service is supposed to be available

### Can't See Service Cards

**Problem:** Service cards are not visible or page looks broken.

**Solutions:**
1. Refresh the page (F5 or Ctrl+R)
2. Clear browser cache
3. Check browser console for errors
4. Try a different browser
5. Contact support

### Authentication Issues

**Problem:** Can't log in or session expires quickly.

**Solutions:**
1. Check your username and password
2. Clear browser cookies and try again
3. Check if your account is active
4. Contact an administrator

---

## FAQ

### Q: What is this platform?

**A:** This is a unified self-hosted platform that provides access to multiple services through a single dashboard. It includes file storage, media server, wiki, Git hosting, monitoring, and password management.

### Q: Do I need separate accounts for each service?

**A:** It depends on your setup. If Single Sign-On (SSO) is configured, you use one account. Otherwise, you may need separate accounts for each service. Contact your administrator.

### Q: How often is service status updated?

**A:** Service status is automatically checked every 30 seconds. You can also manually refresh using the "Refresh" button.

### Q: Can I customize the dashboard?

**A:** Currently, dashboard customization is limited. Contact your administrator for customization requests.

### Q: What should I do if a service is offline?

**A:** First, try refreshing the status. If it persists, contact your administrator as the service may need to be restarted or configured.

### Q: How do I get help?

**A:** Click the help button (`?`) in the header to see documentation. You can also refer to:
- This user guide
- API documentation (for developers)
- Quick start guide (for setup)

### Q: Can I access services directly without the dashboard?

**A:** Yes, if you know the service URLs, you can access them directly. However, the dashboard provides unified authentication and status monitoring.

### Q: What browsers are supported?

**A:** The dashboard works best with modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

### Q: Is my data secure?

**A:** Yes, all services are self-hosted, meaning your data stays on your server. The platform uses secure authentication and encrypted connections.

### Q: How do I report a bug or request a feature?

**A:** Contact your administrator or submit an issue through your organization's bug tracking system.

---

## Additional Resources

- **Platform Documentation**: See `README.md` for technical details
- **API Documentation**: See `API.md` for API endpoints
- **Quick Start Guide**: See `QUICKSTART.md` for setup instructions

---

## Support

For additional help:
1. Check the help modal (click `?` button)
2. Review service-specific documentation
3. Contact your system administrator
4. Check service logs (if you have access)

---

**Last Updated:** 2024  
**Version:** 1.0


