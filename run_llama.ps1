[CmdletBinding()]
param(
    # モデルのファイル名のみを指定（デフォルト値あり）
    [Parameter(Position = 0)]
    [string]$ModelName = "mistralai_Devstral-Small-2-24B-Instruct-2512-Q4_K_M.gguf",

    # ポート番号
    [Parameter(Position = 1)]
    [int]$Port = 11435
)

# 1. 管理者権限チェック（未昇格の場合は引数を引き継いで昇格）
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -ModelName `"$ModelName`" -Port $Port" -Verb RunAs
    exit
}

# --- 基本設定 ---
$hardwareId = "VEN_10DE&DEV_1F06"
$llamaExe   = "C:\llama\llama-server.exe"  # ※実際の llama-server のパス
$modelsDir  = "C:\llama\models"            # ※モデル格納フォルダ
# ----------------

# .gguf 拡張子の補完
if (-not $ModelName.EndsWith(".gguf", [System.StringComparison]::OrdinalIgnoreCase)) {
    $ModelName = "$ModelName.gguf"
}

$fullModelPath = Join-Path -Path $modelsDir -ChildPath $ModelName
if (-not (Test-Path $fullModelPath)) {
    Write-Error "指定されたモデルファイルが見つかりません: $fullModelPath"
    Read-Host "Enterキーを押して終了してください..."
    exit
}

# 2. 稼働中の llama-server があれば終了して VRAM を確実に解放（二重起動防止）
$existing = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[VRAM解放] 既存の llama-server を終了してモデルを切り替えます..." -ForegroundColor Yellow
    $existing | Stop-Process -Force
    Start-Sleep -Seconds 1
}

# 3. 対象 GPU の取得
$device = Get-PnpDevice | Where-Object { $_.HardwareID -like "*$hardwareId*" }
if (-not $device) {
    Write-Error "指定されたGPU ($hardwareId) が見つかりませんでした。"
    Read-Host "Enterキーを押して終了してください..."
    exit
}
$instanceId = $device.InstanceId

try {
    # 4. GPU 有効化 & 130W 設定（既に有効なら待機時間をスキップ）
    if ($device.Status -ne "OK") {
        Write-Host "[1/3] GPUを有効化しています: $instanceId" -ForegroundColor Green
        & "C:\Windows\System32\pnputil.exe" /enable-device "$instanceId" | Out-Null
        
        Write-Host "Vulkan初期化待機中..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
        
        Write-Host "[2/3] 電力制限を130Wに設定しています..." -ForegroundColor Green
        & "C:\Windows\System32\nvidia-smi.exe" -pl 130 | Out-Null
    } else {
        Write-Host "[GPU状態] GPUは既に有効化されています。" -ForegroundColor Green
    }

    # 5. llama-server 引数組み立て（--models-path を除外し、元の引数構成に準拠）
    $llamaArgs = @(
        "-m", $fullModelPath,
        "-dev", "Vulkan0,Vulkan1",
        "-sm", "layer",
        "-ngl", "99",
        "-c", "32768",
        "-np", "1",
        "--port", $Port
    )

    Write-Host "[3/3] llama-server を起動します (Port: $Port)" -ForegroundColor Cyan
    Write-Host "Model: $fullModelPath" -ForegroundColor Gray
    
    $process = Start-Process -FilePath $llamaExe -ArgumentList $llamaArgs -PassThru -NoNewWindow
    Write-Host "`nllama-server が起動しました (PID: $($process.Id))。終了するには Ctrl+C を押してください。" -ForegroundColor Yellow

    # プロセス終了待機
    $process.WaitForExit()

} finally {
    # 6. 終了処理: 完全に終了した時のみ GPU を無効化
    Write-Host "`nllama-server の終了を検知しました。" -ForegroundColor Yellow
    
    $remaining = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $process.Id }
    if (-not $remaining) {
        Write-Host "GPUを無効化（Disable）しています..." -ForegroundColor Red
        & "C:\Windows\System32\pnputil.exe" /disable-device "$instanceId" | Out-Null
        Write-Host "GPUを無効化しました。" -ForegroundColor Gray
    }
}