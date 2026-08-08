@echo off
chcp 1251 >nul
setlocal
cd /d "%~dp0.."

set V8_PATH=C:\Program Files\1cv8\8.3.27.1859\bin\1cv8.exe
set SRC_DIR=_work\src
set OUT_DIR=output
set EPF_NAME=ÂûãğóçêàÇàãğóçêàÓÏÁÏ_v1.00.epf

echo Òåêóùèé êàòàëîã: %CD%

if not exist "%V8_PATH%" (
    echo [ÎØÈÁÊÀ] 1cv8.exe íå íàéäåí
    pause & exit /b 1
)

dir /b /a-d "%SRC_DIR%\*.xml" >nul 2>&1 || (
    echo [ÎØÈÁÊÀ] XML íå íàéäåí â %SRC_DIR%
    pause & exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo Ñáîğêà EPF...

"%V8_PATH%" DESIGNER /BuildEPF "%SRC_DIR%\ÂûãğóçêàÇàãğóçêàÓÏÁÏ.xml" /Out "%OUT_DIR%\%EPF_NAME%" /DisableStartupDialogs > "_work\build.log" 2>&1 > "_work\build.log" 2>&1
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE%==0 (
    echo [ÃÎÒÎÂÎ] %OUT_DIR%\%EPF_NAME%
    goto :end
)

echo [ÎØÈÁÊÀ] Ñáîğêà íå óäàëàñü (êîä: %EXIT_CODE%^)
echo Óáèâàş çàâèñøèé ïğîöåññ 1cv8...
taskkill /f /im 1cv8.exe 2>nul
echo Ïîâòîğíàÿ ïîïûòêà...

"%V8_PATH%" DESIGNER /BuildEPF "%SRC_DIR%\ÂûãğóçêàÇàãğóçêàÓÏÁÏ.xml" /Out "%OUT_DIR%\%EPF_NAME%" /DisableStartupDialogs > "_work\build.log" 2>&1 > "_work\build.log" 2>&1
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE%==0 (
    echo [ÃÎÒÎÂÎ] %OUT_DIR%\%EPF_NAME%
) else (
    echo [ÎØÈÁÊÀ] Ïîâòîğíàÿ ñáîğêà íå óäàëàñü (êîä: %EXIT_CODE%^)
    taskkill /f /im 1cv8.exe 2>nul
)

:end
pause
