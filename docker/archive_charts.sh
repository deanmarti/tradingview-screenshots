#!/bin/bash
# Archive charts weekly - runs every Sunday at 23:30

CHARTS_DIR="/app/output"
ARCHIVES_DIR="/app/archives"
DATE=$(date +%Y-%m-%d)
ARCHIVE_NAME="charts_${DATE}.zip"

# Check if there are any files to archive
if [ -n "$(ls -A ${CHARTS_DIR}/*.png 2>/dev/null)" ] || [ -n "$(ls -A ${CHARTS_DIR}/*.html 2>/dev/null)" ]; then
    echo "$(date): Archiving charts to ${ARCHIVE_NAME}"

    # Create zip archive
    cd ${CHARTS_DIR}
    zip -j ${ARCHIVES_DIR}/${ARCHIVE_NAME} *.png *.html 2>/dev/null

    # Remove archived files
    rm -f ${CHARTS_DIR}/*.png ${CHARTS_DIR}/*.html

    echo "$(date): Archive complete - ${ARCHIVES_DIR}/${ARCHIVE_NAME}"
else
    echo "$(date): No charts to archive"
fi
