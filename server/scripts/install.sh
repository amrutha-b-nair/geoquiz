#!/usr/bin/env bash
# Builds geoquiz-scores and installs it as a systemd service on this machine.
# Run from anywhere inside the repo:  ./server/scripts/install.sh
# Do it by hand once first (docs/sre/week-01.md, Day 3) so you know what each step does.
set -euo pipefail

repo="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
cd "$repo/server"

echo "==> Building"
go build -o geoquiz-scores .

echo "==> Creating the 'geoquiz' system user (if needed)"
id geoquiz >/dev/null 2>&1 || sudo useradd --system --no-create-home --shell /usr/sbin/nologin geoquiz

echo "==> Installing binary, frontend and unit file"
sudo install -m 0755 geoquiz-scores /usr/local/bin/geoquiz-scores
sudo mkdir -p /opt/geoquiz
sudo rm -rf /opt/geoquiz/web
sudo cp -r "$repo/web" /opt/geoquiz/web
sudo install -m 0644 deploy/geoquiz-scores.service /etc/systemd/system/geoquiz-scores.service

echo "==> (Re)starting the service"
sudo systemctl daemon-reload
sudo systemctl enable geoquiz-scores
sudo systemctl restart geoquiz-scores
sleep 1
systemctl --no-pager status geoquiz-scores | head -12
echo
curl -fsS http://localhost:8080/api/healthz && echo
