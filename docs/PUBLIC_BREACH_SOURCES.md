# Public Breach Sources Research and Configuration Guide

## Overview

This document provides guidance on finding and configuring reputable public breach data sources for the free email/domain breach checking system.

## Source Requirements

### Format Requirements

Public breach sources must provide data in one of these formats:

1. **JSON Format:**
   ```json
   {
     "breaches": [
       {
         "email": "user@example.com",
         "breach_name": "ExampleBreach",
         "breach_date": "2024-01-01",
         "data_classes": ["Email addresses", "Passwords"]
       }
     ]
   }
   ```

2. **CSV Format:**
   ```csv
   email,breach_name,breach_date,data_classes
   user@example.com,ExampleBreach,2024-01-01,"Email addresses, Passwords"
   ```

3. **Text Format:**
   ```
   user1@example.com
   user2@example.com
   user3@example.com
   ```

### Source Requirements

- **Publicly Accessible**: No authentication required
- **Legal**: Ensure you have permission to use the data
- **Reputable**: From trusted security researchers or organizations
- **Updated**: Regularly maintained breach data
- **Format**: JSON, CSV, or text format

## Finding Public Breach Sources

### GitHub Repositories

Search GitHub for repositories containing breach data:

1. **Search Terms:**
   - "breach database"
   - "data breach list"
   - "email breach data"
   - "compromised accounts"

2. **Repositories to Investigate:**
   - Security researcher repositories
   - Open-source security projects
   - Public breach databases

3. **GitHub Raw URLs:**
   - Format: `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`
   - Example: `https://raw.githubusercontent.com/user/repo/main/breaches.json`

### Security Forums and Publications

- Security researcher blogs and publications
- Security conference presentations (with public data)
- Academic research datasets (if publicly available)

### Public APIs

Some services may offer public APIs or data dumps:
- Check terms of service
- Verify data usage rights
- Ensure compliance with regulations

## Configuration

### Adding Sources

Add sources to your `.env` file:

```bash
SECURITY_PUBLIC_BREACH_SOURCES=https://raw.githubusercontent.com/user/repo/breaches.json,https://example.com/breach-list.csv
```

### Testing Sources

1. **Manual Test:**
   ```bash
   curl https://raw.githubusercontent.com/user/repo/breaches.json
   ```

2. **Via Script:**
   ```bash
   python scripts/populate_breach_database.py
   ```

3. **Via API:**
   ```bash
   POST /api/security/breaches/update-database?force=true
   ```

## Legal and Ethical Considerations

### Important Notes

1. **Permission**: Only use data you have permission to use
2. **Compliance**: Ensure compliance with GDPR, CCPA, and other regulations
3. **Privacy**: Respect user privacy and data protection laws
4. **Terms of Service**: Review and comply with source terms of service
5. **Attribution**: Provide proper attribution when required

### Data Handling

- Only store email addresses and breach metadata
- Never store passwords or other sensitive data
- Implement proper access controls
- Follow data retention policies
- Provide user notification mechanisms

## Example Sources (Research Required)

**Note:** These are examples of types of sources to look for. You must research and verify actual sources:

1. **GitHub Repositories:**
   - Search for "breach database" or "data breach list"
   - Verify repository is maintained and reputable
   - Check license and terms of use

2. **Security Researcher Publications:**
   - Academic papers with public datasets
   - Security conference presentations
   - Researcher blogs with breach data

3. **Open Source Projects:**
   - Security tools with breach databases
   - Community-maintained breach lists
   - Public security datasets

## Troubleshooting

### No Data Downloaded

- Verify source URLs are accessible
- Check source format matches requirements
- Review error logs for details
- Test source URL manually with curl

### Parsing Errors

- Verify data format matches expected structure
- Check for encoding issues (UTF-8 required)
- Review parser error messages
- Test with sample data

### Database Import Errors

- Check database connection
- Verify table creation (run `init_db()`)
- Review import error logs
- Check for duplicate key constraints

## Best Practices

1. **Multiple Sources**: Use multiple sources for better coverage
2. **Regular Updates**: Update database regularly (on-demand or scheduled)
3. **Source Validation**: Validate source data before importing
4. **Error Handling**: Implement graceful error handling
5. **Monitoring**: Monitor source availability and data quality
6. **Documentation**: Document all configured sources
7. **Testing**: Test with sample data before full import

## Next Steps

1. Research and identify reputable public breach sources
2. Verify source accessibility and format
3. Test data download and parsing
4. Configure sources in `.env` file
5. Run initial database population
6. Test email/domain lookups
7. Monitor and maintain sources

## Support

For issues or questions:
- Check [HIBP Integration Guide](./HIBP_INTEGRATION.md)
- Review [Breach Intake Guide](./BREACH_INTAKE_GUIDE.md)
- Check application logs for detailed error messages

