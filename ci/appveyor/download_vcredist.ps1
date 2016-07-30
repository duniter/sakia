Param([String]$target)

Write-Host "Downloading vcredist to $target"
(New-Object Net.WebClient).DownloadFile('https://download.microsoft.com/download/A/4/D/A4D9F1D3-6449-49EB-9A6E-902F61D8D14B/vcredist_x86.exe', "$target\vcredist_x86.exe")
(New-Object Net.WebClient).DownloadFile('https://download.microsoft.com/download/A/4/D/A4D9F1D3-6449-49EB-9A6E-902F61D8D14B/vcredist_x64.exe', "$target\vcredist_x64.exe")

