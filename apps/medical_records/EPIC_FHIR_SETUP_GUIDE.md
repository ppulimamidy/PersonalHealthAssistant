# Epic FHIR Integration Setup Guide

## Overview
This guide helps you set up Epic FHIR integration for the Personal Health Assistant.

## Prerequisites
1. Epic FHIR Developer Account
2. Epic FHIR App Registration
3. Valid Epic FHIR Client Credentials

## Step 1: Epic FHIR App Registration
1. Go to [Epic FHIR Developer Portal](https://fhir.epic.com/)
2. Create a new app registration
3. Note down your Client ID and Client Secret
4. Configure redirect URIs

## Step 2: Environment Variables
Set the following environment variables:

```bash
export EPIC_FHIR_CLIENT_ID="your_actual_client_id"
export EPIC_FHIR_CLIENT_SECRET="your_actual_client_secret"
export EPIC_FHIR_ENVIRONMENT="sandbox"  # or "production"
export EPIC_FHIR_REDIRECT_URI="http://localhost:8080/callback"
```

Or add them to your `.env` file:

```env
EPIC_FHIR_CLIENT_ID=your_actual_client_id
EPIC_FHIR_CLIENT_SECRET=your_actual_client_secret
EPIC_FHIR_ENVIRONMENT=sandbox
EPIC_FHIR_REDIRECT_URI=http://localhost:8080/callback
```

## Step 3: Database Setup
Run the database migration script:

```bash
python apps/medical_records/create_epic_fhir_tables.py
```

## Step 4: Test Integration
Run the integration test:

```bash
python apps/medical_records/test_epic_fhir_integration.py
```

## Step 5: Start Medical Records Service
```bash
cd apps/medical_records
python main.py
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   - Ensure all Epic FHIR environment variables are set
   - Check that credentials are valid

2. **Authentication Errors**
   - Verify client credentials are correct
   - Check if credentials have expired
   - Ensure proper scopes are configured

3. **Database Connection Issues**
   - Run database migrations
   - Check database connection settings
   - Verify database permissions

4. **Network Connectivity**
   - Check firewall settings
   - Verify Epic FHIR service availability
   - Test network connectivity to Epic servers

### Getting Help
- Epic FHIR Documentation: https://fhir.epic.com/
- Epic FHIR Support: https://fhir.epic.com/Support
- Epic FHIR Community: https://community.epic.com/

## Security Notes
- Never commit real credentials to version control
- Use environment variables for sensitive data
- Regularly rotate client secrets
- Follow Epic FHIR security best practices
