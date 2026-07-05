#!/bin/bash

# ============================================================
# Master Pipeline with rclone Integration
# سكريبت شامل لتشغيل البايبلاين مع ربط Google Drive
# ============================================================

set -e

echo "==============================================="
echo "🚀 Master Pipeline + rclone Setup"
echo "==============================================="
echo ""

# ============================================================
# Phase 0: Install rclone
# ============================================================
echo "📦 Phase 0: Installing rclone..."
if ! command -v rclone &> /dev/null; then
    curl https://rclone.org/install.sh | sudo bash
    echo "✓ rclone installed"
else
    echo "✓ rclone already installed: $(rclone version | head -n1)"
fi

# ============================================================
# Phase 1: Configure rclone (Non-interactive)
# ============================================================
echo ""
echo "⚙️ Phase 1: Configuring rclone with Google Drive..."
echo ""
echo "⚠️ Opening browser for Google authentication..."
echo "📍 This will open a web page - authorize rclone to access your Drive"
echo ""

# Create rclone config directory if it doesn't exist
mkdir -p ~/.config/rclone

# Interactive rclone config
rclone config create gdrive drive --auth-only

echo "✓ rclone configured!"

# ============================================================
# Phase 2: Test connection
# ============================================================
echo ""
echo "🔍 Phase 2: Testing rclone connection..."
if rclone ls gdrive: > /dev/null 2>&1; then
    echo "✓ Connection successful!"
    echo ""
    echo "📁 Available files in Google Drive:"
    rclone lsd gdrive: | head -20
else
    echo "⚠️ Connection test failed - checking configuration..."
    rclone config show gdrive
fi

# ============================================================
# Phase 3: Create workspace
# ============================================================
echo ""
echo "📂 Phase 3: Creating workspace..."
WORKSPACE="/tmp/master_pipeline_workspace"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"/{raw_input,output}
cd "$WORKSPACE"
echo "✓ Workspace created at: $WORKSPACE"

# ============================================================
# Phase 4: Download source files from Drive
# ============================================================
echo ""
echo "⬇️ Phase 4: Downloading source files from Google Drive..."
echo ""

# List what's available
echo "🔎 Searching for source folders..."
rclone ls gdrive: | grep -i "ultimate\|asset" | head -10

echo ""
echo "📥 Downloading files..."

# Try to download the folders mentioned in the pipeline
echo "   → Downloading ultimatebattlelands_il2cpp_mygame..."
rclone copy gdrive:ultimatebattlelands_il2cpp_mygame raw_input/ --progress 2>/dev/null || echo "   ⚠️ Folder not found (will continue)"

echo "   → Downloading my_assest_config_scripts_game..."
rclone copy gdrive:my_assest_config_scripts_game raw_input/ --progress 2>/dev/null || echo "   ⚠️ Folder not found (will continue)"

# Count downloaded files
FILE_COUNT=$(find raw_input -type f | wc -l)
echo "✓ Downloaded $FILE_COUNT files"

# ============================================================
# Phase 5: Run the master pipeline
# ============================================================
echo ""
echo "🔄 Phase 5: Running Master Pipeline..."
echo ""

# Create a modified version of the pipeline that uses local paths
cat > master_pipeline_local.py << 'PYTHON_SCRIPT'
"""
MASTER PIPELINE V5 - LOCAL VERSION (Modified for Codespace)
"""
import os
import sys
import subprocess
from pathlib import Path

print("=" * 60 + "\nPhase 0: Environment Setup\n" + "=" * 60)

# Install dependencies
subprocess.run([sys.executable, "-m", "pip", "install", "py7zr", "dnfile", "pyyaml", "-q"], check=False)

import re
import json
import shutil
import zipfile
from collections import defaultdict
import py7zr
import yaml
import dnfile

print("✓ All imports ready")

# ============================================================
# LOCAL PATHS (No Google Drive required)
# ============================================================
BASE_DIR = Path("/tmp/master_pipeline_workspace")
LOCAL_INPUT = BASE_DIR / "raw_input"
LOCAL_OUTPUT = BASE_DIR / "output"
LOCAL_OUTPUT.mkdir(exist_ok=True)

print(f"📂 Working directory: {BASE_DIR}")
print(f"📥 Input folder: {LOCAL_INPUT}")
print(f"📤 Output folder: {LOCAL_OUTPUT}")

# ============================================================
# CONFIGURATION
# ============================================================
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
]
CORE_DLL_PATTERNS = ["assembly-csharp", "photon", "quantum", "il2cppdummydll"]

MEDIA_EXTS = {".glb", ".gltf", ".fbx", ".obj", ".mtl", ".png", ".tga", ".jpg", ".jpeg", ".dds", ".ogg", ".wav", ".mp3", ".mat", ".anim", ".controller", ".ttf", ".otf"}
TEXT_LOGIC_EXTS = {".cs", ".json", ".yaml", ".yml", ".asset", ".prefab", ".txt", ".xml", ".ini", ".cfg", ".c"}
CSV_EXTS = {".csv"}
USABLE_MESH_EXTS = {".glb", ".gltf", ".fbx", ".obj"}

NETWORK_CONTENT_KEYWORDS = ["photon", "quantum", "exitgames", "enet", "photonnetwork", "rpc", "networkrunner"]
NETWORK_PATH_KEYWORDS = ["photon", "quantum", "exitgames", "network", "multiplayer"]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_unity_yaml(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        anchors = ANCHOR_RE.findall(text)
        lines = []
        for l in text.splitlines():
            if l.startswith("%YAML") or l.startswith("%TAG"): 
                continue
            lines.append(STRIP_TAG_RE.sub(r"--- \2", l))
        clean = "\n".join(lines)
        try:
            docs = list(yaml.safe_load_all(clean))
        except Exception as e:
            return None, str(e)
        objects = {}
        for i, doc in enumerate(docs):
            if doc is None or i >= len(anchors):
                continue
            class_id, file_id = anchors[i]
            objects[file_id] = {
                "class_id": class_id,
                "class_name": CLASS_ID_NAMES.get(class_id, f"Unknown_{class_id}"),
                "data": doc
            }
        return objects, None
    except Exception as e:
        return None, str(e)

def build_clean_structure(objects: dict) -> dict:
    result = {"game_objects": []}
    for file_id, obj in objects.items():
        if obj["class_name"] != "GameObject":
            continue
        go_data = obj["data"].get("GameObject", {})
        name = go_data.get("m_Name", "Unnamed")
        components_resolved = []
        for comp_ref in go_data.get("m_Component", []):
            comp_file_id = str(comp_ref.get("component", {}).get("fileID", ""))
            comp_obj = objects.get(comp_file_id)
            if not comp_obj:
                continue
            comp_class = comp_obj["class_name"]
            comp_data = comp_obj["data"].get(comp_class, {})
            useful_fields = {k: v for k, v in comp_data.items() if k not in IGNORED_FIELDS}
            components_resolved.append({"type": comp_class, "fields": useful_fields})
        result["game_objects"].append({"name": name, "components": components_resolved})
    return result

def extract_all_config_values(work_dir: Path, output_dir: Path, log: dict):
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$")
    all_values = {}
    asset_files = [p for p in work_dir.rglob("*") if p.suffix.lower() in {".asset", ".prefab"}]
    total = len(asset_files)
    
    if total == 0:
        print(f"⚠️ No .asset/.prefab files found")
        return
    
    print(f"استخراج القيم من {total} ملف...")
    for idx, f in enumerate(asset_files):
        if idx % 50 == 0 and idx > 0:
            print(f"  ... {idx}/{total} processed")
        try:
            found = {}
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    m = pattern.match(line)
                    if not m:
                        continue
                    key, raw_val = m.group(1), m.group(2)
                    if re.fullmatch(r"-?\d+\.?\d*", raw_val):
                        val = float(raw_val) if "." in raw_val else int(raw_val)
                    else:
                        val = raw_val.strip('"')
                    found[key] = val
            if found:
                all_values[f.name] = found
        except Exception as e:
            log["failed"].append(f"{f} - {e}")
    
    out_path = output_dir / "01_Logic_Configs" / "all_extracted_config_values.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_values, ensure_ascii=False, indent=2), encoding="utf-8")
    log["config_files_extracted"] = len(all_values)
    print(f"✓ Extracted {len(all_values)} config files")

def run_pipeline(work_dir: Path, output_dir: Path):
    print("\n" + "=" * 60)
    print("Phase 5: Running Master Pipeline")
    print("=" * 60 + "\n")
    
    log = {"extracted": [], "failed": []}
    
    # 1. Extract Archives
    print("📦 Step 1: Extracting archives...")
    pass_num = 0
    while True:
        pass_num += 1
        archives = list(work_dir.rglob("*.zip")) + list(work_dir.rglob("*.7z"))
        if not archives:
            break
        print(f"[Round {pass_num}] Found {len(archives)} archives")
        for i, archive in enumerate(archives):
            if i % 10 == 0 and i > 0:
                print(f"  ... {i}/{len(archives)}")
            target = archive.parent / (archive.stem + "_extracted")
            target.mkdir(parents=True, exist_ok=True)
            try:
                if archive.suffix.lower() == ".zip":
                    with zipfile.ZipFile(archive, "r") as zf:
                        zf.extractall(target)
                else:
                    with py7zr.SevenZipFile(archive, "r") as zf:
                        zf.extractall(target)
                log["extracted"].append(str(archive))
                archive.unlink()
            except Exception as e:
                log["failed"].append(f"{archive} - {e}")
    
    print(f"✓ Extracted {len(log['extracted'])} archives\n")
    
    # 2. Verify Meshes
    print("🎨 Step 2: Checking meshes...")
    usable = [p for p in work_dir.rglob("*") if p.suffix.lower() in USABLE_MESH_EXTS]
    log["meshes_usable"] = len(usable)
    print(f"✓ Found {len(usable)} usable mesh files\n")
    
    # 3. Extract Config Values
    print("⚙️ Step 3: Extracting configuration values...")
    extract_all_config_values(work_dir, output_dir, log)
    
    # 4. Organize Files
    print("\n📂 Step 4: Organizing files...")
    counts = defaultdict(int)
    for c in ["01_Logic_Configs", "02_Assets_Media", "03_CSV_Data", "04_Network_Backend", "05_Unclassified", "06_DLLs_Raw_Original"]:
        (output_dir / c).mkdir(parents=True, exist_ok=True)
    
    all_files = [p for p in work_dir.rglob("*") if p.is_file()]
    total_files = len(all_files)
    print(f"Organizing {total_files} files...")
    
    for idx, f in enumerate(all_files):
        if idx % 100 == 0 and idx > 0:
            print(f"  ... {idx}/{total_files}")
        
        ext = f.suffix.lower()
        path_lower = str(f).lower()
        
        # Skip irrelevant SDK files
        if any(p in path_lower for p in IRRELEVANT_SDK_PATTERNS):
            counts["00_Excluded"] += 1
            try:
                f.unlink()
            except:
                pass
            continue
        
        # Categorize
        is_net = any(kw in path_lower for kw in NETWORK_PATH_KEYWORDS)
        if not is_net and ext in {".cs", ".c"}:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").lower()
                is_net = any(kw in content for kw in NETWORK_CONTENT_KEYWORDS)
            except:
                pass
        
        if is_net:
            key = "04_Network_Backend"
        elif ext in TEXT_LOGIC_EXTS:
            key = "01_Logic_Configs"
        elif ext in MEDIA_EXTS:
            key = "02_Assets_Media"
        elif ext in CSV_EXTS:
            key = "03_CSV_Data"
        else:
            key = "05_Unclassified"
        
        dest = output_dir / key / f.name
        i = 1
        while dest.exists():
            dest = output_dir / key / f"{f.stem}_{i}{f.suffix}"
            i += 1
        
        try:
            shutil.move(str(f), str(dest))
            counts[key] += 1
        except Exception as e:
            log["failed"].append(f"{f} - {e}")
    
    print(f"✓ Files organized\n")
    
    # 5. Generate Report
    print("📊 Step 5: Generating report...")
    manifest = {
        "counts": dict(counts),
        "archives_extracted": len(log["extracted"]),
        "meshes_usable": log.get("meshes_usable", 0),
        "config_files_extracted": log.get("config_files_extracted", 0),
        "failed_items": len(log["failed"]),
        "failed_list": log["failed"][:10] if log["failed"] else [],
    }
    
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("=" * 60)
    print("📋 PIPELINE SUMMARY")
    print("=" * 60)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    
    return manifest

# ============================================================
# MAIN EXECUTION
# ============================================================

if not LOCAL_INPUT.exists() or not list(LOCAL_INPUT.glob("*")):
    print("⚠️ No files found in input directory!")
    print(f"   Path: {LOCAL_INPUT}")
    print("   Exiting...")
    sys.exit(1)

print(f"\n✓ Found files to process")
print(f"   Input: {LOCAL_INPUT}")
print(f"   Output: {LOCAL_OUTPUT}\n")

manifest = run_pipeline(LOCAL_INPUT, LOCAL_OUTPUT)

print("\n" + "=" * 60)
print("✅ PIPELINE COMPLETE!")
print("=" * 60)
print(f"\n📁 Results saved to: {LOCAL_OUTPUT}\n")

# List output structure
print("📂 Output Structure:")
for category in sorted(LOCAL_OUTPUT.glob("*")):
    if category.is_dir():
        count = len(list(category.rglob("*")))
        print(f"   {category.name}: {count} items")

sys.exit(0)
PYTHON_SCRIPT

echo "✓ Pipeline script created"
echo ""
echo "▶️ Starting pipeline execution..."
echo ""

python3 master_pipeline_local.py

PIPELINE_EXIT=$?

# ============================================================
# Phase 6: Upload results to Google Drive
# ============================================================
echo ""
echo "📤 Phase 6: Uploading results to Google Drive..."
echo ""

if [ $PIPELINE_EXIT -eq 0 ]; then
    OUTPUT_DIR="$WORKSPACE/output"
    
    # Check if output exists
    if [ -d "$OUTPUT_DIR" ]; then
        # Create a unique folder in Drive for this run
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        DRIVE_PATH="Master_Pipeline_Results_$TIMESTAMP"
        
        echo "Uploading to: gdrive:$DRIVE_PATH"
        rclone copy "$OUTPUT_DIR" "gdrive:$DRIVE_PATH" --progress
        
        echo ""
        echo "✓ Upload complete!"
        echo ""
        echo "📍 Results location on Google Drive:"
        echo "   Path: $DRIVE_PATH"
        echo ""
        
        # Generate Drive link
        echo "🔗 Accessing your Google Drive..."
        FOLDER_ID=$(rclone lsd gdrive: | grep "$DRIVE_PATH" | awk '{print $NF}')
        
        if [ ! -z "$FOLDER_ID" ]; then
            DRIVE_LINK="https://drive.google.com/drive/folders/$FOLDER_ID"
            echo ""
            echo "✅ Direct Drive Link:"
            echo "   $DRIVE_LINK"
        fi
    else
        echo "⚠️ Output directory not found"
    fi
else
    echo "⚠️ Pipeline execution failed (exit code: $PIPELINE_EXIT)"
fi

# ============================================================
# Final Summary
# ============================================================
echo ""
echo "==============================================="
echo "🎉 COMPLETE!"
echo "==============================================="
echo ""
echo "📊 Summary:"
echo "   ✓ rclone configured"
echo "   ✓ Files downloaded from Drive"
echo "   ✓ Pipeline executed"
echo "   ✓ Results uploaded to Drive"
echo ""
echo "📁 Local workspace: $WORKSPACE"
echo ""
echo "==============================================="
