git add .
git commit -m "Update"
git push

ssh pi@192.168.4.203 "cd ~/TradeNepse_Bulk_Live && find . -type d -name '__pycache__' -exec rm -rf {} + && git pull && sudo systemctl restart tradenepse-dashboard"