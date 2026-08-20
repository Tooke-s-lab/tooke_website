@echo off
REM Starts a local web server for previewing the site, then opens it.
REM
REM Why this exists: opening the .html files straight from Explorer gives them a
REM file:// address, and browsers block two things there that the site needs —
REM the structure viewer loading .pdb files, and any fetch of local data. The
REM pages will look broken in ways that are nothing to do with the pages.
REM
REM Port 8899 is fixed on purpose. Bookmark http://localhost:8899/ and it will
REM always be the right address; a different port means a stale tab pointing at
REM a server that is no longer running, which looks exactly like a broken site.
REM
REM Leave this window open while you browse. Close it, or press Ctrl+C, to stop.

cd /d "%~dp0"
echo.
echo   The Tooke Lab — local preview
echo   ------------------------------------------------
echo   Site        http://localhost:8899/
echo   News studio http://localhost:8899/studio.html
echo.
echo   Leave this window open. Ctrl+C to stop.
echo.
start "" "http://localhost:8899/"
python -m http.server 8899 --bind 127.0.0.1
