Option Explicit

Dim fso, shell, projectDir, pythonw, appScript, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe")
appScript = fso.BuildPath(projectDir, "hwp-auto-docfit.py")

If Not fso.FileExists(pythonw) Then
    MsgBox "앱 실행 환경을 찾을 수 없습니다." & vbCrLf & _
           "먼저 개발 환경을 설치하거나 배포용 HWP_AutoDocFit.exe를 실행해 주세요.", _
           vbExclamation, "한글문서 후처리 도구"
    WScript.Quit 1
End If

If Not fso.FileExists(appScript) Then
    MsgBox "앱 파일을 찾을 수 없습니다." & vbCrLf & appScript, _
           vbCritical, "한글문서 후처리 도구"
    WScript.Quit 1
End If

shell.CurrentDirectory = projectDir
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & appScript & Chr(34)
shell.Run command, 0, False
