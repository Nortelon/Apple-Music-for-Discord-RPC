"""
Apple Music Discord RPC - Kaldirma
Calisan processi durdurur ve baslangictan kaldirir.
"""
import os
import subprocess
import winreg

APP_NAME = "AppleMusicDiscordRPC"
PID_FILE = os.path.join(os.environ.get("TEMP", ""), "apple_music_rpc.pid")

def uninstall():
    # Calisan processi durdur
    stopped = False
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = f.read().strip()
            result = subprocess.run(["taskkill", "/pid", pid, "/f"], capture_output=True)
            if result.returncode == 0:
                stopped = True
            os.remove(PID_FILE)
        except Exception:
            pass

    if stopped:
        print("[OK] Process durduruldu.")
    else:
        print("[--] Calisir process bulunamadi.")

    # Registry'den kaldir
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print("[OK] Baslangictan kaldirildi.")
    except FileNotFoundError:
        print("[--] Baslangic kaydı bulunamadi.")

    # Apple Music watcher PS process'ini de kapat
    subprocess.run(
        ["taskkill", "/f", "/fi", "IMAGENAME eq powershell.exe",
         "/fi", "WINDOWTITLE eq apple_music*"],
        capture_output=True,
    )

    print("\nUygulama tamamen kaldirildi.")

if __name__ == "__main__":
    uninstall()
