# Chay Newman collection tu dong
Write-Host "==> Bat dau kiem thu API bang Newman..." -ForegroundColor Cyan

newman run books-api.postman_collection.json `
  -e local.postman_environment.json `
  -r cli,junit `
  --reporter-junit-export reports/junit.xml

Write-Host "==> Hoan thanh kiem thu! Ket qua da duoc xuat ra reports/junit.xml" -ForegroundColor Green
