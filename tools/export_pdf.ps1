param(
    [string]$SrcDir = "docs",
    [string]$OutDir = ".",
    [string]$Log = ""
)
# Export every .docx found in $SrcDir to same-name .pdf in $OutDir,
# and print page counts. ASCII-only on purpose: avoids code page issues.
#
# Each document is also opened writable and re-saved once: Word then rewrites
# docProps/app.xml (application name, word/page counts) and stamps itself as
# last modifier, which is what a normally hand-edited .docx looks like.
#
# Robustness notes (learned the hard way):
#  - Stale Word AutoRecovery files (*.asd, left behind when Word is killed)
#    make Word hang forever at startup under COM, because the recovery pane
#    cannot be shown on a hidden window. So hide them before starting.
#  - One fresh Word instance per document: a poisoned instance then cannot
#    take the remaining documents down with it. Each step is logged.
#  - NEVER build a COM argument with Join-Path: the string it returns carries
#    ETS note properties (Drive/Provider), and handing that to Word's COM
#    methods (ExportAsFixedFormat) makes Word spin forever instead of
#    exporting. Use [System.IO.Path]::Combine for plain .NET strings.

if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}
if (-not $Log) { $Log = [System.IO.Path]::Combine($env:TEMP, "packetlens_export_pdf.log") }

function Log-Line([string]$msg) {
    $line = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "  " + $msg
    Add-Content -Path $Log -Value $line
    Write-Output $line
}

$recoveryDir = Join-Path $env:APPDATA "Microsoft\Word"
Get-ChildItem -Path $recoveryDir -Filter *.asd -EA SilentlyContinue | ForEach-Object {
    Move-Item -LiteralPath $_.FullName -Destination ($_.FullName + ".bak") -Force
    Log-Line ("hid stale AutoRecovery: " + $_.Name)
}

Log-Line ("START  src=" + $SrcDir + "  out=" + $OutDir)

Get-ChildItem -Path $SrcDir -Filter *.docx | ForEach-Object {
    $f = $_
    $pdfPath = [System.IO.Path]::Combine($OutDir, ($f.BaseName + ".pdf"))
    $word = $null
    try {
        Log-Line ("OPEN   " + $f.Name)
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        # Open writable (3rd arg $false) so the Save below can rewrite the
        # document properties. NOTE: never put non-ASCII in this file -- it has
        # no BOM, so PowerShell 5.1 reads it as GBK and the bytes eat the next
        # line of code.
        $doc = $word.Documents.Open($f.FullName, $false, $false)
        Log-Line ("PAGES  " + $f.BaseName + " = " + $doc.ComputeStatistics(2))
        $doc.Save()
        $doc.ExportAsFixedFormat($pdfPath, 17)
        $doc.Close($false)
        $word.Quit()
        Log-Line ("PDF    " + $f.BaseName + ".pdf written")
    } catch {
        Log-Line ("ERROR  " + $f.Name + " : " + $_.Exception.Message)
        if ($word) { try { $word.Quit() } catch {} }
    }
}
Log-Line "DONE"
