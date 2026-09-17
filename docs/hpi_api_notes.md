# Healthy Places Index (HPI) API Notes

## Registration Process
**Account creation is required** to obtain an API key for the HPI system.

### Steps to Register:
1. Navigate to https://map.healthyplacesindex.org/
2. Click the "Sign In" button in the top-right navigation bar
3. The system uses **Google SSO (Single Sign-On)** for authentication
4. After signing in with a Google account, the API key will be available in your account settings

### Registration Blocker Encountered:
- The HPI system requires Google account authentication
- Email verification/password is needed to complete account creation
- **Manual user action required**: The owner (benjaminknkirk@gmail.com) must:
  - Sign in to Google with their password
  - Complete any MFA/2FA if enabled
  - Navigate to account settings on the map portal to retrieve the API key

## API Information

### Base URLs:
- API Documentation: https://api.healthyplacesindex.org/documentation
- API Base: https://api.healthyplacesindex.org/
- Map Portal: https://map.healthyplacesindex.org/

### Key Notes:
- **2010 Census Geographies**: As of February 6, 2026, the API supports data using **2010 census tract geographies**
- **2020 Census Geographies**: For HPI 3.0 data with 2020 geographies, a separate "Complete HPI Data File request form" must be filled out at https://www.healthyplacesindex.org/request-hpi-data-file
-For research purposes focused on 2010 tracts, the API is the appropriate tool

### Available Geography Types:
The API supports multiple geographic levels including:
- `tracts` (census tracts - 2010 boundaries)
- `counties`
- `places`
- `zips`
- `cbsa` (Core-Based Statistical Areas)
- `congressional_district`
- `state_assembly_districts`
- `state_senate_districts`
- And others

### API Endpoint Pattern (Preliminary - requires API key to test):
Based on documentation review, the API likely follows this pattern:
```
https://api.healthyplacesindex.org/api/v1/data?
  geography_type=tracts
  &variable=hpi_score
  &api_key=YOUR_API_KEY
```

**Note**: The exact endpoint URL pattern cannot be fully confirmed without:
1. Completing account creation
2. Obtaining an actual API key
3. Testing authenticated requests

### Variables Available:
The API provides access to numerous health and social determinant indicators including:
- `hpi_score` - Overall HPI score (percentile ranking)
- Multiple domain-specific indicators (economic, education, healthcare, etc.)
- Each variable has associated metadata (technical definitions, years, sources, units)

### Data Format:
- Response format: JSON (likely, based on modern API patterns)
- CSV export may be available through the map interface "Download" feature

## Next Steps for User:
1. Complete Google authentication at https://map.healthyplacesindex.org/
2. Locate API key in account settings/profile
3. Test API endpoint with authentication
4. Update this file with confirmed endpoint patterns

## Research Context:
Project: LA28 Equity Watch - Academic research mapping Olympic investment access vs disadvantage in Los Angeles County (Fulbright-related prototype)
Owner: Benjamin Kirk (benjaminknkirk@gmail.com)
Purpose: Non-commercial academic research
