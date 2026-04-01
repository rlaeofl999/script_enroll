# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the main script
uv run test_script.py
```

No linting, testing, or build pipeline is configured.

## Architecture

This is a single-script clinical data automation tool (`test_script.py`) that batch-processes patient data through a medical prediction web app.

**Flow:**
1. Load patient records from an Excel file (`C:\TEST.xlsx`) using pandas
2. For each row, use Selenium to open the Shiny web app (`https://bostonmontpelliercare.shinyapps.io/AIClarity/`), fill in 15 clinical parameters (biochemistry, hematology, vitals, respiratory, vasopressors), and submit
3. Scrape the returned probability value using a regex (`\d+\.?\d*\s?%`)
4. Collect results and write them to a new Excel file; a backup is saved every 10 iterations

**Key dependencies:**
- `selenium` + `webdriver-manager` — Chrome automation, driver managed automatically
- `pandas` + `openpyxl` — read/write Excel files

**Environment:** Designed for Windows (hardcoded input path `C:\TEST.xlsx`, CRLF line-ending notes in README). Python 3.12 required; use `uv` (not pip) for package management.
