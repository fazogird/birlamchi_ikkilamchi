@echo off
chcp 65001 >nul
rem ===================================================================
rem  1-BOSQICH: asl shp -> ekin_yerlar_yakuniy.gpkg + xatolar_hisoboti.xlsx
rem  Ikki marta bosing. Shp faylini tanlash oynasi chiqadi.
rem  gis_pro muhiti boshqa joyda bo'lsa, quyidagi ENV qatorini o'zgartiring.
rem ===================================================================
set "ENV=%LOCALAPPDATA%\miniconda3\envs\gis_pro"
if not exist "%ENV%\python.exe" (
  echo gis_pro muhiti topilmadi: %ENV%
  echo Ushbu faylni Bloknotda ochib, ENV qatoriga to'g'ri yo'lni yozing.
  pause
  exit /b 1
)
"%ENV%\python.exe" "%~dp0pipeline.py" tayyorla %*
echo.
pause
