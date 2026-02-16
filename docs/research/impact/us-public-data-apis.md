# US Public Data APIs for Social Program Evaluation and Impact Assessment

Comprehensive reference guide for major US federal data APIs useful for evaluating social programs and assessing policy impact.

**Last Updated:** 2026-02-13
**Research Date:** February 2026

---

## 1. Census Bureau API

**Purpose:** American Community Survey (ACS), Decennial Census, Population Estimates, Economic Indicators, International Trade

**Base URL:** `https://api.census.gov/data/`

**Authentication:**
- Optional for basic use (up to 500 queries/day per IP address)
- API key required for >500 queries/day
- Register at: https://www.census.gov/developers/
- Include key as query parameter: `?key=YOUR_API_KEY`

**Key Endpoints:**
- ACS 1-Year: `https://api.census.gov/data/{year}/acs/acs1`
- ACS 5-Year: `https://api.census.gov/data/{year}/acs/acs5`
- Decennial Census: `https://api.census.gov/data/{year}/dec/`
- Population Estimates: `https://api.census.gov/data/{year}/pep/`
- Economic Indicators: `https://api.census.gov/data/timeseries/eits/`

**Data Format:**
- JSON (2D array format)
- First row: column names
- Subsequent rows: data values

**Example Query:**
```
https://api.census.gov/data/2019/acs/acs1?get=NAME,B02015_009E,B02015_009M&for=state:*&key=YOUR_KEY
```

**Example Response:**
```json
[
  ["STNAME","POP","DATE_","state"],
  ["Alabama","4849377","7","01"],
  ["Alaska","736732","7","02"],
  ["Arizona","6731484","7","04"]
]
```

**Rate Limits:**
- Without key: 500 queries/day per IP address
- With key: Higher limits (contact Census for details)
- Max 50 variables per query
- Cell return limits vary by dataset

**Use Cases:**
- Demographic analysis for program targeting
- Poverty rates, income distribution, educational attainment
- Housing characteristics, employment statistics
- Geographic comparisons (state, county, tract, block group)

**Documentation:** https://www.census.gov/data/developers/guidance/api-user-guide.html

---

## 2. data.gov CKAN API

**Purpose:** Metadata search across 300,000+ federal datasets; discovery and access portal

**Base URL:** `https://api.gsa.gov/technology/datagov/v3/action/`

**Authentication:**
- API key required (header-based)
- Register at: https://api.data.gov/signup/
- Include in header: `x-api-key: YOUR_API_KEY`

**Key Endpoints:**
- Package search: `package_search`
- Package show: `package_show`
- Resource search: `resource_search`
- Organization list: `organization_list`
- Tag list: `tag_list`

**Data Format:**
- JSON (CKAN standard format)
- Metadata only (not actual dataset contents)

**Example Query:**
```
https://api.gsa.gov/technology/datagov/v3/action/package_search?q=education&api_key=DEMO_KEY
```

**Example Response:**
```json
{
  "success": true,
  "result": {
    "count": 1234,
    "results": [
      {
        "id": "dataset-id",
        "name": "dataset-name",
        "title": "Dataset Title",
        "organization": {...},
        "resources": [...]
      }
    ]
  }
}
```

**Rate Limits:**
- Not publicly documented
- CKAN API typically has generous limits for public use

**Use Cases:**
- Dataset discovery across all federal agencies
- Metadata analysis for data inventory
- Cross-agency data integration planning
- Finding datasets by topic, agency, or keyword

**Documentation:** https://open.gsa.gov/api/datadotgov/

---

## 3. Bureau of Labor Statistics (BLS) API

**Purpose:** Employment data, unemployment rates, wages, inflation (CPI), productivity, workplace injuries

**Base URL (v2):** `https://api.bls.gov/publicAPI/v2/timeseries/data/`

**Authentication:**
- v1.0: No key required (limited features)
- v2.0: API key required for advanced features
- Register at: https://www.bls.gov/developers/home.htm
- Include as query parameter: `?registrationkey=YOUR_KEY`

**Key Endpoints:**
- Timeseries data: `/timeseries/data/`
- Surveys list: `/surveys/`
- Popular series: `/popular/`

**Data Format:**
- JSON
- Series-based with observations array

**Example Query (POST):**
```json
POST https://api.bls.gov/publicAPI/v2/timeseries/data/
{
  "seriesid": ["LNS14000000"],
  "startyear": "2020",
  "endyear": "2024",
  "registrationkey": "YOUR_KEY"
}
```

**Example Response:**
```json
{
  "status": "REQUEST_SUCCEEDED",
  "responseTime": 123,
  "Results": {
    "series": [
      {
        "seriesID": "LNS14000000",
        "data": [
          {
            "year": "2024",
            "period": "M01",
            "value": "3.7"
          }
        ]
      }
    ]
  }
}
```

**Rate Limits:**
- v1.0: 25 queries/day, 10 years/query, 25 series/query
- v2.0: 500 queries/day, 20 years/query, 50 series/query

**Use Cases:**
- Labor market analysis for workforce programs
- Unemployment trends by demographics
- Wage data for income support evaluation
- CPI for inflation adjustment in longitudinal studies

**Documentation:** https://www.bls.gov/developers/home.htm

---

## 4. CDC WONDER API

**Purpose:** Public health data including mortality, natality, cancer incidence, environmental health, vaccine data

**Base URL:** `https://wonder.cdc.gov/`

**Authentication:**
- No API key required
- XML-based query system

**Key Endpoints:**
- Detailed Mortality: Database D76, D77, D149, etc.
- Natality: Database D66, D149
- Cancer Incidence: SEER database
- Environmental Health: EHDI, Air Quality

**Data Format:**
- XML request/response
- Automated queries over HTTP

**Example Query:**
XML-formatted POST request to specific database endpoint (complex, see documentation)

**Rate Limits:**
- Not publicly documented
- Reasonable use policy applies

**Use Cases:**
- Mortality analysis for public health programs
- Birth outcome evaluation
- Disease surveillance and trends
- Environmental exposure assessment

**HealthData.gov Integration:**
CDC datasets also available through HealthData.gov portal for broader discovery

**Documentation:** https://wonder.cdc.gov/wonder/help/wonder-api.html

**Additional HHS APIs:**
- CMS Data Repository: Medicare/Medicaid data
- HealthData.gov: Portal for health datasets across HHS agencies

---

## 5. Department of Education - College Scorecard API

**Purpose:** Higher education data including costs, student outcomes, earnings, demographics, financial aid

**Base URL:** `https://api.data.gov/ed/collegescorecard/v1/schools`

**Authentication:**
- API key required
- Register at: https://api.data.gov/signup/
- Include as query parameter: `?api_key=YOUR_KEY`

**Key Endpoints:**
- Schools: `/schools` (main endpoint)
- Supports filtering, field selection, pagination

**Data Format:**
- JSON
- Paginated results (100 records per page max)

**Example Query:**
```
https://api.data.gov/ed/collegescorecard/v1/schools?api_key=YOUR_KEY&school.state=CA&fields=id,school.name,latest.student.size,latest.cost.avg_net_price.overall&per_page=100
```

**Example Response:**
```json
{
  "metadata": {
    "page": 0,
    "total": 453,
    "per_page": 100
  },
  "results": [
    {
      "id": 110635,
      "school.name": "University of California-Berkeley",
      "latest.student.size": 45057,
      "latest.cost.avg_net_price.overall": 18136
    }
  ]
}
```

**Rate Limits:**
- Standard api.data.gov limits apply
- Typically 1,000 requests/hour per API key

**Use Cases:**
- Higher education program evaluation
- College access and completion analysis
- Student debt and earnings outcomes
- Institution comparison for policy research

**Additional NCES Resources:**
- NCES Data Tools: https://nces.ed.gov/datatools/
- EdFacts API, IPEDS API (separate systems)

**Documentation:** https://collegescorecard.ed.gov/data/api-documentation/

---

## 6. USAspending.gov API

**Purpose:** Federal spending data including contracts, grants, loans, financial assistance

**Base URL:** `https://api.usaspending.gov/api/v2/`

**Authentication:**
- No API key required for public endpoints
- Open access REST JSON API

**Key Endpoints:**
- Award search: `/search/spending_by_award/`
- Recipient search: `/recipient/`
- Agency spending: `/agency/`
- Federal accounts: `/federal_account/`
- CFDA programs: `/references/cfda/`
- Bulk download: `/bulk_download/`

**Data Format:**
- JSON
- POST requests for complex queries

**Example Query (POST):**
```json
POST https://api.usaspending.gov/api/v2/search/spending_by_award/
{
  "filters": {
    "award_type_codes": ["02", "03", "04", "05"],
    "agencies": [{"type": "funding", "tier": "toptier", "name": "Department of Education"}]
  },
  "fields": ["Award ID", "Recipient Name", "Award Amount"],
  "limit": 100
}
```

**Example Response:**
```json
{
  "limit": 100,
  "results": [
    {
      "Award ID": "EDGR123456",
      "Recipient Name": "State Board of Education",
      "Award Amount": 5000000
    }
  ],
  "page_metadata": {
    "page": 1,
    "total": 12345,
    "hasNext": true
  }
}
```

**Rate Limits:**
- Not publicly documented
- Reasonable use policy applies
- Bulk downloads available for large requests

**Use Cases:**
- Grant and contract analysis
- Federal program funding flows
- Recipient analysis (geographic, demographic)
- Program evaluation for federally funded initiatives

**Documentation:** https://api.usaspending.gov/docs/endpoints/

---

## 7. FRED (Federal Reserve Economic Data) API

**Purpose:** 800,000+ economic time series including GDP, inflation, employment, interest rates, financial markets

**Base URL:** `https://api.stlouisfed.org/fred/`

**Authentication:**
- API key required
- Register at: https://fred.stlouisfed.org/docs/api/api_key.html
- Include as query parameter: `?api_key=YOUR_KEY`

**Key Endpoints:**
- Series observations: `/series/observations`
- Series search: `/series/search`
- Categories: `/category`
- Releases: `/releases`
- Sources: `/sources`

**Data Format:**
- JSON or XML
- Specify via `file_type` parameter

**Example Query:**
```
https://api.stlouisfed.org/fred/series/observations?series_id=GNPCA&api_key=YOUR_KEY&file_type=json
```

**Example Response:**
```json
{
  "realtime_start": "2026-02-13",
  "realtime_end": "2026-02-13",
  "observation_start": "1776-07-04",
  "observation_end": "9999-12-31",
  "units": "lin",
  "output_type": 1,
  "file_type": "json",
  "order_by": "observation_date",
  "sort_order": "asc",
  "count": 95,
  "offset": 0,
  "limit": 100000,
  "observations": [
    {
      "realtime_start": "2026-02-13",
      "realtime_end": "2026-02-13",
      "date": "1929-01-01",
      "value": "1065.9"
    }
  ]
}
```

**Rate Limits:**
- 120 requests per minute
- ~172,800 requests per day (theoretical maximum)
- Max 100,000 observations per request (use offset for more)

**Use Cases:**
- Macroeconomic context for program evaluation
- Inflation adjustment for cost-benefit analysis
- Labor market indicators
- Regional economic data for geographic analysis

**Documentation:** https://fred.stlouisfed.org/docs/api/fred/

---

## 8. Performance.gov / Results.gov

**Purpose:** Federal agency performance data, strategic goals, agency priority goals, program performance

**Status:** **No public API currently available**

**Alternative Access:**
- Performance Data Report (downloadable file)
- Agency performance plans and reports (PDF/Excel)
- Previously had API (now archived)

**Base URL (archived):** `https://trumpadministration.archives.performance.gov/data/`

**Data Format:**
- CSV/Excel downloads
- Agency-specific reports

**Use Cases:**
- Government performance management research
- Cross-agency strategic goal tracking
- GPRA Modernization Act compliance analysis
- Outcome-based program evaluation

**Notes:**
- Performance.gov transitioned from API-based system to report-based system
- Data available through consolidated Performance Data Report
- Individual agency performance plans available on agency websites
- Statutory requirements under GPRA Modernization Act of 2010

**Documentation:** https://www.performance.gov/about/

---

## 9. HUD (Housing and Urban Development) APIs

**Purpose:** Fair Market Rent, Income Limits, USPS Address Crosswalk, Comprehensive Housing Affordability Strategy (CHAS)

**Base URL:** `https://www.huduser.gov/hudapi/public/`

**Authentication:**
- Token-based authentication
- Register at: https://www.huduser.gov/hudapi/public/login
- Create token with dataset access
- Include in header: `Authorization: Bearer YOUR_TOKEN`

**Key Endpoints:**
- Fair Market Rent (FMR): `/fmr/`
- Income Limits: `/il/`
- USPS Crosswalk: `/usps/`
- CHAS: `/chas/`

**Data Format:**
- JSON

**Example Query:**
```
GET https://www.huduser.gov/hudapi/public/fmr/statedata/CA?year=2024
Authorization: Bearer YOUR_TOKEN
```

**Rate Limits:**
- 1,200 queries per minute

**Additional HUD Resources:**
- HUD Open Data (ArcGIS): https://hudgis-hud.opendata.arcgis.com/
- Geospatial datasets, mapping tools
- No API key required for basic access

**Use Cases:**
- Housing affordability analysis
- Fair market rent for subsidy programs
- Geographic data for housing programs
- Income limit calculations for eligibility

**Documentation:** https://www.huduser.gov/portal/dataset/fmr-api.html

---

## 10. USDA (United States Department of Agriculture) APIs

**Purpose:** Agricultural data, food and nutrition, rural development, economic research

**Multiple API Services Available:**

### 10.1 FoodData Central API

**Base URL:** `https://api.nal.usda.gov/fdc/v1/`

**Authentication:**
- API key required
- Register at: https://fdc.nal.usda.gov/api-key-signup.html
- Include as query parameter: `?api_key=YOUR_KEY`

**Key Endpoints:**
- Food search: `/foods/search`
- Food details: `/food/{fdcId}`
- Food list: `/foods/list`

**Example Query:**
```
https://api.nal.usda.gov/fdc/v1/foods/search?query=apple&api_key=YOUR_KEY
```

**Use Cases:**
- Nutrition program evaluation
- Food assistance program analysis
- Dietary assessment research

### 10.2 Economic Research Service (ERS) APIs

**Base URL:** `https://api.ers.usda.gov/`

**Authentication:**
- API key required
- Register through ERS developer portal

**Available APIs:**
- ARMS Data API (Agricultural Resource Management Survey)
- Quick Stats API (agricultural statistics)
- Food Access Research Atlas
- Food Environment Atlas

**Example Query:**
```
https://quickstats.nass.usda.gov/api/api_GET/?key=YOUR_KEY&commodity_desc=CORN&year=2023
```

**Use Cases:**
- Rural development program evaluation
- Agricultural economics research
- Food security and access analysis
- Farm program effectiveness

### 10.3 Agricultural Marketing Service APIs

**Base URL:** Various endpoints for different datasets

**Available APIs:**
- Livestock Mandatory Price Reporting
- Market News (fruits, vegetables, dairy, livestock)
- Farmers Market Directory API

**Authentication:**
- Varies by API (some require keys, some open)

**Use Cases:**
- Agricultural market analysis
- Price trend evaluation
- Farmers market program assessment

**Documentation:** https://www.ers.usda.gov/developer/

---

## 11. EPA (Environmental Protection Agency) APIs

**Purpose:** Environmental data including air quality, water quality, toxic releases, facility compliance

**Multiple API Services Available:**

### 11.1 Envirofacts Data Service API

**Base URL:** `https://data.epa.gov/efservice/`

**Authentication:**
- API key required (via api.data.gov)
- Register at: https://api.data.gov/signup/
- Include in header: `X-Api-Key: YOUR_KEY`

**Key Endpoints:**
- Facility search (by location, program)
- Air emissions data
- Water discharge data
- Hazardous waste data
- Toxics Release Inventory (TRI)

**Data Format:**
- JSON, XML, CSV

**Example Query:**
```
https://data.epa.gov/efservice/tri_facility/state_abbr/CA/rows/0:100/JSON
```

**Use Cases:**
- Environmental justice analysis
- Facility compliance monitoring
- Pollution exposure assessment
- Environmental program evaluation

### 11.2 Air Quality System (AQS) API

**Base URL:** `https://aqs.epa.gov/data/api/`

**Authentication:**
- Email and API key required
- Register through AQS system
- Include as query parameters: `?email=YOUR_EMAIL&key=YOUR_KEY`

**Key Endpoints:**
- Daily summary data: `/dailyData/byState`
- Annual summary: `/annualData/byState`
- Monitors: `/monitors/byState`

**Example Query:**
```
https://aqs.epa.gov/data/api/dailyData/byState?email=YOUR_EMAIL&key=YOUR_KEY&param=44201&bdate=20230101&edate=20231231&state=06
```

**Use Cases:**
- Air quality trend analysis
- Health impact assessment
- Environmental program effectiveness
- Pollution reduction program evaluation

**Rate Limits:**
- Not publicly documented for Envirofacts
- AQS API: reasonable use policy

**Documentation:** https://www.epa.gov/enviro/envirofacts-data-service-api

---

## Summary Comparison Table

| API | Auth Required | Rate Limit (per day) | Data Format | Primary Use Cases |
|-----|---------------|---------------------|-------------|-------------------|
| Census Bureau | Optional (key for >500/day) | 500 without key | JSON (2D array) | Demographics, poverty, housing, employment |
| data.gov CKAN | Yes (header) | Not specified | JSON | Dataset discovery across federal agencies |
| BLS | Optional (v2 needs key) | 500 (v2 with key) | JSON | Labor market, unemployment, wages, CPI |
| CDC WONDER | No | Not specified | XML | Mortality, natality, disease surveillance |
| College Scorecard | Yes | ~1,000/hour | JSON | Higher education costs, outcomes, earnings |
| USAspending.gov | No | Not specified | JSON | Federal spending, grants, contracts |
| FRED | Yes | 172,800 (120/min) | JSON/XML | Economic indicators, financial data |
| Performance.gov | N/A - No API | N/A | CSV/Excel | Federal agency performance (no API) |
| HUD | Yes (token) | 1,200/minute | JSON | Housing affordability, income limits, FMR |
| USDA (FoodData) | Yes | Not specified | JSON | Nutrition data, agricultural statistics |
| EPA (Envirofacts) | Yes | Not specified | JSON/XML/CSV | Environmental quality, facility compliance |

---

## Best Practices for API Usage

1. **API Key Management**
   - Store keys in environment variables, never in code
   - Use separate keys for development and production
   - Rotate keys periodically
   - Monitor usage to stay within rate limits

2. **Rate Limit Handling**
   - Implement exponential backoff for retries
   - Cache responses when appropriate
   - Use bulk download endpoints for large requests
   - Monitor rate limit headers in responses

3. **Data Quality**
   - Validate API responses before use
   - Check for missing values and data quality flags
   - Understand data vintages and revision policies
   - Document data sources and retrieval dates

4. **Error Handling**
   - Implement robust error handling for network issues
   - Log API errors for debugging
   - Handle rate limit errors gracefully
   - Validate input parameters before requests

5. **Documentation**
   - Always reference official API documentation
   - Check for API versioning and deprecation notices
   - Subscribe to API update notifications
   - Test queries in sandbox/demo mode first

---

## Additional Resources

### Cross-Cutting Portals
- **api.data.gov**: Unified API key system for many federal APIs
- **catalog.data.gov**: CKAN-based metadata catalog (300,000+ datasets)
- **HealthData.gov**: Health-focused data portal with API access
- **FederalRegister.gov**: Regulatory data with REST API

### Developer Resources
- GSA's API Standards: https://github.com/GSA/api-standards
- Federal API Directory: https://api.data.gov/docs/
- Data.gov Developer Resources: https://data.gov/developers/

### Program Evaluation Resources
- OMB Evidence and Evaluation Resources: https://www.whitehouse.gov/omb/
- Foundations for Evidence-Based Policymaking Act
- Federal Evaluation Clearinghouse

---

## Sources

**Census Bureau:**
- [Census Bureau Available APIs](https://www.census.gov/data/developers/data-sets.html)
- [Census Data API User Guide](https://www.census.gov/data/developers/guidance/api-user-guide.html)
- [American Community Survey Data via API](https://www.census.gov/programs-surveys/acs/data/data-via-api.html)

**data.gov:**
- [Data.gov API Documentation](https://open.gsa.gov/api/datadotgov/)
- [Data.gov CKAN API Dataset](https://catalog.data.gov/dataset/data-gov-ckan-api)
- [CKAN API Guide](https://docs.ckan.org/en/latest/api/)

**Bureau of Labor Statistics:**
- [BLS Data API](https://www.bls.gov/bls/api_features.htm)
- [BLS API Getting Started](https://www.bls.gov/developers/home.htm)
- [BLS API FAQs](https://www.bls.gov/developers/api_faqs.htm)
- [BLS Public Data API Signatures v2](https://www.bls.gov/developers/api_signature_v2.htm)

**CDC/HHS:**
- [CDC Open Technology APIs](https://open.cdc.gov/apis.html)
- [CDC WONDER API Documentation](https://wonder.cdc.gov/wonder/help/wonder-api.html)
- [CDC WONDER API on HealthData.gov](https://healthdata.gov/dataset/CDC-WONDER-API-for-Data-Query-Web-Service/t3mh-uddy)
- [HHS Developers' Center](https://www.hhs.gov/web/developer/index.html)

**Department of Education:**
- [College Scorecard API](https://collegescorecard.ed.gov/data/api/)
- [College Scorecard API Documentation](https://collegescorecard.ed.gov/data/api-documentation/)

**USAspending.gov:**
- [USAspending API](https://api.usaspending.gov/)
- [USAspending API Documentation](https://api.usaspending.gov/docs/endpoints/)
- [USAspending GitHub Repository](https://github.com/fedspendingtransparency/usaspending-api)

**FRED:**
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [FRED API Overview](https://fred.stlouisfed.org/docs/api/fred/overview.html)
- [FRED API Key Registration](https://fred.stlouisfed.org/docs/api/api_key.html)

**Performance.gov:**
- [Performance.gov](https://www.performance.gov/)
- [Performance.gov About](https://www.performance.gov/about/)
- [Performance.gov Framework](https://www.performance.gov/about/performance-framework/)

**HUD:**
- [HUD Open Data Site](https://hudgis-hud.opendata.arcgis.com/)
- [HUD FMR/IL Dataset API Documentation](https://www.huduser.gov/portal/dataset/fmr-api.html)
- [HUD Data Catalog](https://data.hud.gov/datasets)

**USDA:**
- [USDA Developer Resources](https://www.usda.gov/about-usda/policies-and-links/digital/developer-resources)
- [ERS Data APIs](https://www.ers.usda.gov/developer/data-apis)
- [FoodData Central API Guide](https://fdc.nal.usda.gov/api-guide/)
- [ARMS Data API](https://www.ers.usda.gov/developer/data-apis/arms-data-api)

**EPA:**
- [EPA APIs Overview](https://www.epa.gov/data/application-programming-interface-api)
- [EPA Envirofacts Data Service API](https://www.epa.gov/enviro/envirofacts-data-service-api)
- [EPA AQS API](https://aqs.epa.gov/aqsweb/documents/data_api.html)
- [EPA Envirofacts Web Services](https://www.epa.gov/enviro/web-services)

---

**Document Version:** 1.0
**Compiled by:** Ehrlich AI Research System
**Date:** February 13, 2026
