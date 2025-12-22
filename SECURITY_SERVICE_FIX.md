# Security Service Fix - SQLAlchemy Metadata Conflict

## ✅ Issue Fixed

**Problem**: SQLAlchemy error - `Attribute name 'metadata' is reserved when using the Declarative API`

**Root Cause**: SQLAlchemy's Declarative API reserves the name `metadata` for table metadata, so it cannot be used as a column name.

**Solution**: Renamed all `metadata` columns to specific names:
- `SecurityEvent.metadata` → `SecurityEvent.event_metadata`
- `ThreatIntelligence.metadata` → `ThreatIntelligence.threat_metadata`
- `FirewallRule.metadata` → `FirewallRule.rule_metadata`
- `VulnerabilityScan.metadata` → `VulnerabilityScan.vuln_metadata`
- `PatchStatus.metadata` → `PatchStatus.patch_metadata`
- `SecurityIncident.metadata` → `SecurityIncident.incident_metadata`

## ✅ Verification

- **Models Load Test**: ✅ Passed
- **Code Changes**: ✅ All files updated
- **References Updated**: ✅ All code references updated

## ⚠️ Current Issue: Port 8001 in Use

The security service cannot start because port 8001 is already allocated.

**To fix:**

1. **Find what's using port 8001:**
   ```powershell
   netstat -ano | findstr :8001
   ```

2. **Stop the process** (if safe to do so) or **change the port** in docker-compose.yml:
   ```yaml
   ports:
     - "8002:8001"  # Use 8002 externally, 8001 internally
   ```

3. **Start the service:**
   ```bash
   docker-compose up -d security-service
   ```

## 📋 Next Steps

1. **Free port 8001** or change the external port
2. **Start security service**: `docker-compose up -d security-service`
3. **Verify it's running**: `docker logs platform-security`
4. **Test VirusTotal integration**: `curl http://localhost:8001/api/security/threats/ip/8.8.8.8`

## ✅ Status

- [x] SQLAlchemy metadata conflict fixed
- [x] Code changes verified
- [x] Models load successfully
- [ ] Port 8001 freed/changed
- [ ] Service started
- [ ] Integration tested

---

**The VirusTotal API key is configured and ready. Once the port issue is resolved, the service will start and automatically use VirusTotal for threat intelligence.**

