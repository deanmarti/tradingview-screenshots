"""
FastAPI REST API for TradingView Screenshot Tool

This API exposes all TradingView Screenshot functionality via HTTP endpoints.
Authentication is done via Bearer token stored in key.md file.

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import subprocess
import glob as glob_module
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import existing functionality from tradingview_screenshot module
from tradingview_screenshot import (
    create_tradingview_chart,
    INTERVAL_CONFIG,
    INDICATOR_SHORTCUTS,
)


# =============================================================================
# API KEY LOADING
# =============================================================================

def load_api_key() -> str:
    """
    Load API key from key.md file.

    Checks multiple locations to support both local development and Docker:
    1. Project root (parent of src/) - for local development
    2. /app/key.md - for Docker container (mounted volume)

    The key.md file should contain only the API key (single line).
    This file is gitignored for security.

    Returns:
        str: The API key

    Raises:
        RuntimeError: If key.md file is not found or is empty
    """
    # Check multiple locations for key.md
    possible_paths = [
        # Project root (parent of src/) - for local development
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "key.md"),
        # Docker container path (mounted volume)
        "/app/key.md",
    ]

    for key_file in possible_paths:
        if os.path.exists(key_file):
            with open(key_file, "r") as f:
                api_key = f.read().strip()
            if api_key:
                return api_key

    raise RuntimeError(
        "key.md file not found. Create it with your API key. "
        "For Docker: mount to /app/key.md or place in /home/pi/tradingview-screenshot/"
    )


# Load API key at startup
API_KEY = load_api_key()


# =============================================================================
# FASTAPI APP SETUP
# =============================================================================

app = FastAPI(
    title="TradingView Screenshot API",
    description="REST API for generating TradingView chart screenshots",
    version="1.0.0",
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme for Bearer token authentication
security = HTTPBearer()


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ChartRequest(BaseModel):
    """Request model for chart generation."""
    ticker: str = Field(
        ...,
        description="Stock ticker symbol with exchange prefix (e.g., NASDAQ:AAPL)",
        examples=["NASDAQ:AAPL", "NYSE:IBM"]
    )
    interval: str = Field(
        default="1D",
        description="Chart interval: 15m, 1h, 4h, 1D, 1W",
        examples=["1D", "4h", "1W"]
    )
    studies: list[str] = Field(
        default=[],
        description="List of indicator names (empty for no indicators)",
        examples=[["MACD", "RSI"], ["BB", "VWAP"]]
    )


class ChartResponse(BaseModel):
    """Response model for chart generation."""
    success: bool
    filename: Optional[str] = None
    html_filename: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool = False
    error: str


class IntervalsResponse(BaseModel):
    """Response model for intervals list."""
    intervals: dict


class IndicatorsResponse(BaseModel):
    """Response model for indicators list."""
    indicators: dict


class ArchiveListResponse(BaseModel):
    """Response model for archive list."""
    archives: list[str]


class ArchiveTriggerResponse(BaseModel):
    """Response model for archive trigger."""
    success: bool
    message: str
    archive_file: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str


# =============================================================================
# AUTHENTICATION
# =============================================================================

def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify the Bearer token matches the API key.

    Args:
        credentials: The HTTP Authorization credentials

    Returns:
        str: The verified API key

    Raises:
        HTTPException: 401 if the token is invalid
    """
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_output_directory() -> str:
    """Get the default output directory (src/ folder)."""
    return os.path.dirname(os.path.abspath(__file__))


def get_archives_directory() -> str:
    """Get the archives directory path."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Check if running in Docker (archives in /home/pi/tradingview-screenshot/archives)
    if os.path.exists("/home/pi/tradingview-screenshot/archives"):
        return "/home/pi/tradingview-screenshot/archives"
    # Otherwise use project root archives folder
    return os.path.join(project_root, "archives")


def normalize_interval(interval: str) -> str:
    """
    Normalize interval to match INTERVAL_CONFIG keys (case-insensitive).

    Args:
        interval: User-provided interval string

    Returns:
        str: Normalized interval key

    Raises:
        ValueError: If interval is not valid
    """
    interval_map = {"15M": "15m", "1H": "1h", "4H": "4h", "1D": "1D", "1W": "1W"}
    interval_upper = interval.upper()

    if interval_upper in interval_map:
        return interval_map[interval_upper]

    # Check against INTERVAL_CONFIG keys
    for key in INTERVAL_CONFIG:
        if key.upper() == interval_upper:
            return key

    valid_intervals = ", ".join(INTERVAL_CONFIG.keys())
    raise ValueError(f"Invalid interval '{interval}'. Choose from: {valid_intervals}")


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint (no authentication required).

    Returns the API status and current timestamp.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@app.get("/api/intervals", response_model=IntervalsResponse, tags=["Reference"])
async def get_intervals(api_key: str = Security(verify_api_key)):
    """
    Get available chart intervals with their configurations.

    Returns all supported time intervals with their TradingView codes
    and automatic lookback periods.
    """
    return IntervalsResponse(intervals=INTERVAL_CONFIG)


@app.get("/api/indicators", response_model=IndicatorsResponse, tags=["Reference"])
async def get_indicators(api_key: str = Security(verify_api_key)):
    """
    Get available indicator shortcuts.

    Returns all supported indicator shortcut names and their
    corresponding TradingView study codes.
    """
    return IndicatorsResponse(indicators=INDICATOR_SHORTCUTS)


@app.post(
    "/api/chart/generate",
    response_model=ChartResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    tags=["Charts"]
)
async def generate_chart(
    request: ChartRequest,
    api_key: str = Security(verify_api_key)
):
    """
    Generate a TradingView chart screenshot.

    Creates a chart screenshot for the specified ticker, interval, and
    optional technical indicators. The chart is saved to the output
    directory and the filename is returned.

    **Note**: Chart generation takes approximately 8-10 seconds due to
    browser rendering time.
    """
    # Normalize ticker (uppercase)
    ticker = request.ticker.strip().upper()

    # Validate and normalize interval
    try:
        interval = normalize_interval(request.interval)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Normalize studies (uppercase)
    studies = [s.strip().upper() for s in request.studies if s.strip()]

    # Get output directory
    output_dir = get_output_directory()

    try:
        # Call the existing chart generation function
        # Note: This function prints to stdout/stderr and returns exit code
        exit_code = create_tradingview_chart(
            ticker_symbol=ticker,
            interval=interval,
            studies=studies,
            output_dir=output_dir
        )

        if exit_code != 0:
            return ChartResponse(
                success=False,
                message="Chart generation failed - invalid chart or ticker"
            )

        # Build expected filenames based on the function's naming convention
        safe_ticker = ticker.replace(':', '_')
        indicators_suffix = "_indicators" if studies else ""
        png_filename = f"tradingview_{interval}_chart_{safe_ticker}{indicators_suffix}.png"
        html_filename = f"tradingview_{interval}_chart_{safe_ticker}{indicators_suffix}.html"

        # Verify the file was actually created
        png_path = os.path.join(output_dir, png_filename)
        if not os.path.exists(png_path):
            return ChartResponse(
                success=False,
                message="Chart file was not created"
            )

        return ChartResponse(
            success=True,
            filename=png_filename,
            html_filename=html_filename,
            message="Chart generated successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chart generation error: {str(e)}"
        )


@app.get(
    "/api/chart/download/{filename}",
    responses={404: {"model": ErrorResponse}},
    tags=["Charts"]
)
async def download_chart(
    filename: str,
    api_key: str = Security(verify_api_key)
):
    """
    Download a generated chart file.

    Returns the PNG or HTML file as a binary download. Use the filename
    returned from the /api/chart/generate endpoint.
    """
    # Security: Only allow files from the output directory
    output_dir = get_output_directory()

    # Prevent directory traversal attacks
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(output_dir, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {safe_filename}"
        )

    # Determine media type based on extension
    if safe_filename.endswith(".png"):
        media_type = "image/png"
    elif safe_filename.endswith(".html"):
        media_type = "text/html"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type
    )


@app.get(
    "/api/chart/list",
    tags=["Charts"]
)
async def list_charts(
    api_key: str = Security(verify_api_key)
):
    """
    List all generated chart files in the output directory.

    Returns a list of PNG files that have been generated.
    """
    output_dir = get_output_directory()

    # Find all PNG files matching the naming pattern
    pattern = os.path.join(output_dir, "tradingview_*.png")
    files = glob_module.glob(pattern)

    # Return just the filenames, sorted by modification time (newest first)
    chart_files = sorted(
        [os.path.basename(f) for f in files],
        key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
        reverse=True
    )

    return {"charts": chart_files}


@app.get("/api/archive/list", response_model=ArchiveListResponse, tags=["Archives"])
async def list_archives(api_key: str = Security(verify_api_key)):
    """
    List all available chart archives.

    Returns a list of ZIP archive files that have been created
    by the weekly archiving process.
    """
    archives_dir = get_archives_directory()

    if not os.path.exists(archives_dir):
        return ArchiveListResponse(archives=[])

    # Find all zip files
    pattern = os.path.join(archives_dir, "*.zip")
    files = glob_module.glob(pattern)

    # Return just the filenames, sorted by name (which includes date)
    archive_files = sorted([os.path.basename(f) for f in files], reverse=True)

    return ArchiveListResponse(archives=archive_files)


@app.post("/api/archive/trigger", response_model=ArchiveTriggerResponse, tags=["Archives"])
async def trigger_archive(api_key: str = Security(verify_api_key)):
    """
    Trigger a manual archive of generated charts.

    Creates a ZIP archive of all PNG and HTML files in the charts
    directory, similar to the weekly cron job.
    """
    output_dir = get_output_directory()
    archives_dir = get_archives_directory()

    # Create archives directory if it doesn't exist
    os.makedirs(archives_dir, exist_ok=True)

    # Find files to archive
    png_files = glob_module.glob(os.path.join(output_dir, "tradingview_*.png"))
    html_files = glob_module.glob(os.path.join(output_dir, "tradingview_*.html"))
    files_to_archive = png_files + html_files

    if not files_to_archive:
        return ArchiveTriggerResponse(
            success=True,
            message="No chart files to archive"
        )

    # Create archive filename with date
    date_str = datetime.now().strftime("%Y-%m-%d")
    archive_filename = f"charts_{date_str}.zip"
    archive_path = os.path.join(archives_dir, archive_filename)

    try:
        # Create the zip archive
        import zipfile
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_archive:
                zipf.write(file_path, os.path.basename(file_path))

        # Remove archived files
        for file_path in files_to_archive:
            os.remove(file_path)

        return ArchiveTriggerResponse(
            success=True,
            message=f"Archived {len(files_to_archive)} files",
            archive_file=archive_filename
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Archive creation failed: {str(e)}"
        )


@app.get(
    "/api/archive/download/{filename}",
    responses={404: {"model": ErrorResponse}},
    tags=["Archives"]
)
async def download_archive(
    filename: str,
    api_key: str = Security(verify_api_key)
):
    """
    Download an archive file.

    Returns the ZIP archive file as a binary download.
    """
    archives_dir = get_archives_directory()

    # Prevent directory traversal attacks
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(archives_dir, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Archive not found: {safe_filename}"
        )

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="application/zip"
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
