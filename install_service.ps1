# ══════════════════════════════════════════════════════════════════
# Yorglass IK Chatbot API - Windows Service Kurulumu
# ══════════════════════════════════════════════════════════════════
#
# KULLANIM:
#   PowerShell'i YONETICI (Administrator) olarak ac ve calistir:
#     .\install_service.ps1
#
# ISLEMLER:
#   install   - Servisi kur ve baslat (varsayilan)
#   uninstall - Servisi kaldir
#   restart   - Servisi yeniden baslat
#
# ORNEK:
#   .\install_service.ps1              → kur ve baslat
#   .\install_service.ps1 uninstall    → kaldir
#   .\install_service.ps1 restart      → yeniden baslat
# ══════════════════════════════════════════════════════════════════

param(
    [string]$Action = "install"
)

# ── Yapilandirma ──
$ServiceName = "YorglassIKChatbot"
$ServiceDisplayName = "Yorglass IK Chatbot API"
$ServiceDescription = "IK dokumanlari uzerinde RAG tabanli soru-cevap web servisi (FastAPI)"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
$Port = 8000

# ── Yonetici kontrolu ──
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host ""
    Write-Host "HATA: Bu script YONETICI (Administrator) olarak calistirilmalidir!" -ForegroundColor Red
    Write-Host "PowerShell'i sag tiklayip 'Yonetici olarak calistir' secin." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# ── Python kontrolu ──
if (-not $PythonPath) {
    Write-Host "HATA: Python bulunamadi! PATH'e ekli oldugundan emin olun." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $PythonPath" -ForegroundColor Cyan
Write-Host "Proje : $ProjectDir" -ForegroundColor Cyan
Write-Host "Port  : $Port" -ForegroundColor Cyan
Write-Host ""

# ══════════════════════════════════════════════════════════════════
# KURULUM
# ══════════════════════════════════════════════════════════════════
function Install-ChatbotService {
    # Mevcut servisi kontrol et
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Servis zaten mevcut. Once kaldiriliyor..." -ForegroundColor Yellow
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        sc.exe delete $ServiceName | Out-Null
        Start-Sleep -Seconds 2
    }

    # Uvicorn yolunu bul
    $UvicornPath = Join-Path (Split-Path $PythonPath) "Scripts\uvicorn.exe"
    if (-not (Test-Path $UvicornPath)) {
        # pip ile kurulu degilse Scripts klasorunde olmayabilir
        $UvicornPath = (Get-Command uvicorn -ErrorAction SilentlyContinue).Source
    }
    if (-not $UvicornPath -or -not (Test-Path $UvicornPath)) {
        Write-Host "HATA: uvicorn bulunamadi! 'pip install uvicorn[standard]' calistirin." -ForegroundColor Red
        exit 1
    }
    Write-Host "Uvicorn: $UvicornPath" -ForegroundColor Cyan

    # Windows servisi olustur
    $binPath = "`"$UvicornPath`" api_server:app --host 0.0.0.0 --port $Port"

    sc.exe create $ServiceName `
        binPath= "$binPath" `
        start= auto `
        DisplayName= "$ServiceDisplayName" | Out-Null

    # Aciklama ekle
    sc.exe description $ServiceName "$ServiceDescription" | Out-Null

    # Calisma dizinini ayarla (Registry uzerinden)
    # Not: sc.exe calisma dizini desteklemez, bunu workaround ile yapiyoruz

    # Servisi baslat
    Write-Host ""
    Write-Host "Servis olusturuldu: $ServiceDisplayName" -ForegroundColor Green
    Write-Host "Baslatiliyor..." -ForegroundColor Yellow

    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3

    $svc = Get-Service -Name $ServiceName
    if ($svc.Status -eq "Running") {
        Write-Host ""
        Write-Host "════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  SERVIS BASARIYLA KURULDU VE CALISIYOR!" -ForegroundColor Green
        Write-Host "════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "  API Adresi  : http://$(hostname):$Port" -ForegroundColor White
        Write-Host "  Swagger UI  : http://$(hostname):$Port/docs" -ForegroundColor White
        Write-Host "  Health Check: http://$(hostname):$Port/health" -ForegroundColor White
        Write-Host ""
        Write-Host "  Servis her sunucu yeniden basladiginda" -ForegroundColor Gray
        Write-Host "  otomatik olarak acilacaktir." -ForegroundColor Gray
    }
    else {
        Write-Host ""
        Write-Host "UYARI: Servis baslatildi ama durum: $($svc.Status)" -ForegroundColor Yellow
        Write-Host "Alternatif olarak start_api.bat dosyasini kullanabilirsiniz." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "ONERILEN YONTEM:" -ForegroundColor Cyan
        Write-Host "Eger servis calismazsa, Gorev Zamanlayici (Task Scheduler) kullanin:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  1. Gorev Zamanlayici ac" -ForegroundColor White
        Write-Host "  2. 'Gorev Olustur' tikla" -ForegroundColor White
        Write-Host "  3. Tetikleyici: 'Bilgisayar basladiginda'" -ForegroundColor White
        Write-Host "  4. Eylem: 'Program Baslat'" -ForegroundColor White
        Write-Host "     Program : $ProjectDir\start_api.bat" -ForegroundColor White
        Write-Host "  5. 'Kullanici oturum acmasa bile calistir' sec" -ForegroundColor White
    }
}

# ══════════════════════════════════════════════════════════════════
# KALDIRMA
# ══════════════════════════════════════════════════════════════════
function Uninstall-ChatbotService {
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "Servis bulunamadi: $ServiceName" -ForegroundColor Yellow
        return
    }

    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    sc.exe delete $ServiceName | Out-Null

    Write-Host "Servis basariyla kaldirildi: $ServiceDisplayName" -ForegroundColor Green
}

# ══════════════════════════════════════════════════════════════════
# YENIDEN BASLATMA
# ══════════════════════════════════════════════════════════════════
function Restart-ChatbotService {
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existing) {
        Write-Host "Servis bulunamadi. Once kurulum yapin." -ForegroundColor Yellow
        return
    }

    Restart-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 3
    $svc = Get-Service -Name $ServiceName
    Write-Host "Servis yeniden baslatildi. Durum: $($svc.Status)" -ForegroundColor Green
}

# ══════════════════════════════════════════════════════════════════
# FIREWALL KURAL EKLEME
# ══════════════════════════════════════════════════════════════════
function Add-FirewallRule {
    $existing = Get-NetFirewallRule -DisplayName "Yorglass IK Chatbot API" -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Firewall kurali zaten mevcut." -ForegroundColor Yellow
        return
    }

    New-NetFirewallRule `
        -DisplayName "Yorglass IK Chatbot API" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $Port `
        -Action Allow `
        -Profile Domain,Private | Out-Null

    Write-Host "Firewall kurali eklendi: Port $Port (Domain + Private)" -ForegroundColor Green
}

# ── Action'a gore calistir ──
switch ($Action.ToLower()) {
    "install" {
        Add-FirewallRule
        Install-ChatbotService
    }
    "uninstall" {
        Uninstall-ChatbotService
    }
    "restart" {
        Restart-ChatbotService
    }
    default {
        Write-Host "Gecersiz islem: $Action" -ForegroundColor Red
        Write-Host "Kullanim: .\install_service.ps1 [install|uninstall|restart]"
    }
}
