Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope LocalMachine

cd "C:\Program Files\Trend Micro\Deep Security Manager"
cmd.exe /c "dsm_c.exe -action changesetting -name settings.configuration.webserviceAPIEnabled -value true"
cmd.exe /c "dsm_c.exe -action changesetting -name settings.configuration.agentInitiatedActivation -value 1"
cmd.exe /c "dsm_c.exe -action changesetting -name settings.security.activeSessionsAllowed -value -1"
cmd.exe /c "dsm_c.exe -action changesetting -name settings.configuration.dsruAutoApplyNewDSRUs -value false"
cmd.exe /c "dsm_c.exe -action changesetting -name settings.security.activeSessionExceededAction -value 2"