Option Explicit

Dim fso, shell, projectDir, pythonw, appScript, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe")
appScript = fso.BuildPath(projectDir, "hwp-auto-docfit.py")

If fso.FileExists(pythonw) Then
    ' Use project virtual environment
ElseIf fso.FileExists("C:\Users\haiju\AppData\Local\Programs\Python\Python314\pythonw.exe") Then
    pythonw = "C:\Users\haiju\AppData\Local\Programs\Python\Python314\pythonw.exe"
Else
    pythonw = "pythonw.exe"
End If

If Not fso.FileExists(appScript) Then
    MsgBox "App file not found: " & appScript, vbCritical, "HWP Auto DocFit"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectDir
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & appScript & Chr(34)
shell.Run command, 1, False
