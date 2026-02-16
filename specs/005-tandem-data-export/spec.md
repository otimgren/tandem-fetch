# Feature Specification: Tandem Data Export Command

**Feature Branch**: `005-tandem-data-export`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "I'd like to set up a command that downloads all the latest data from Tandem and dumps it into a CSV or parquet file (user should be able to specify). Please write the specification for that."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export CGM Readings to Parquet (Priority: P1)

A user wants to export their continuous glucose monitoring (CGM) data for analysis in a Python data science environment. They run a single command that fetches the latest data from Tandem Source and exports it to a parquet file, which they then load into pandas for time-in-range calculations and visualization.

**Why this priority**: CGM readings are the most frequently accessed data type for diabetes analytics. Parquet format is columnar and highly efficient for time-series data analysis, making it the preferred choice for data scientists and analysts.

**Independent Test**: Can be fully tested by running the export command with parquet format and verifying that a valid parquet file is created containing CGM readings with timestamp and glucose value columns. Delivers immediate value by enabling data analysis without requiring additional features.

**Acceptance Scenarios**:

1. **Given** the user has valid Tandem credentials configured, **When** they run the export command with format option "parquet" and table "cgm_readings", **Then** a parquet file is created containing all CGM readings with timestamp and glucose values
2. **Given** the user has existing CGM data in the local database, **When** they run the export command, **Then** the export includes only the latest data fetched from Tandem Source
3. **Given** the user specifies an output file path, **When** the export completes successfully, **Then** the file is created at the specified location with the correct format extension
4. **Given** the export command is running, **When** data is being fetched and exported, **Then** progress information is displayed showing fetch and export status

---

### User Story 2 - Export Multiple Data Tables in One Command (Priority: P2)

A user wants to export their complete diabetes data set including CGM readings, basal deliveries, and all parsed events for comprehensive analysis. They run a single command that exports all three tables to separate files, allowing them to analyze relationships between glucose levels, insulin delivery, and pump events.

**Why this priority**: Enables comprehensive analysis by exporting multiple related datasets simultaneously. This is a common use case for users doing in-depth analysis but not as critical as the basic single-table export functionality.

**Independent Test**: Can be fully tested by running the export command with multiple table names specified and verifying that all requested tables are exported to separate files. Delivers value independently by enabling multi-table exports without requiring other features.

**Acceptance Scenarios**:

1. **Given** the user specifies multiple tables to export, **When** they run the export command, **Then** each table is exported to a separate file with the table name included in the filename
2. **Given** the user wants to export all available tables, **When** they use an "all" option, **Then** all tables (cgm_readings, basal_deliveries, events, raw_events) are exported
3. **Given** one table export fails, **When** the command continues processing remaining tables, **Then** successful exports are completed and failures are reported at the end

---

### User Story 3 - Export to CSV Format (Priority: P3)

A user wants to export their CGM data to CSV format for viewing in Excel or importing into a non-Python analysis tool. They run the export command with CSV format option and open the resulting file in their spreadsheet application.

**Why this priority**: CSV is a universal format useful for Excel users and non-technical analysts. However, parquet is more efficient for programmatic analysis, making CSV a secondary priority. This can be added after core parquet export is working.

**Independent Test**: Can be fully tested by running the export command with CSV format and verifying that a valid CSV file is created with proper headers and comma-delimited values. Delivers value independently for users who need spreadsheet-compatible exports.

**Acceptance Scenarios**:

1. **Given** the user specifies CSV as the output format, **When** they run the export command, **Then** a CSV file is created with headers and comma-delimited data
2. **Given** the exported CSV file, **When** opened in Excel or another spreadsheet application, **Then** all columns are properly separated and dates are readable
3. **Given** text fields contain commas or quotes, **When** exported to CSV, **Then** values are properly escaped according to CSV standards

---

### User Story 4 - Incremental Export with Date Range Filtering (Priority: P4)

A user wants to export only recent data for weekly analysis rather than their entire historical dataset. They run the export command with date range filters to export only the last 7 days of CGM readings, reducing file size and processing time.

**Why this priority**: Useful for regular periodic exports and reducing file sizes, but most users can achieve this by filtering after export or querying the database directly. Lower priority than core export functionality.

**Independent Test**: Can be fully tested by running the export command with start/end date parameters and verifying that the output only contains records within the specified date range. Delivers value independently for users who want filtered exports.

**Acceptance Scenarios**:

1. **Given** the user specifies a start date, **When** they run the export command, **Then** only records with timestamps on or after the start date are included
2. **Given** the user specifies both start and end dates, **When** they run the export command, **Then** only records within the date range (inclusive) are included
3. **Given** the user specifies only an end date, **When** they run the export command, **Then** all records up to and including the end date are included

---

### Edge Cases

- What happens when no data exists in the requested table (e.g., fresh install)?
- How does the system handle export failures (disk full, permission denied, invalid path)?
- What happens when the user specifies an invalid table name?
- How does the system handle invalid date ranges (end date before start date)?
- What happens if the Tandem API is unavailable during the fetch operation?
- How does the system handle very large exports (millions of records)?
- What happens if the output file already exists?
- How does the system handle special characters or spaces in the output file path?
- What happens when the user cancels the export operation mid-process (Ctrl+C)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch the latest data from Tandem Source API before exporting
- **FR-002**: System MUST support exporting data to parquet format
- **FR-003**: System MUST support exporting data to CSV format
- **FR-004**: Users MUST be able to specify the output file path for the export
- **FR-005**: Users MUST be able to specify which table(s) to export (cgm_readings, basal_deliveries, events, raw_events)
- **FR-006**: System MUST validate that the specified table exists before attempting export
- **FR-007**: System MUST create parent directories for the output file path if they don't exist
- **FR-008**: System MUST provide clear progress indicators during fetch and export operations
- **FR-009**: System MUST handle export errors gracefully and provide actionable error messages
- **FR-010**: System MUST use the existing credentials configuration (sensitive/credentials.toml)
- **FR-011**: System MUST log export operations including table name, format, record count, and duration
- **FR-012**: Users MUST be able to export multiple tables in a single command invocation
- **FR-013**: System MUST support date range filtering with start date and/or end date parameters
- **FR-014**: System MUST validate date range parameters and reject invalid ranges
- **FR-015**: System MUST handle existing output files by either overwriting or prompting based on user preference
- **FR-016**: System MUST complete the full pipeline (fetch, parse, extract) before exporting to ensure data freshness
- **FR-017**: System MUST preserve data types and precision when exporting (timestamps, integers, JSON fields)

### Key Entities

- **Export Configuration**: Represents the parameters for an export operation including table name(s), output format, file path, and optional date filters
- **Data Table**: Represents one of the four available tables (cgm_readings, basal_deliveries, events, raw_events) with its schema and data
- **Export Result**: Represents the outcome of an export operation including success/failure status, record count, file path, and any errors encountered

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can export CGM readings to parquet format with a single command invocation in under 30 seconds for typical datasets (up to 100,000 records)
- **SC-002**: Export operations complete successfully 99% of the time when valid parameters are provided and network is available
- **SC-003**: Users can open exported CSV files in Excel without encountering formatting issues or data corruption
- **SC-004**: Users can load exported parquet files in pandas/polars without schema or encoding errors
- **SC-005**: Export command provides clear error messages that enable users to resolve issues without consulting documentation in 90% of error cases
- **SC-006**: Users can export their complete dataset (all tables) with a single command flag rather than running four separate commands
- **SC-007**: Date range filtering reduces export file sizes by the expected proportion (e.g., 7 days of data from 1 year dataset results in approximately 2% of full dataset size)

## Assumptions

- Users have already configured their Tandem credentials in sensitive/credentials.toml
- Users have successfully run the pipeline at least once to populate the local database
- Output file paths are on local filesystem with sufficient disk space
- Users have write permissions to the specified output directory
- Default output directory will be "exports/" in the project root
- Default file naming convention will be "{table_name}_{timestamp}.{format}" when no path is specified
- The existing pipeline commands (run-pipeline, get-all-raw-pump-events, etc.) will be used for fetching latest data
- Parquet format will be the default format if none is specified (due to efficiency for time-series data)
- Exports will include all columns from the table (no column selection in initial version)
