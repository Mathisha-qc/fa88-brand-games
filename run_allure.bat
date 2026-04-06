@echo off
title HitClub Allure Reporter
echo 🚀 Starting Automation...

:: 1. Clean old results so the report is fresh
if exist allure-results rmdir /s /q allure-results

:: 2. Run the Python tests
:: This will trigger your LoginPage and GamePage @allure.steps
pytest --alluredir=allure-results

:: 3. Generate the "Best Steps" HTML Viewer
:: This requires the Java path we set earlier
echo 📊 Opening Allure Dashboard...
allure serve allure-results

pause