' Author: Luke Chikkala
' Modified by Jeremy Dufeux - Carrot Industries

WScript.Sleep 1000

Set LC			= CreateObject("WScript.Shell")
Set LC_fstream	= CreateObject("Scripting.FileSystemObject")
LC_HomePath		= LC.ExpandEnvironmentStrings("%HOMEPATH%")

version				 = InputBox("Enter first 3 digits of gMA3 software version", "Used Ma version", "2.2.5")
IPAddress			 = InputBox("Enter Station IP", "IP address", "127.0.0.1")
gMA3LogsLocation	 = InputBox("Enter Ma3 Logs directory location", "Folder", "D:\Desktop\gMA3Logs")

If LC_fstream.FolderExists(gMA3LogsLocation) Then
	Set CheckgMA3Directory = LC_fstream.GetFolder(gMA3LogsLocation)
Else

	Set CheckgMA3Directory = LC_fstream.CreateFolder(gMA3LogsLocation)
	WScript.Echo "gMA3 SysMon Logger created ""gMA3Logs"" directory on Desktop."
End If

' Temporary file stores the ping status.
TempFileName	 			= "LC_IP_Status"

gMA3LogsLocation_TempFile	= gMA3LogsLocation & "\" & TempFileName
Const OpenAsASCII	 = 0
Const FailIfNotExist = 0
Const ForReading	 = 1

' Pings the station to check if connection to the device is possible.
LC.run "%comspec% /c ping.exe -n 2 -w 500 " & IPAddress & ">" & gMA3LogsLocation_TempFile, 0 , True
Set ReadFile		 = LC_fstream.OpenTextFile(gMA3LogsLocation_TempFile, ForReading, FailIfNotExist, OpenAsASCII)

' If the ping status reads "TTL=" in it's contents, then the script starts to log.
If InStr(ReadFile.ReadAll, "TTL=") Then
	Today		= Replace(date(),"/", "_")
	Hours		= Hour(time)
	Minutes		= Minute(time)
	Seconds		= Second(time)
	TimeNow		= Hours & "_" & Minutes & "_" & Seconds
	TimeStamp	= Today & "_" & TimeNow
	LC_gMA3_cmd		= " sysmon " & IPAddress & " > " & gMA3LogsLocation & "\SysMon_" & TimeStamp & ".txt "
	LC_Final_cmd			= "cmd.exe @cmd /k ""C:\Program Files\MALightingTechnology\gma3_" & version & "\bin\app_terminal.exe""" & LC_gMA3_cmd & ""

	LC.run LC_Final_cmd
Else
	' vbCrLf adds new line.
	CurrentStatus = MsgBox("Unable to ping " & IPAddress & vbCrLf & "Check Firewall or Contact TechSupport", 48, "Ping Status")
End If

ReadFile.Close
LC_fstream.DeleteFile(gMA3LogsLocation_TempFile)
