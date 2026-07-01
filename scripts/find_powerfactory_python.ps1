$roots = @(
    "$env:ProgramFiles\DIgSILENT",
    "${env:ProgramFiles(x86)}\DIgSILENT"
)

foreach ($root in $roots) {
    if (-not (Test-Path $root)) {
        continue
    }

    Get-ChildItem -Path $root -Recurse -Filter powerfactory.pyd -ErrorAction SilentlyContinue |
        ForEach-Object {
            [PSCustomObject]@{
                PowerFactoryPythonPath = $_.DirectoryName
                Module = $_.FullName
            }
        }
}
