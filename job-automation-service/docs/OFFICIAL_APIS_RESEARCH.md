# Official APIs Research

## Overview

This document contains research findings on official APIs for job search platforms. This research helps determine which APIs are available, their pricing, rate limits, and integration requirements.

## Research Date

December 23, 2024

## LinkedIn API

### Availability
- **Status**: Available (with restrictions)
- **Type**: Partner API / Marketing API
- **Access**: Requires LinkedIn Partner Program approval

### Details
- **Authentication**: OAuth 2.0
- **Rate Limits**: Varies by partnership tier
- **Pricing**: Enterprise pricing (contact sales)
- **Features**:
  - Job postings search
  - Company information
  - Profile data (with permissions)
- **Limitations**:
  - Requires partnership approval
  - Strict ToS compliance
  - Limited to approved use cases
- **Documentation**: https://learn.microsoft.com/en-us/linkedin/

### Recommendation
- **For Production**: Requires partnership - not suitable for immediate use
- **Alternative**: Use LinkedIn Marketing API if available, or consider browser scraping with proper ToS compliance

## Indeed API

### Availability
- **Status**: Limited / Partner Program
- **Type**: Indeed Publisher API (for job boards)
- **Access**: Requires Indeed Publisher Program enrollment

### Details
- **Authentication**: API Key
- **Rate Limits**: Varies by partnership tier
- **Pricing**: Free for approved publishers
- **Features**:
  - Job search
  - Job details
  - Company information
- **Limitations**:
  - Only available to approved job board publishers
  - Must display Indeed branding
  - Strict usage guidelines
- **Documentation**: https://ads.indeed.com/jobroll/xmlfeed

### Recommendation
- **For Production**: Requires publisher approval - not suitable for personal use
- **Alternative**: Use Indeed RSS feeds or browser scraping

## Glassdoor API

### Availability
- **Status**: Not publicly available
- **Type**: Enterprise/Partner only
- **Access**: Contact sales for enterprise access

### Details
- **Authentication**: Unknown (enterprise only)
- **Rate Limits**: Unknown
- **Pricing**: Enterprise pricing
- **Features**: Unknown (enterprise only)
- **Limitations**: Not available for general use

### Recommendation
- **For Production**: Not available for general use
- **Alternative**: Browser scraping (with ToS compliance)

## ZipRecruiter API

### Availability
- **Status**: Partner Program
- **Type**: ZipRecruiter Partner API
- **Access**: Requires partnership application

### Details
- **Authentication**: API Key (after approval)
- **Rate Limits**: Varies by partnership tier
- **Pricing**: Free for approved partners
- **Features**:
  - Job search
  - Job details
  - Application tracking
- **Limitations**:
  - Requires partnership approval
  - Must comply with partner guidelines
- **Documentation**: Contact ZipRecruiter for partner information

### Recommendation
- **For Production**: Requires partnership - not suitable for immediate use
- **Alternative**: Browser scraping or aggregator APIs

## Summary

### Key Findings

1. **All major job sites require partnerships** for official API access
2. **No free public APIs** available for general use
3. **Partnership requirements** are strict and time-consuming
4. **Alternative approaches needed** for immediate implementation

### Recommended Approach

1. **Use Aggregator APIs** (Adzuna, The Muse, JSearch) - Free tiers available
2. **Browser Scraping** - With proper anti-bot evasion
3. **RSS Feeds** - Some sites offer RSS (limited functionality)
4. **Future**: Pursue partnerships if project scales

### Next Steps

1. Implement aggregator APIs (Adzuna, The Muse)
2. Enhance browser scraping capabilities
3. Monitor for API availability changes
4. Consider partnerships if project grows

