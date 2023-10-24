# Konfiguration crontab

## Ausführen von finalize_next_week jeden Sonntag 4:11 Uhr

Eintragen der folgenden Zeile mit *crontab -e*

`11 4 * * 0 wget http://localhost:4000/finalize_next_week`
