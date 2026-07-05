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
os.environ["DOTNET_EnableWriteXorExecute"] = "0"  # إصلاح segfault معروف ببيئات gVisor (Colab بالضبط)
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

    # جلب رابط التحميل الصحيح فعلياً من GitHub API — لا تخمين لاسم الملف/التاريخ
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
    GHIDRA_SCRIPT = '''
import time
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
decompiler = DecompInterface()
decompiler.openProgram(currentProgram)
monitor = ConsoleTaskMonitor()
out = open("/content/libil2cpp_decompiled.c", "w")
func = getFirstFunction()
count = 0
start_time = time.time()
while func is not None:
    res = decompiler.decompileFunction(func, 60, monitor)
    if res.decompileCompleted():
        out.write("// ===== " + func.getName() + " =====\\n" + res.getDecompiledFunction().getC() + "\\n\\n")
        out.flush()
    count += 1
    if count % 500 == 0:
        elapsed = time.time() - start_time
        print("فُكت " + str(count) + " دالة خلال " + str(int(elapsed)) + " ثانية (" + str(round(count/elapsed, 1)) + " دالة/ثانية)")
    func = getFunctionAfter(func)
out.write("// إجمالي: " + str(count) + " دالة\\n")
out.close()
print("انتهى فعلياً: " + str(count) + " دالة إجمالي")
'''
    Path("/content/decompile_all.py").write_text(GHIDRA_SCRIPT, encoding="utf-8")
    so_path = LOCAL_INPUT / "ultimatebattlelands_il2cpp_mygame" / "libil2cpp.so"
    ghidra_bin = list(Path("/content/ghidra_install").glob("*/support/analyzeHeadless"))
    if so_path.exists() and ghidra_bin:
        subprocess.run([str(ghidra_bin[0]), "/content/ghidra_project", "libil2cpp_project", "-import", str(so_path), "-scriptPath", "/content", "-postScript", "decompile_all.py"], check=False)
        print("✓ حاول Ghidra يفك libil2cpp.so — تحقق من /content/libil2cpp_decompiled.c")
    else:
        print("⚠️ Ghidra أو libil2cpp.so غير جاهزين — تخطي (نكمل الباقي بلا توقف)")
except Exception as e:
    print(f"⚠️ Ghidra فشلت ({e}) — نكمل بلا توقف")

# ============================================================
# المرحلة 4: تجميع الملفات (Staging) للبايبلاين
# ============================================================
STAGING_DIR = Path("/content/STAGING_WORKSPACE")
if STAGING_DIR.exists(): shutil.rmtree(STAGING_DIR)
STAGING_DIR.mkdir()

shutil.copytree(LOCAL_INPUT, STAGING_DIR / "Raw_Original", dirs_exist_ok=True)
if ASSETRIPPER_OUTPUT.exists():
    shutil.copytree(ASSETRIPPER_OUTPUT, STAGING_DIR / "Ripper_Assets", dirs_exist_ok=True)
if Path("/content/libil2cpp_decompiled.c").exists():
    shutil.copy("/content/libil2cpp_decompiled.c", STAGING_DIR / "libil2cpp_decompiled.c")


# ============================================================
# المرحلة 5: البايبلاين الأصلي الكامل (بدون أي تبسيط)
# ============================================================
print("\n" + "=" * 60 + "\nالمرحلة 5: البايبلاين الشامل (الأصلي)\n" + "=" * 60)

CLASS_ID_NAMES = {
    "1": "GameObject", "4": "Transform", "114": "MonoBehaviour",
    "33": "MeshFilter", "23": "MeshRenderer", "65": "BoxCollider",
    "54": "Rigidbody", "137": "SkinnedMeshRenderer", "95": "Animator",
    "82": "AudioSource", "108": "Light", "20": "Camera",
}
ANCHOR_RE = re.compile(r'^--- !u!(\d+) &(\d+)', re.MULTILINE)
STRIP_TAG_RE = re.compile(r'^--- !u!(\d+) (&\d+)', re.MULTILINE)
IGNORED_FIELDS = {"m_GameObject", "m_Script", "m_ObjectHideFlags", "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset"}

IRRELEVANT_SDK_PATTERNS = [
    "facebook", "appsflyer", "firebase", "purchasing", "stores.dll",
    "advertisements", "unityanalyticsmodule", "unitywebrequest",
    "testrunner", "nunit", "winrt", "sirenix", "applecore", "applemacos",
    "apple.dll", "facebookstore",
]
CORE_DLL_PATTERNS = ["assembly-csharp", "photon", "quantum", "il2cppdummydll"]

MEDIA_EXTS = {".glb", ".gltf", ".fbx", ".obj", ".mtl", ".png", ".tga", ".jpg", ".jpeg", ".dds", ".ogg", ".wav", ".mp3", ".mat", ".anim", ".controller", ".ttf", ".otf"}
TEXT_LOGIC_EXTS = {".cs", ".json", ".yaml", ".yml", ".asset", ".prefab", ".txt", ".xml", ".ini", ".cfg", ".c"}
CSV_EXTS = {".csv"}
USABLE_MESH_EXTS = {".glb", ".gltf", ".fbx", ".obj"}
DEAD_MESH_MARKER = ".mesh"

NETWORK_CONTENT_KEYWORDS = ["photon", "quantum", "exitgames", "enet", "photonnetwork", "rpc", "networkrunner", "irpcallback", "iphotonpeerlistener"]
NETWORK_PATH_KEYWORDS = ["photon", "quantum", "exitgames", "network", "multiplayer"]

def parse_unity_yaml(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    anchors = ANCHOR_RE.findall(text)
    lines = []
    for l in text.splitlines():
        if l.startswith("%YAML") or l.startswith("%TAG"): continue
        lines.append(STRIP_TAG_RE.sub(r"--- \2", l))
    clean = "\n".join(lines)
    try: docs = list(yaml.safe_load_all(clean))
    except Exception as e: return None, str(e)
    objects = {}
    for i, doc in enumerate(docs):
        if doc is None or i >= len(anchors): continue
        class_id, file_id = anchors[i]
        objects[file_id] = {"class_id": class_id, "class_name": CLASS_ID_NAMES.get(class_id, f"Unknown_{class_id}"), "data": doc}
    return objects, None

def build_clean_structure(objects: dict) -> dict:
    result = {"game_objects": []}
    for file_id, obj in objects.items():
        if obj["class_name"] != "GameObject": continue
        go_data = obj["data"].get("GameObject", {})
        name = go_data.get("m_Name", "Unnamed")
        components_resolved = []
        for comp_ref in go_data.get("m_Component", []):
            comp_file_id = str(comp_ref.get("component", {}).get("fileID", ""))
            comp_obj = objects.get(comp_file_id)
            if not comp_obj: continue
            comp_class = comp_obj["class_name"]
            comp_data = comp_obj["data"].get(comp_class, {})
            useful_fields = {k: v for k, v in comp_data.items() if k not in IGNORED_FIELDS}
            components_resolved.append({"type": comp_class, "fields": useful_fields})
        result["game_objects"].append({"name": name, "components": components_resolved})
    return result

def decompose_all_prefabs_assets(work_dir: Path, output_dir: Path, log: dict):
    out_dir = output_dir / "01_Logic_Configs" / "decomposed_prefabs_assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [p for p in work_dir.rglob("*") if p.suffix.lower() in {".prefab", ".asset"}]
    total = len(targets)
    print(f"تفكيك هرمي لـ {total} ملف .prefab/.asset...")
    decomposed = 0
    for idx, f in enumerate(targets):
        if idx % 500 == 0 and idx > 0:
            print(f"  ... {idx}/{total} ملف مُعالَج")
        objects, err = parse_unity_yaml(f)
        if err:
            log["failed"].append(f"{f} — فشل تفكيك YAML: {err}")
            continue
        clean = build_clean_structure(objects)
        if not clean["game_objects"]: continue
        out_path = out_dir / f"{f.stem}.json"
        out_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        decomposed += 1
    log["prefabs_decomposed"] = decomposed

def extract_all_config_values(work_dir: Path, output_dir: Path, log: dict):
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$")
    all_values = {}
    asset_files = [p for p in work_dir.rglob("*") if p.suffix.lower() in {".asset", ".prefab"}]
    total = len(asset_files)
    print(f"استخراج القيم من {total} ملف .asset/.prefab...")
    for idx, f in enumerate(asset_files):
        if idx % 500 == 0 and idx > 0:
            print(f"  ... {idx}/{total} ملف مُعالَج")
        try:
            found = {}
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    m = pattern.match(line)
                    if not m: continue
                    key, raw_val = m.group(1), m.group(2)
                    if re.fullmatch(r"-?\d+\.?\d*", raw_val):
                        val = float(raw_val) if "." in raw_val else int(raw_val)
                    else:
                        val = raw_val.strip('"')
                    found[key] = val
            if found: all_values[f.name] = found
        except Exception as e:
            log["failed"].append(f"{f} — فشل قراءة القيم: {e}")
    out_path = output_dir / "01_Logic_Configs" / "all_extracted_config_values.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_values, ensure_ascii=False, indent=2), encoding="utf-8")
    log["config_files_extracted"] = len(all_values)

def analyze_il2cpp_dump(work_dir: Path, output_dir: Path, log: dict):
    dump_cs_files = list(work_dir.rglob("dump.cs"))
    script_json_files = list(work_dir.rglob("script.json"))
    if not dump_cs_files and not script_json_files: return
    il2cpp_out_dir = output_dir / "07_IL2CPP_Dump_Analysis"
    il2cpp_out_dir.mkdir(parents=True, exist_ok=True)
    
    if script_json_files:
        try:
            with open(script_json_files[0], "r", encoding="utf-8") as f: script_data = json.load(f)
            methods_map = {m.get("Name", "Unknown"): hex(m.get("Address", 0)) for m in script_data.get("ScriptMethod", []) if m.get("Address", 0) > 0}
            (il2cpp_out_dir / "il2cpp_methods_offsets.json").write_text(json.dumps(methods_map, indent=2, ensure_ascii=False), encoding="utf-8")
            log["il2cpp_methods"] = len(methods_map)
        except Exception as e: log["failed"].append(f"script.json: {e}")

    if dump_cs_files:
        try:
            classes_map = defaultdict(list)
            class_re = re.compile(r"public class ([a-zA-Z0-9_]+)")
            field_re = re.compile(r"// Offset: (0x[0-9A-Fa-f]+)\s+public\s+([a-zA-Z0-9_\[\]]+)\s+([a-zA-Z0-9_]+);")
            current_class = None
            with open(dump_cs_files[0], "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    c_match = class_re.search(line)
                    if c_match:
                        current_class = c_match.group(1)
                        continue
                    if current_class:
                        f_match = field_re.search(line)
                        if f_match: classes_map[current_class].append({"name": f_match.group(3), "type": f_match.group(2), "offset": f_match.group(1)})
            (il2cpp_out_dir / "il2cpp_classes_fields.json").write_text(json.dumps(classes_map, indent=2, ensure_ascii=False), encoding="utf-8")
            log["il2cpp_classes"] = len(classes_map)
        except Exception as e: log["failed"].append(f"dump.cs: {e}")

def try_decompile_core_dlls(dll_files: list, output_dir: Path, log: dict):
    decompiled_dir = output_dir / "04_Network_Backend" / "decompiled_structure"
    decompiled_dir.mkdir(parents=True, exist_ok=True)
    total_classes = 0
    for dll_path in dll_files:
        try:
            pe = dnfile.dnPE(str(dll_path))
            out_lines = [f"// بنية مستخرجة من {dll_path.name} عبر dnfile", ""]
            type_table = pe.net.mdtables.TypeDef
            for row in type_table.rows:
                out_lines.append(f"class {row.TypeNamespace.value}.{row.TypeName.value} {{")
                total_classes += 1
                for field in getattr(row, "FieldList", []) or []: out_lines.append(f"    // field: {field.Name.value}")
                for method in getattr(row, "MethodList", []) or []: out_lines.append(f"    // method: {method.Name.value}()")
                out_lines.append("}\n")
            out_path = decompiled_dir / f"{dll_path.stem}_structure.cs"
            out_path.write_text("\n".join(out_lines), encoding="utf-8")
        except Exception as e: log["failed"].append(f"{dll_path} — فشل فك التشفير: {e}")
    log["classes_decompiled"] = total_classes

def split_large_text_file(path: Path, max_mb: int = 50):
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb <= max_mb: return [path]
    parts = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        header = f.readline() if path.suffix.lower() == ".csv" else None
        part_num, current_size, current_lines = 1, 0, ([header] if header else [])
        for line in f:
            current_lines.append(line)
            current_size += len(line.encode("utf-8"))
            if current_size >= max_mb * 1024 * 1024:
                part_path = path.parent / f"{path.stem}_part{part_num}{path.suffix}"
                part_path.write_text("".join(current_lines), encoding="utf-8")
                parts.append(part_path)
                part_num += 1
                current_size = 0
                current_lines = [header] if header else []
        if current_lines and (len(current_lines) > 1 or not header):
            part_path = path.parent / f"{path.stem}_part{part_num}{path.suffix}"
            part_path.write_text("".join(current_lines), encoding="utf-8")
            parts.append(part_path)
    path.unlink()
    return parts

def run_pipeline(work_dir: Path, output_dir: Path):
    log = {"extracted": [], "failed": []}
    
    # 1. Archives
    pass_num = 0
    while True:
        pass_num += 1
        archives = list(work_dir.rglob("*.zip")) + list(work_dir.rglob("*.7z"))
        if not archives: break
        print(f"[الجولة {pass_num}] فك {len(archives)} أرشيف...")
        for i, archive in enumerate(archives):
            if i % 20 == 0 and i > 0:
                print(f"  ... {i}/{len(archives)} أرشيف")
            target = archive.parent / (archive.stem + "_extracted")
            target.mkdir(parents=True, exist_ok=True)
            try:
                if archive.suffix.lower() == ".zip":
                    with zipfile.ZipFile(archive, "r") as zf: zf.extractall(target)
                else:
                    with py7zr.SevenZipFile(archive, "r") as zf: zf.extractall(target)
                log["extracted"].append(str(archive))
                archive.unlink()
            except Exception as e: log["failed"].append(f"{archive} - {e}")

    # 2. Meshes Verify
    usable = [p for p in work_dir.rglob("*") if p.suffix.lower() in USABLE_MESH_EXTS]
    broken = [p for p in work_dir.rglob("*") if p.suffix.lower() == DEAD_MESH_MARKER]
    log["meshes_usable"] = len(usable)
    log["meshes_broken"] = len(broken)

    # 3. Extracts & Decompose
    print("استخراج القيم من ملفات .asset/.prefab...")
    extract_all_config_values(work_dir, output_dir, log)
    print("تفكيك هرمي لملفات .prefab/.asset...")
    decompose_all_prefabs_assets(work_dir, output_dir, log)
    print("تحليل dump.cs / script.json (IL2CPP)...")
    analyze_il2cpp_dump(work_dir, output_dir, log)
    print("✓ خلصت مرحلة الاستخراج، بدء التصنيف...")

    # 4. Organize
    counts, core_dlls_found = defaultdict(int), []
    for c in ["01_Logic_Configs", "02_Assets_Media", "03_CSV_Data", "04_Network_Backend", "05_Unclassified", "06_DLLs_Raw_Original"]:
        (output_dir / c).mkdir(parents=True, exist_ok=True)
        
    all_files = [p for p in work_dir.rglob("*") if p.is_file()]
    total_files = len(all_files)
    print(f"بدء تصنيف {total_files} ملف...")

    for idx, f in enumerate(all_files):
        if idx % 200 == 0 and idx > 0:
            print(f"  ... تمت معالجة {idx}/{total_files} ملف")
        ext, path_lower = f.suffix.lower(), str(f).lower()
        if any(p in path_lower for p in IRRELEVANT_SDK_PATTERNS):
            counts["00_Excluded"] += 1
            f.unlink()
            continue
        if ext == ".dll" and any(p in path_lower for p in CORE_DLL_PATTERNS):
            core_dlls_found.append(f)
            shutil.copy(str(f), str(output_dir / "06_DLLs_Raw_Original" / f.name))
            counts["06_DLLs_Raw"] += 1
            continue
        
        is_net = any(kw in path_lower for kw in NETWORK_PATH_KEYWORDS)
        if not is_net and ext in {".cs", ".c"}:
            try: is_net = any(kw in f.read_text(encoding="utf-8", errors="ignore").lower() for kw in NETWORK_CONTENT_KEYWORDS)
            except: pass
            
        if is_net: key = "04_Network_Backend"
        elif ext in TEXT_LOGIC_EXTS: key = "01_Logic_Configs"
        elif ext in MEDIA_EXTS: key = "02_Assets_Media"
        elif ext in CSV_EXTS: key = "03_CSV_Data"
        elif ext == DEAD_MESH_MARKER: continue
        else: key = "05_Unclassified"
        
        dest = output_dir / key / f.name
        i = 1
        while dest.exists():
            dest = output_dir / key / f"{f.stem}_{i}{f.suffix}"
            i += 1
        try:
            shutil.move(str(f), str(dest))
            counts[key] += 1
        except Exception as e: log["failed"].append(f"{f} - {e}")

    # 5. Core DLL Decompile
    try_decompile_core_dlls(core_dlls_found, output_dir, log)

    # 6. Split Large Files
    split_count = 0
    for big_dir in [output_dir / "03_CSV_Data", output_dir / "01_Logic_Configs"]:
        if not big_dir.exists(): continue
        for f in list(big_dir.rglob("*")):
            if f.is_file() and f.suffix.lower() in {".csv", ".txt", ".json", ".c"}:
                parts = split_large_text_file(f)
                split_count += len(parts) - 1

    # Finalize
    manifest = {
        "counts": dict(counts),
        "archives_extracted": len(log["extracted"]),
        "meshes_usable": log.get("meshes_usable", 0),
        "meshes_broken": log.get("meshes_broken", 0),
        "config_files_extracted": log.get("config_files_extracted", 0),
        "classes_decompiled": log.get("classes_decompiled", 0),
        "files_split": split_count,
        "failed_items": len(log["failed"]),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))

FINAL_OUTPUT = Path("/content/drive/MyDrive/ORGANIZED_MASTER_PROJECT")
if FINAL_OUTPUT.exists(): shutil.rmtree(FINAL_OUTPUT)
FINAL_OUTPUT.mkdir(parents=True)
run_pipeline(STAGING_DIR, FINAL_OUTPUT)

print("\n✓ اكتمل الاستخراج والتنظيم بالكامل!")
