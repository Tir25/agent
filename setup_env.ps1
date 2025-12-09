#Requires -Version 5.1
<#
.SYNOPSIS
    The Sovereign Desktop - Environment Setup Script
    
.DESCRIPTION
    This script sets up the complete development environment for The Sovereign Desktop agent:
    - Validates Python 3.11+ installation
    - Creates a virtual environment
    - Checks/prompts for Ollama installation
    - Pulls required AI models
    
.NOTES
    Author: Sovereign Desktop Team
    Version: 1.0.0
    Run this script from the project root directory.
#>

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$VENV_NAME = "sovereign_agent"
$MIN_PYTHON_VERSION = [Version]"3.11.0"

$OLLAMA_MODELS = @(
    @{ Name = "llama3.2-vision"; Purpose = "Vision/Perception - Multimodal understanding" },
    @{ Name = "llama3.2:3b"; Purpose = "Semantic Router - Fast intent classification" },
    @{ Name = "nomic-embed-text"; Purpose = "Embeddings - Text classification" }
)

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Banner {
    $banner = @"

    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              🏛️  THE SOVEREIGN DESKTOP                        ║
    ║              Your AI, Your Machine, Your Rules                ║
    ║                                                               ║
    ║              Environment Setup Script v1.0                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message, [string]$Icon = "→")
    Write-Host "`n$Icon " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor White
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ " -ForegroundColor Green -NoNewline
    Write-Host $Message -ForegroundColor Gray
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠ " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor Gray
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ✗ " -ForegroundColor Red -NoNewline
    Write-Host $Message -ForegroundColor Gray
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor Gray
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Get-PythonVersion {
    param([string]$PythonPath)
    try {
        $versionOutput = & $PythonPath --version 2>&1
        if ($versionOutput -match "Python (\d+\.\d+\.\d+)") {
            return [Version]$Matches[1]
        }
    } catch {
        return $null
    }
    return $null
}

# ============================================================================
# Step 1: Check Python Installation
# ============================================================================

function Test-PythonInstallation {
    Write-Step "Checking Python installation..."
    
    # Try different Python commands
    $pythonCandidates = @("python", "python3", "py -3.11", "py -3")
    $selectedPython = $null
    $selectedVersion = $null
    
    foreach ($candidate in $pythonCandidates) {
        $parts = $candidate -split " "
        $cmd = $parts[0]
        $args = if ($parts.Length -gt 1) { $parts[1..($parts.Length-1)] } else { @() }
        
        if (Test-CommandExists $cmd) {
            try {
                if ($args.Length -gt 0) {
                    $versionOutput = & $cmd @args --version 2>&1
                } else {
                    $versionOutput = & $cmd --version 2>&1
                }
                
                if ($versionOutput -match "Python (\d+\.\d+\.\d+)") {
                    $version = [Version]$Matches[1]
                    if ($version -ge $MIN_PYTHON_VERSION) {
                        $selectedPython = $candidate
                        $selectedVersion = $version
                        break
                    }
                }
            } catch {
                continue
            }
        }
    }
    
    if ($selectedPython) {
        Write-Success "Found Python $selectedVersion (using: $selectedPython)"
        return $selectedPython
    } else {
        Write-Error "Python 3.11+ is required but not found."
        Write-Host ""
        Write-Host "  Please install Python 3.11 or higher from:" -ForegroundColor White
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
        Write-Host ""
        
        $install = Read-Host "  Would you like to open the download page? (y/n)"
        if ($install -eq "y" -or $install -eq "Y") {
            Start-Process "https://www.python.org/downloads/"
        }
        
        throw "Python 3.11+ is required. Please install it and run this script again."
    }
}

# ============================================================================
# Step 2: Create Virtual Environment
# ============================================================================

function New-VirtualEnvironment {
    param([string]$PythonCmd)
    
    Write-Step "Setting up virtual environment '$VENV_NAME'..."
    
    $venvPath = Join-Path $PSScriptRoot $VENV_NAME
    
    if (Test-Path $venvPath) {
        Write-Warning "Virtual environment already exists at: $venvPath"
        $recreate = Read-Host "  Do you want to recreate it? (y/n)"
        
        if ($recreate -eq "y" -or $recreate -eq "Y") {
            Write-Info "Removing existing virtual environment..."
            Remove-Item -Recurse -Force $venvPath
        } else {
            Write-Success "Using existing virtual environment"
            return $venvPath
        }
    }
    
    Write-Info "Creating virtual environment..."
    
    # Parse Python command
    $parts = $PythonCmd -split " "
    $cmd = $parts[0]
    $args = if ($parts.Length -gt 1) { $parts[1..($parts.Length-1)] + @("-m", "venv", $VENV_NAME) } else { @("-m", "venv", $VENV_NAME) }
    
    try {
        & $cmd @args
        
        if (Test-Path $venvPath) {
            Write-Success "Virtual environment created at: $venvPath"
            
            # Upgrade pip
            $pipPath = Join-Path $venvPath "Scripts\pip.exe"
            Write-Info "Upgrading pip..."
            & $pipPath install --upgrade pip --quiet
            Write-Success "pip upgraded successfully"
            
            return $venvPath
        } else {
            throw "Virtual environment was not created"
        }
    } catch {
        Write-Error "Failed to create virtual environment: $_"
        throw
    }
}

# ============================================================================
# Step 3: Check Ollama Installation
# ============================================================================

function Test-OllamaInstallation {
    Write-Step "Checking Ollama installation..."
    
    if (Test-CommandExists "ollama") {
        try {
            $versionOutput = & ollama --version 2>&1
            Write-Success "Ollama is installed: $versionOutput"
            return $true
        } catch {
            Write-Warning "Ollama command found but may not be working properly"
        }
    }
    
    Write-Error "Ollama is not installed or not in PATH."
    Write-Host ""
    Write-Host "  Ollama is required for local LLM inference." -ForegroundColor White
    Write-Host "  Download from: https://ollama.ai/download" -ForegroundColor Cyan
    Write-Host ""
    
    $install = Read-Host "  Would you like to open the download page? (y/n)"
    if ($install -eq "y" -or $install -eq "Y") {
        Start-Process "https://ollama.ai/download"
        Write-Host ""
        Write-Host "  After installing Ollama:" -ForegroundColor Yellow
        Write-Host "  1. Restart your terminal" -ForegroundColor Gray
        Write-Host "  2. Run 'ollama serve' to start the service" -ForegroundColor Gray
        Write-Host "  3. Run this script again" -ForegroundColor Gray
        Write-Host ""
    }
    
    return $false
}

function Test-OllamaRunning {
    Write-Info "Checking if Ollama service is running..."
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        Write-Success "Ollama service is running"
        return $true
    } catch {
        Write-Warning "Ollama service is not running"
        Write-Host ""
        Write-Host "  Please start Ollama by running:" -ForegroundColor White
        Write-Host "  ollama serve" -ForegroundColor Cyan
        Write-Host ""
        
        $start = Read-Host "  Would you like to start Ollama now? (y/n)"
        if ($start -eq "y" -or $start -eq "Y") {
            Write-Info "Starting Ollama in a new window..."
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized
            
            # Wait for service to start
            Write-Info "Waiting for Ollama service to start..."
            $maxAttempts = 10
            $attempt = 0
            
            while ($attempt -lt $maxAttempts) {
                Start-Sleep -Seconds 2
                try {
                    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3
                    Write-Success "Ollama service started successfully"
                    return $true
                } catch {
                    $attempt++
                    Write-Host "    Waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
                }
            }
            
            Write-Error "Failed to start Ollama service"
            return $false
        }
        
        return $false
    }
}

# ============================================================================
# Step 4: Pull Required Models
# ============================================================================

function Get-OllamaModels {
    Write-Step "Pulling required Ollama models..."
    Write-Host ""
    Write-Host "  This may take a while depending on your internet connection." -ForegroundColor Gray
    Write-Host "  Models will be downloaded to Ollama's cache (~5-10 GB total)." -ForegroundColor Gray
    Write-Host ""
    
    $failed = @()
    
    foreach ($model in $OLLAMA_MODELS) {
        $modelName = $model.Name
        $modelPurpose = $model.Purpose
        
        Write-Host "  📦 " -ForegroundColor Magenta -NoNewline
        Write-Host "Pulling " -NoNewline
        Write-Host $modelName -ForegroundColor Cyan -NoNewline
        Write-Host " ($modelPurpose)..." -ForegroundColor Gray
        
        try {
            # Check if model already exists
            $existingModels = & ollama list 2>&1
            if ($existingModels -match [regex]::Escape($modelName)) {
                Write-Host "     Already downloaded ✓" -ForegroundColor Green
                continue
            }
            
            # Pull the model
            & ollama pull $modelName
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "     Downloaded successfully ✓" -ForegroundColor Green
            } else {
                throw "Pull command returned error code $LASTEXITCODE"
            }
        } catch {
            Write-Host "     Failed to download ✗" -ForegroundColor Red
            $failed += $modelName
        }
    }
    
    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Warning "Some models failed to download:"
        foreach ($model in $failed) {
            Write-Host "     - $model" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "  You can manually pull them later with:" -ForegroundColor Gray
        Write-Host "  ollama pull <model_name>" -ForegroundColor Cyan
    }
    
    return $failed.Count -eq 0
}

# ============================================================================
# Step 5: Install Python Dependencies
# ============================================================================

function Install-PythonDependencies {
    param([string]$VenvPath)
    
    Write-Step "Installing Python dependencies..."
    
    $pipPath = Join-Path $VenvPath "Scripts\pip.exe"
    $requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
    
    if (-not (Test-Path $requirementsPath)) {
        Write-Warning "requirements.txt not found, skipping dependency installation"
        return
    }
    
    try {
        Write-Info "Installing from requirements.txt..."
        & $pipPath install -r $requirementsPath --quiet
        Write-Success "Python dependencies installed successfully"
    } catch {
        Write-Error "Failed to install some dependencies: $_"
        Write-Host "  You may need to install them manually with:" -ForegroundColor Gray
        Write-Host "  .\$VENV_NAME\Scripts\pip install -r requirements.txt" -ForegroundColor Cyan
    }
}

# ============================================================================
# Step 6: Create .env Template
# ============================================================================

function New-EnvTemplate {
    Write-Step "Creating .env configuration template..."
    
    $envPath = Join-Path $PSScriptRoot ".env"
    $envExamplePath = Join-Path $PSScriptRoot ".env.example"
    
    $envContent = @"
# ============================================================================
# The Sovereign Desktop - Environment Configuration
# ============================================================================
# Copy this file to .env and customize for your system.
# All values with defaults can be left empty to use the default.

# ============================================================================
# LLM Configuration (Ollama)
# ============================================================================

# Ollama API host (default: http://localhost:11434)
OLLAMA_HOST=http://localhost:11434

# Vision model for screen understanding
VISION_MODEL=llama3.2-vision

# Fast model for semantic routing
ROUTER_MODEL=llama3.2:3b

# Embedding model for classification
EMBEDDING_MODEL=nomic-embed-text

# Default temperature for LLM responses (0.0 - 1.0)
LLM_TEMPERATURE=0.7

# Maximum context length in tokens
LLM_CONTEXT_LENGTH=8192

# ============================================================================
# Browser Configuration
# ============================================================================

# Path to Chrome User Data directory for browser automation
# Windows default: C:\Users\<username>\AppData\Local\Google\Chrome\User Data
CHROME_USER_DATA_PATH=

# Chrome profile to use (default: Default)
CHROME_PROFILE=Default

# Run browser in headless mode (true/false)
BROWSER_HEADLESS=false

# ============================================================================
# Voice Configuration
# ============================================================================

# Speech-to-Text engine (faster_whisper, whisper, windows)
STT_ENGINE=faster_whisper

# Whisper model size (tiny, base, small, medium, large)
STT_MODEL_SIZE=base

# Text-to-Speech engine (sapi, piper, edge)
TTS_ENGINE=sapi

# TTS voice ID (leave empty for default)
TTS_VOICE=

# Language code for speech recognition
LANGUAGE=en

# Push-to-talk hotkey
PUSH_TO_TALK_KEY=ctrl+space

# Wake word (leave empty to disable)
WAKE_WORD=

# ============================================================================
# Vision Configuration
# ============================================================================

# OCR backend (tesseract, easyocr)
OCR_BACKEND=tesseract

# Path to Tesseract executable (if not in PATH)
# Windows default: C:\Program Files\Tesseract-OCR\tesseract.exe
TESSERACT_PATH=

# Screen capture interval in seconds
CAPTURE_INTERVAL=1.0

# Maximum screenshot resolution (width,height)
MAX_RESOLUTION=1920,1080

# ============================================================================
# Paths & Storage
# ============================================================================

# Data directory for persistent storage
DATA_DIR=data

# Logs directory
LOGS_DIR=logs

# Plugins directory
PLUGINS_DIR=plugins

# ============================================================================
# Debug & Development
# ============================================================================

# Enable debug mode (true/false)
DEBUG=false

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable action logging for audit trail
LOG_ACTIONS=true
"@

    # Create .env.example
    Set-Content -Path $envExamplePath -Value $envContent -Encoding UTF8
    Write-Success "Created .env.example template"
    
    # Create .env if it doesn't exist
    if (-not (Test-Path $envPath)) {
        Set-Content -Path $envPath -Value $envContent -Encoding UTF8
        Write-Success "Created .env configuration file"
        Write-Info "Edit .env to customize your configuration"
    } else {
        Write-Warning ".env already exists, not overwriting"
        Write-Info "Check .env.example for new configuration options"
    }
}

# ============================================================================
# Step 7: Create Activation Script
# ============================================================================

function New-ActivationScript {
    Write-Step "Creating activation convenience script..."
    
    $activatePath = Join-Path $PSScriptRoot "activate.ps1"
    
    $activateContent = @"
# The Sovereign Desktop - Quick Activation Script
# Run this to activate the virtual environment and start working

`$venvPath = Join-Path `$PSScriptRoot "$VENV_NAME"
`$activateScript = Join-Path `$venvPath "Scripts\Activate.ps1"

if (Test-Path `$activateScript) {
    . `$activateScript
    Write-Host ""
    Write-Host "  🏛️ The Sovereign Desktop environment activated!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Commands:" -ForegroundColor White
    Write-Host "    python main.py          - Start in text mode" -ForegroundColor Gray
    Write-Host "    python main.py --voice  - Start in voice mode" -ForegroundColor Gray
    Write-Host "    python main.py --debug  - Start with debug logging" -ForegroundColor Gray
    Write-Host "    deactivate              - Exit the virtual environment" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  Virtual environment not found. Run setup_env.ps1 first." -ForegroundColor Red
}
"@

    Set-Content -Path $activatePath -Value $activateContent -Encoding UTF8
    Write-Success "Created activate.ps1 convenience script"
}

# ============================================================================
# Main Script
# ============================================================================

function Main {
    Write-Banner
    
    $startTime = Get-Date
    
    try {
        # Step 1: Check Python
        $pythonCmd = Test-PythonInstallation
        
        # Step 2: Create virtual environment
        $venvPath = New-VirtualEnvironment -PythonCmd $pythonCmd
        
        # Step 3: Check Ollama
        $ollamaInstalled = Test-OllamaInstallation
        
        if ($ollamaInstalled) {
            $ollamaRunning = Test-OllamaRunning
            
            if ($ollamaRunning) {
                # Step 4: Pull models
                $modelsSuccess = Get-OllamaModels
            } else {
                Write-Warning "Skipping model downloads - Ollama not running"
                Write-Host "  Run 'ollama serve' and then manually pull models:" -ForegroundColor Gray
                foreach ($model in $OLLAMA_MODELS) {
                    Write-Host "    ollama pull $($model.Name)" -ForegroundColor Cyan
                }
            }
        } else {
            Write-Warning "Skipping model downloads - Ollama not installed"
        }
        
        # Step 5: Install Python dependencies
        Install-PythonDependencies -VenvPath $venvPath
        
        # Step 6: Create .env template
        New-EnvTemplate
        
        # Step 7: Create activation script
        New-ActivationScript
        
        # Summary
        $duration = (Get-Date) - $startTime
        
        Write-Host ""
        Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✓ Setup completed in $($duration.TotalSeconds.ToString('0.0')) seconds!" -ForegroundColor Green
        Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Next steps:" -ForegroundColor White
        Write-Host "    1. Edit .env to configure your environment" -ForegroundColor Gray
        Write-Host "    2. Run: .\activate.ps1" -ForegroundColor Cyan
        Write-Host "    3. Run: python main.py" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Or activate manually:" -ForegroundColor White
        Write-Host "    .\$VENV_NAME\Scripts\Activate.ps1" -ForegroundColor Cyan
        Write-Host ""
        
    } catch {
        Write-Host ""
        Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host "  ✗ Setup failed: $_" -ForegroundColor Red
        Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# Run the script
Main
