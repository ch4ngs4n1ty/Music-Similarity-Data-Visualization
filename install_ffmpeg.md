# Installing FFmpeg for Audio Conversion

FFmpeg is required to convert downloaded audio to MP3 format.

## Quick Install (Windows)

### Option 1: Using winget (Recommended)
```powershell
winget install ffmpeg
```

### Option 2: Using Chocolatey
```powershell
choco install ffmpeg
```

### Option 3: Manual Installation
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract the zip file
3. Add the `bin` folder to your system PATH:
   - Open System Properties → Environment Variables
   - Edit "Path" variable
   - Add the path to ffmpeg's `bin` folder (e.g., `C:\ffmpeg\bin`)
4. Restart your terminal/IDE

### Verify Installation
```powershell
ffmpeg -version
```

If you see version info, it's installed correctly!

## Note
If FFmpeg is not installed, the script will still download audio but in the original format (m4a/webm) instead of MP3.

