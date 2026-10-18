Add-Type -AssemblyName System.Drawing

$assetsDir = Join-Path $PSScriptRoot "assets"
if (-not (Test-Path $assetsDir)) {
    New-Item -ItemType Directory -Force -Path $assetsDir | Out-Null
}

$icoPath = Join-Path $assetsDir "app_icon.ico"

$size = 256
$bmp = New-Object System.Drawing.Bitmap $size, $size
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.Clear([System.Drawing.Color]::Transparent)

# Draw Rounded Shield Background
$shieldPath = New-Object System.Drawing.Drawing2D.GraphicsPath
$pts = @(
    (New-Object System.Drawing.PointF 128, 16),
    (New-Object System.Drawing.PointF 232, 52),
    (New-Object System.Drawing.PointF 232, 148),
    (New-Object System.Drawing.PointF 128, 240),
    (New-Object System.Drawing.PointF 24, 148),
    (New-Object System.Drawing.PointF 24, 52)
)
$shieldPath.AddPolygon($pts)

# Dark gradient fill for shield (Obsidian & Navy)
$brush = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 16), (New-Object System.Drawing.Point 0, 240), ([System.Drawing.Color]::FromArgb(255, 30, 36, 60)), ([System.Drawing.Color]::FromArgb(255, 13, 15, 23))
$g.FillPath($brush, $shieldPath)

# Glowing Indigo/Cyan Border
$borderPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 99, 102, 241)), 10
$g.DrawPath($borderPen, $shieldPath)

$innerPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 6, 182, 212)), 3
$g.DrawPath($innerPen, $shieldPath)

# Draw Lightning Apex Bolt (Golden Yellow & White)
$boltPath = New-Object System.Drawing.Drawing2D.GraphicsPath
$boltPts = @(
    (New-Object System.Drawing.PointF 140, 48),
    (New-Object System.Drawing.PointF 84, 136),
    (New-Object System.Drawing.PointF 124, 136),
    (New-Object System.Drawing.PointF 108, 208),
    (New-Object System.Drawing.PointF 176, 116),
    (New-Object System.Drawing.PointF 136, 116)
)
$boltPath.AddPolygon($boltPts)

$boltBrush = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.Point 0, 48), (New-Object System.Drawing.Point 0, 208), ([System.Drawing.Color]::FromArgb(255, 255, 215, 0)), ([System.Drawing.Color]::FromArgb(255, 245, 158, 11))
$g.FillPath($boltBrush, $boltPath)

$boltPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 255, 255, 255)), 2
$g.DrawPath($boltPen, $boltPath)

$g.Flush()

# Save as ICO via HIcon
$hIcon = $bmp.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($hIcon)
$fileStream = [System.IO.File]::OpenWrite($icoPath)
$icon.Save($fileStream)
$fileStream.Close()
$icon.Dispose()
$bmp.Dispose()
$g.Dispose()

Write-Host "Application icon created at: $icoPath"
