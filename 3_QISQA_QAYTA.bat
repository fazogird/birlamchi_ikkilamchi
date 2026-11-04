@echo off
chcp 65001 >nul
rem ===================================================================
rem  QO'SHIMCHA: mavjud to'liq versiyadan (ekin_yerlar_toliq_*.gpkg)
rem  qisqa versiyani qayta yasash. uniqueid O'ZGARMAYDI.
rem  Baliqxovuz va Issiqxona qisqa versiyaga kirmaydi.
rem  Ikki marta bosing. To'liq versiya faylini tanlash oynasi chiqadi.
rem ===================================================================
set "ENV=%LOCALAPPDATA%\miniconda3\envs\gis_pro"
if not exist "%ENV%\python.exe" (
  echo gis_pro muhiti topilmadi: %ENV%
  echo Ushbu faylni Bloknotda ochib, ENV qatoriga to'g'ri yo'lni yozing.
  pause
  exit /b 1
)
"%ENV%\python.exe" "%~dp0pipeline.py" qisqa %*
echo.
pause
