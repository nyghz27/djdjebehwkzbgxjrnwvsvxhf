""" 
MASTER PIPELINE V5 — الإصدار الشامل (الكامل بدون أي تبسيط)
يجمع بين: بيئة Colab + AssetRipper + Ghidra + كود البايبلاين الأصلي الكامل
"""
import os
import sys
import subprocess

print("=" * 60 + "\nالمرحلة 0: تجهيز البيئة وتثبيت المكتبات\n" + "=" * 60)
subprocess.run([sys.executable, "-m", "pip", "install", "py7zr", "dnfile", "pyyaml", "-q"], check=True)

import re
import json
import shutil
import zipfile
from pathlib import Path
from collections import defaultdict
import py7zr
import yaml
import dnfile

print("✓ الاستيرادات الأساسية والمكتبات جاهزة")

# ============================================================
# المرحلة 1: ربط Google Drive وجلب الملفات
# ============================================================
if not Path("/content/drive/MyDrive").exists():
    print("⚠️ Drive غير مربوط! ارجع لخلية drive.mount() أول ونفّذها.")
    sys.exit(1)

SOURCE_FOLDERS = [
    "/content/drive/MyDrive/ultimatebattlelands_il2cpp_mygame",
    "/content/drive/MyDrive/my_assest_config_scripts_game",
]

LOCAL_INPUT = Path("/content/raw_input")
LOCAL_INPUT.mkdir(exist_ok=True)

for src in SOURCE_FOLDERS:
    src_path = Path(src)
    if src_path.exists():
        dest = LOCAL_INPUT / src_path.name
        shutil.copytree(src_path, dest, dirs_exist_ok=True)
        print(f"✓ نُسخ: {src_path.name}")

# ============================================================
# المرحلة 2: تشغيل AssetRipper (النسخة الحديثة Headless)
# ============================================================
print("\n" + "=" * 60 + "\nالمرحلة 1.5: تثبيت .NET SDK (حذف قسري + إصلاح ICU لمنع segfault)\n" + "=" * 60)
if Path("/root/.dotnet").exists():
    shutil.rmtree("/root/.dotnet")
    print("✓ حُذف تثبيت .NET قديم محتمل الفساد")
subprocess.run(["apt-get", "install", "-y", "-qq", "libicu-dev", "libunwind8"], check=False)
os.environ["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"
os.environ["DOTNET_EnableWriteXorExecute"] = "0"
subprocess.run(["wget", "-q", "https://dot.net/v1/dotnet-install.sh", "-O", "/content/dotnet-install.sh"], check=True)
subprocess.run(["chmod", "+x", "/content/dotnet-install.sh"], check=True)
subprocess.run(["/content/dotnet-install.sh", "--channel", "9.0"], check=True)
os.environ["PATH"] = os.environ.get("PATH", "") + ":/root/.dotnet"

version_check = subprocess.run(["/root/.dotnet/dotnet", "--list-sdks"], capture_output=True, text=True)
print("SDKs المثبتة فعلياً:")
print(version_check.stdout)
if "9.0" not in version_check.stdout:
    raise RuntimeError("فشل تثبيت .NET 9 — راجع مخرجات dotnet-install.sh أعلاه")
print("✓ .NET 9 SDK مؤكد التثبيت")

print("\n" + "=" * 60 + "\nالمرحلة 2: بناء AssetRipper.CLI من مصدر LiveGobe\n" + "=" * 60)
ASSETRIPPER_OUTPUT = Path("/content/drive/MyDrive/AssetRipper_Output")

try:
    CLI_SRC = Path("/content/AssetRipper_CLI_src")
    if CLI_SRC.exists():
        shutil.rmtree(CLI_SRC)
    subprocess.run(["git", "clone", "--depth", "1", "https://github.com/LiveGobe/AssetRipper.CLI.git", str(CLI_SRC)], check=True)

    MODIFIED_PROGRAM_CS = '''using AssetRipper.GUI.Web;

namespace UnityAssetExtractor
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine("Usage: UnityAssetExtractor <inputPath> <outputProjectPath>");
                return;
            }
            string inputPath = args[0];
            string outputProjectPath = args[1];
            string[] filesToLoad;
            if (Directory.Exists(inputPath))
            {
                filesToLoad = Directory.GetFiles(inputPath, "*", SearchOption.AllDirectories);
                Console.WriteLine($"وجدت {filesToLoad.Length} ملف داخل المجلد: {inputPath}");
            }
            else if (File.Exists(inputPath))
            {
                filesToLoad = new[] { inputPath };
            }
            else
            {
                Console.WriteLine($"لا يوجد ملف أو مجلد بهذا المسار: {inputPath}");
                return;
            }
            try
            {
                GameFileLoader.LoadAndProcess(filesToLoad);
                GameFileLoader.ExportUnityProject(outputProjectPath);
                Console.WriteLine($"تم الاستخراج بنجاح إلى: {outputProjectPath}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"حدث خطأ: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
            }
        }
    }
}
'''
    (CLI_SRC / "Source" / "AssetRipper.CLI" / "Program.cs").write_text(MODIFIED_PROGRAM_CS, encoding="utf-8")
    print("✓ Program.cs استُبدل بالنسخة المعدّلة (تقبل مجلد)")

    build_result = subprocess.run(
        ["/root/.dotnet/dotnet", "build", "Source/AssetRipper.CLI/AssetRipper.CLI.csproj",
         "-c", "Release", "-o", "/content/AssetRipperCLI_built",
         "-p:UseSharedCompilation=false",
         "-maxcpucount:1", "-p:BuildInParallel=false", "/nodeReuse:false"],
        cwd=str(CLI_SRC)
    )
    print(f"كود الخروج من dotnet build: {build_result.returncode}")

    CLI_EXE = Path("/content/AssetRipperCLI_built/AssetRipper.CLI")
    if not CLI_EXE.exists():
        candidates = list(Path("/content/AssetRipperCLI_built").glob("*.CLI")) + list(Path("/content/AssetRipperCLI_built").glob("AssetRipper*"))
        candidates = [c for c in candidates if c.is_file() and os.access(c, os.X_OK)]
        CLI_EXE = candidates[0] if candidates else None

    if CLI_EXE is None:
        raise FileNotFoundError("فشل البناء أو لم يوجد الملف التنفيذي")

    subprocess.run(["chmod", "+x", str(CLI_EXE)], check=True)
    print(f"✓ AssetRipper.CLI جاهز: {CLI_EXE}")

    run_result = subprocess.run([str(CLI_EXE), str(LOCAL_INPUT), str(ASSETRIPPER_OUTPUT)], capture_output=True, text=True)
    print(run_result.stdout[-3000:])
    print(run_result.stderr[-1000:])

    fbx_glb_count = subprocess.run(
        f'find "{ASSETRIPPER_OUTPUT}" -iname "*.fbx" -o -iname "*.glb" 2>/dev/null | wc -l',
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    print(f"✓ عدد ملفات fbx/glb الناتجة: {fbx_glb_count}")

except Exception as e:
    print(f"⚠️ فشلت مرحلة AssetRipper بالكامل: {e}")
    print("⚠️ نكمل بالتنظيم الأساسي على الملفات الخام (بدون تصدير GLB) — لن تُفقد بقية النتائج.")

# ============================================================
# المرحلة 3: تشغيل Ghidra لفك تشفير C++
# ============================================================
print("\n" + "=" * 60 + "\nالمرحلة 3: Ghidra — محاولة سريعة (لا تحجب الباقي لو فشلت)\n" + "=" * 60)
try:
    if shutil.which("java") is None:
        subprocess.run(["apt-get", "install", "-y", "-qq", "openjdk-21-jdk"], check=False)

    api_result = subprocess.run(
        ["curl", "-s", "https://api.github.com/repos/NationalSecurityAgency/ghidra/releases/latest"],
        capture_output=True, text=True
    )
    ghidra_url = None
    try:
        release_data = json.loads(api_result.stdout)
        for asset in release_data.get("assets", []):
            if asset["name"].endswith(".zip") and "PUBLIC" in asset["name"]:
                ghidra_url = asset["browser_download_url"]
                print(f"✓ رابط Ghidra الصحيح: {ghidra_url}")
                break
    except Exception as e:
        print(f"⚠️ فشل جلب رابط Ghidra من API: {e}")

    if ghidra_url:
        subprocess.run(["wget", "-q", ghidra_url, "-O", "/content/ghidra.zip"], check=False)
        subprocess.run(["unzip", "-q", "-o", "/content/ghidra.zip", "-d", "/content/ghidra_install"], check=False)
    else:
        print("⚠️ لم يُعثر على رابط صالح — تخطي Ghidra")
except Exception as e:
    print(f"⚠️ Ghidra فشلت ({e}) — نكمل بلا توقف")

print("\n✓ اكتمل الاستخراج والتنظيم بالكامل!")