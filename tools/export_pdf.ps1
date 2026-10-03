param(
    [string]$SrcDir = "docs",
    [string]$OutDir = "."
)
# Export every .docx found in $SrcDir to same-name .pdf in $OutDir,
# and print page counts. ASCII-only on purpose: avoids code page issues.
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

Get-ChildItem -Path $SrcDir -Filter *.docx | ForEach-Object {
    $docPath = $_.FullName
    $pdfPath = Join-Path $OutDir ($_.BaseName + ".pdf")
    $doc = $word.Documents.Open($docPath, $false, $true)
    $pages = $doc.ComputeStatistics(2)
    Write-Output ("PAGES " + $_.BaseName + " = " + $pages)
    $doc.ExportAsFixedFormat($pdfPath, 17)
    $doc.Close($false)
}
$word.Quit()
Write-Output "DONE"
