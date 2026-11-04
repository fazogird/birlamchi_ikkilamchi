@echo off
chcp 65001 >nul
rem ===================================================================
rem  2-BOSQICH: qo'lda tuzatilgan ekin_yerlar_yakuniy.gpkg ->
rem             ekin_yerlar_toliq_*.gpkg (backup) + ekin_yerlar_qisqa_*.gpkg
rem  Ikki marta bosing. Gpkg faylini tanlash oynasi chiqadi.
rem  ArcGIS GUID ko'rinishidagi ID kerak bo'lsa: 2_EKSPORT.bat --format arcgis
rem ===================================================================
set "ENV=%LOCALAPPDATA%\miniconda3\envs\gis_pro"
if not exist "%ENV%\python.exe" (
  echo gis_pro muhiti topilmadi: %ENV%
  echo Ushbu faylni Bloknotda ochib, ENV qatoriga to'g'ri yo'lni yozing.
  pause
  exit /b 1
)
"%ENV%\python.exe" "%~dp0pipeline.py" eksport %*
echo.
pause
