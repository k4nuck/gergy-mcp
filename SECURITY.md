# Security Configuration Guide

## Environment Variables

This project uses environment variables to securely manage sensitive configuration like database credentials and API keys.

### Required Environment Variables

#### Database Configuration
```bash
# PostgreSQL connection details
POSTGRES_USER=your_database_username
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_DB=gergy_knowledge
POSTGRES_HOST=localhost  # or your database host
POSTGRES_PORT=5432

# Complete connection URL
DATABASE_URL=postgresql://your_username:your_password@host:port/database_name
```

#### API Keys
```bash
# Anthropic API key for Claude integration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### Optional Configuration
```bash
# Redis connection
REDIS_URL=redis://localhost:6379

# Server budget limits (USD per day)
FINANCIAL_BUDGET_LIMIT=15.0
FAMILY_BUDGET_LIMIT=10.0
LIFESTYLE_BUDGET_LIMIT=8.0
PROFESSIONAL_BUDGET_LIMIT=12.0
HOME_BUDGET_LIMIT=8.0
```

### Setup Instructions

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Update `.env` with your actual credentials:**
   - Replace `your_db_user` with your PostgreSQL username
   - Replace `your_secure_password` with your PostgreSQL password
   - Replace `your_anthropic_api_key_here` with your actual Anthropic API key
   - Update host/port if using remote database

3. **Verify the `.env` file is gitignored:**
   ```bash
   grep "^\.env$" .gitignore
   ```

### Production Security

#### Database Security
- **Use strong passwords:** Minimum 16 characters with mixed case, numbers, and symbols
- **Create dedicated database user:** Don't use admin/root accounts
- **Enable SSL/TLS:** Use `sslmode=require` in DATABASE_URL for production
- **Network security:** Restrict database access to application servers only
- **Regular rotation:** Change database passwords regularly

#### API Key Security
- **Environment isolation:** Use different API keys for dev/staging/production
- **Key rotation:** Rotate API keys regularly
- **Access monitoring:** Monitor API usage for suspicious activity
- **Scope limitation:** Use API keys with minimal required permissions

#### Docker Production
For Docker deployments, use Docker secrets or environment variable injection:

```yaml
# docker-compose.prod.yml
services:
  financial-server:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    # Never hardcode secrets in compose files
```

### Security Checklist

- [ ] No hardcoded credentials in source code
- [ ] `.env` file is gitignored
- [ ] Strong database passwords in use
- [ ] API keys are environment-specific
- [ ] Database user has minimal required permissions
- [ ] SSL/TLS enabled for database connections
- [ ] Regular security audits of dependencies
- [ ] Monitoring for unauthorized access

### Environment Examples

#### Development
```bash
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/gergy_dev
ANTHROPIC_API_KEY=your_dev_api_key
```

#### Production
```bash
DATABASE_URL=postgresql://prod_user:complex_secure_password@db.example.com:5432/gergy_production?sslmode=require
ANTHROPIC_API_KEY=your_production_api_key
```

### Troubleshooting

#### Common Issues

1. **"DATABASE_URL environment variable is required"**
   - Ensure `.env` file exists and contains `DATABASE_URL`
   - Check that the application can read the `.env` file

2. **Database connection refused**
   - Verify database server is running
   - Check host/port in DATABASE_URL
   - Ensure firewall allows connections

3. **Authentication failed**
   - Verify username/password in DATABASE_URL
   - Check database user permissions
   - Ensure user exists and can connect

#### Security Incident Response

If credentials are compromised:
1. **Immediately rotate** all affected credentials
2. **Review logs** for unauthorized access
3. **Update** all affected applications
4. **Monitor** for suspicious activity
5. **Document** the incident and response

### Regular Maintenance

- **Monthly:** Review and rotate API keys
- **Quarterly:** Update database passwords
- **Annually:** Security audit of entire system
- **As needed:** Update dependencies for security patches