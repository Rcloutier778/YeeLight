Dim WinScriptHost
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "C:\Users\Richard\Documents\Coding Projects\YeeLight\yeesystray.bat" & Chr(34), 0
Set WinScriptHost = Nothing