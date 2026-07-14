' Generation Vault — 静默启动器 (无命令行窗口)
Dim shell, fso
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 切换到脚本所在目录
shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)

' 设置环境变量
env = "PYTHONPATH=" & shell.CurrentDirectory & "\site-packages;"

' 用pythonw.exe静默启动 (无窗口)
shell.Run env & "pythonw launcher.py", 0, False
