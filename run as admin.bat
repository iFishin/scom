@echo off
setlocal

REM Set the working directory to the directory of the batch file
cd /d %~dp0

REM Query the registry value
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled > nul 2>&1

REM Check the query result
if %errorlevel% neq 0 (
    echo Registry key does not exist or cannot be accessed.
    goto EnableLongPaths
)

for /f "tokens=3" %%A in ('reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled 2^>nul') do (
    if %%A==0x1 (
        echo Registry value is correct.
        goto Continue
    ) else (
        goto EnableLongPaths
    )
)

:EnableLongPaths
REM Add or modify the registry value
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f
if %errorlevel% neq 0 (
    echo Failed to modify the registry value.
    exit /b 1
)

REM Prompt the user to restart the computer
echo Long path support has been enabled. A restart is required.
msg * "Long path support has been enabled. The computer will restart in 3 seconds. Click OK to proceed or Cancel to exit." /time:3

REM Restart the computer after 3 seconds
shutdown /r /t 3
goto End

:Continue
REM Install python requirements
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
) else (
    echo Dependencies installed successfully.
)
pause

echo Run the program
python window.py
pause

:End
endlocal