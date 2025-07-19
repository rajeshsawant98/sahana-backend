# Standalone Test Files

This directory contains standalone test files that were moved from the project root for better organization.

## Files

- `test_api_endpoints.py` - Tests for API endpoint validation and pagination
- `test_main_endpoint.py` - Tests for main events endpoint
- `test_cursor_pagination.py` - Tests for cursor pagination functionality  
- `debug_cursor_pagination.py` - Debug script for cursor pagination issues

## Usage

These files can be run directly:

```bash
cd /path/to/sahana-backend
python app/test/standalone/test_api_endpoints.py
python app/test/standalone/test_main_endpoint.py
```

## Note

For formal testing, use the main test suite in the parent `test/` directory with pytest:

```bash
python -m pytest app/test/
```
