@echo off
setlocal EnableDelayedExpansion


set GC_VERSION_URL=https://github.com/l3v11/gclone/releases/download/v1.62.2-purple/gclone-v1.62.2-purple-windows-amd64.zip
set GC_ZIP=gclone.zip
set GC_EXE=gclone.exe
set GC_TEMP_EXTRACT=temp_gclone



set CRED_B64=hehehaha

set ROOT_B64=ffoollddeerr


if not exist "%~dp0accounts" mkdir "%~dp0accounts"


if not exist "%~dp0%GC_EXE%" (
    echo Downloading gclone...
    if exist "%~dp0%GC_ZIP%" del /f /q "%~dp0%GC_ZIP%"
    powershell -Command "Invoke-WebRequest -Uri '%GC_VERSION_URL%' -OutFile '%GC_ZIP%'"
    echo Waiting for file handle to release...
    timeout /t 2 >nul
    echo Extracting gclone...
    if exist "%~dp0%GC_TEMP_EXTRACT%" rd /s /q "%~dp0%GC_TEMP_EXTRACT%"
    powershell -Command "Expand-Archive -Path '%GC_ZIP%' -DestinationPath '%~dp0%GC_TEMP_EXTRACT%' -Force"
    echo Moving gclone.exe to script folder...
    for /r "%~dp0%GC_TEMP_EXTRACT%" %%f in (gclone.exe) do move "%%f" "%~dp0"
    rd /s /q "%~dp0%GC_TEMP_EXTRACT%"
    del "%~dp0%GC_ZIP%"
) else (
    echo gclone.exe already exists, skipping download.
)



powershell -Command "$bytes = [Text.Encoding]::UTF8.GetBytes([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('%CRED_B64%'))); [IO.File]::WriteAllBytes('%~dp0accounts\\0.json', $bytes)"



for /f "delims=" %%i in ('powershell -Command "[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('%ROOT_B64%'))"') do set ROOT_ID=%%i


echo [sadrive]>"%~dp0rclone.conf"
echo type = drive>>"%~dp0rclone.conf"
echo scope = drive>>"%~dp0rclone.conf"
echo service_account_file = %~dp0accounts\0.json>>"%~dp0rclone.conf"
echo service_account_file_path = %~dp0accounts>>"%~dp0rclone.conf"
echo root_folder_id = !ROOT_ID!>>"%~dp0rclone.conf"


echo Mounting sadrive: ...
"%~dp0%GC_EXE%" mount sadrive: * --read-only --vfs-cache-mode full --vfs-cache-max-size 1G --vfs-cache-max-age 12h

echo Done.
endlocal
