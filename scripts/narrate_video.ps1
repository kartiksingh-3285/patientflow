param(
    [Parameter(Mandatory = $true)][string]$NarrationFile,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$chapters = Get-Content -Raw -Encoding UTF8 -LiteralPath $NarrationFile | ConvertFrom-Json
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speaker.SelectVoice('Microsoft Zira Desktop')
    $speaker.Rate = 2
    $speaker.Volume = 100
    for ($index = 0; $index -lt $chapters.Count; $index++) {
        $path = Join-Path $OutputDirectory ('speech-{0:D2}.wav' -f $index)
        $speaker.SetOutputToWaveFile($path)
        $speaker.Speak([string]$chapters[$index].narration)
        $speaker.SetOutputToNull()
    }
}
finally {
    $speaker.Dispose()
}
