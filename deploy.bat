@echo off

git add .
git commit -m "Auto deploy"
git push

ssh pi@192.168.4.203 "cd ~/TradeNepse_Bulk_Live && git pull && sudo systemctl restart tradenepse-dashboard"

pause