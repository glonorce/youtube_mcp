# PYPI paketleme

Repo kökünde (`C:\Users\göksel\uygulamalarım\youtube_mcp`) şunları yap:

## 1) (Opsiyonel ama önerilir) dist'i temizle

Karışıklığı tamamen bitirmek için:

```powershell
Remove-Item -Recurse -Force dist
```

## 2) Token ile upload

```powershell
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-...SCOPED_TOKEN..."

.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe -m twine upload dist\*

Remove-Item Env:TWINE_PASSWORD
Remove-Item Env:TWINE_USERNAME
```

## 3) Gerekli araçları kur

```powershell
python -m pip install -U build twine pytest pytest-asyncio
```

## 4) Hızlı doğrulama

```powershell
python -c "import youtube_mcp, youtube_mcp.server; print(youtube_mcp.__file__); print(list(youtube_mcp.server.mcp._tool_manager._tools.keys()))"
```

---

# Venv karışırsa / timeout gibi sorunlar olursa

Repo kökünde (`C:\Users\göksel\uygulamalarım\youtube_mcp`) şunları yap:

```powershell
# 1) venv'i kapat (aktifse)
deactivate

# 2) bozuk venv'i sil
Remove-Item -Recurse -Force .venv

# 3) yeniden oluştur
C:\Python313\python.exe -m venv .venv

# 4) aktif et
.\.venv\Scripts\activate

# 5) pip ve projeyi kur
python -m pip install -U pip
python -m pip install -e .
```
