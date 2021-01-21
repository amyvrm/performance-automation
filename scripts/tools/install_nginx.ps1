Expand-Archive -Path "C:/temp/nginx-1.19.2ready.zip" -DestinationPath "C:/temp/"
Start-Sleep -s 1
Start-Process "C:/temp/nginx-1.19.2/nginx.exe" \s
Start-Sleep -s 2