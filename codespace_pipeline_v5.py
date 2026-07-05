"""
MASTER PIPELINE V5 - CODESPACE VERSION (المحسّن لـ GitHub Codespace)
نسخة معدّلة من البايبلاين الأصلي للعمل المباشر مع Codespace بدون Google Drive
"""
import os
import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("🚀 MASTER PIPELINE V5 - CODESPACE EXECUTION")
print("=" * 70)
print(f"\n📍 Environment: GitHub Codespace")
print(f"📁 Workspace: {os.getcwd()}\n")

# ============================================================
# Phase 0: Setup Environment
# ============================================================
print("=" * 70)
print("Phase 0: Environment Setup")
print("=" * 70 + "\n")

# Install dependencies silently
subprocess.run([sys.executable, "-m", "pip", "install", "py7zr", "dnfile", "pyyaml", "-q"], check=False)

import re
import json
import shutil
import zipfile
from collections import defaultdict
import py7zr
import yaml
import dnfile

print("✓ All dependencies installed\n")

# ============================================================
# Phase 1: Setup Local Directories
# ============================================================
print("=" * 70)
print("Phase 1: Setting Up Workspace")
print("=" * 70 + "\n")

WORKSPACE = Path.cwd() / "master_pipeline_workspace"
LOCAL_INPUT = WORKSPACE / "raw_input"
LOCAL_OUTPUT = WORKSPACE / "ORGANIZED_MASTER_PROJECT"

# Clean and recreate
if WORKSPACE.exists():
    shutil.rmtree(WORKSPACE)
WORKSPACE.mkdir()
LOCAL_INPUT.mkdir(parents=True)
LOCAL_OUTPUT.mkdir(parents=True)

print(f"✓ Workspace created: {WORKSPACE}")
print(f"✓ Input directory: {LOCAL_INPUT}")
print(f"✓ Output directory: {LOCAL_OUTPUT}\n")

# ============================================================
# Phase 2: Create Sample Game Assets (Demo Data)
# ============================================================
print("=" * 70)
print("Phase 2: Creating Sample Game Project")
print("=" * 70 + "\n")

# Create sample directory structure like a real game
(LOCAL_INPUT / "Assets" / "Scenes").mkdir(parents=True)
(LOCAL_INPUT / "Assets" / "Scripts").mkdir(parents=True)
(LOCAL_INPUT / "Assets" / "Config").mkdir(parents=True)
(LOCAL_INPUT / "Assets" / "Data").mkdir(parents=True)

# MainScene.yaml
scene_yaml = LOCAL_INPUT / "Assets" / "Scenes" / "MainScene.yaml"
scene_yaml.write_text("""
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &123456
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 123457}
  - component: {fileID: 123458}
  m_Layer: 0
  m_Name: MainPlayer
  m_TagString: Player
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &123457
Transform:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 123456}
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalPosition: {x: 0, y: 1, z: 0}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_Children: []
  m_Father: {fileID: 0}
  m_RootOrder: 0
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
--- !u!114 &123458
MonoBehaviour:
  m_ObjectHideFlags: 1
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 123456}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: 5f7201a12d95ffc409449d95f23cf332, type: 3}
  m_Name: 
  m_EditorClassIdentifier: 
  speed: 5.5
  health: 100
  damage: 25
""")

# GameConfig.json
config_json = LOCAL_INPUT / "Assets" / "Config" / "GameConfig.json"
config_json.write_text(json.dumps({
    "gameTitle": "Ultimate Battle Lands",
    "version": "1.2.5",
    "platform": "Android",
    "buildVersion": 42,
    "maxPlayers": 4,
    "networking": {
        "provider": "Photon",
        "appId": "photon_abc123def456",
        "server": "eu.photonengine.com",
        "port": 5055
    },
    "gameplay": {
        "difficulty": "Hard",
        "spawnRate": 2.5,
        "timeLimit": 300
    },
    "graphics": {
        "quality": "High",
        "resolution": "1920x1080",
        "fps": 60
    }
}, indent=2))

# player_stats.csv
stats_csv = LOCAL_INPUT / "Assets" / "Data" / "player_stats.csv"
stats_csv.write_text("""ID,PlayerName,Score,Level,Kills,Deaths,Ping,JoinDate
1,Player001,5000,25,150,45,45,2026-01-15
2,Player002,4850,24,142,52,62,2026-01-16
3,Player003,5200,26,158,40,38,2026-01-14
4,Player004,4650,23,135,58,71,2026-01-17
5,Player005,5100,25,149,43,49,2026-01-15
6,Player006,4900,24,138,55,58,2026-01-18
7,Player007,5150,25,152,41,44,2026-01-16
8,Player008,4750,24,140,50,52,2026-01-19""")

# NetworkManager.cs - Network code
network_cs = LOCAL_INPUT / "Assets" / "Scripts" / "NetworkManager.cs"
network_cs.write_text("""using UnityEngine;
using Photon.Pun2;
using ExitGames.Client.Photon;

public class NetworkManager : MonoBehaviourPunCallbacks
{
    [SerializeField] private float speed = 5f;
    [SerializeField] private int maxPlayers = 4;
    [SerializeField] private bool usePhoton = true;
    
    private PhotonView photonView;
    
    void Start()
    {
        photonView = GetComponent<PhotonView>();
        
        if (usePhoton)
        {
            PhotonNetwork.ConnectUsingSettings();
        }
    }
    
    public override void OnConnectedToPhoton()
    {
        Debug.Log("Connected to Photon Network!");
    }
    
    public override void OnJoinedLobby()
    {
        Debug.Log("Joined Photon Lobby");
    }
    
    [PunRPC]
    public void RPC_PlayerJoined(string playerName)
    {
        Debug.Log($"Player {playerName} joined the game!");
    }
    
    [PunRPC]
    public void RPC_PlayerSpawned(Vector3 position, string playerName)
    {
        Debug.Log($"Player spawned at {position}");
    }
    
    public void SpawnPlayer(Vector3 position)
    {
        if (photonView.IsMine)
        {
            photonView.RPC("RPC_PlayerSpawned", RpcTarget.All, position, gameObject.name);
        }
    }
}""")

# game_config.asset
asset_file = LOCAL_INPUT / "Assets" / "Config" / "game_config.asset"
asset_file.write_text("""
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_GameObject: {fileID: 0}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: gameconfig, type: 3}
  m_Name: GameConfig
  m_EditorClassIdentifier: 
  gameTitle: Ultimate Battle Lands
  version: 1.2.5
  targetPlatform: Mobile
  buildVersion: 42
  serverUrl: https://api.ultimatebattlelands.com
  analyticsEnabled: 1
  photonEnabled: 1
  characters:
    - name: Warrior
      health: 150
      damage: 35
      speed: 4.5
    - name: Mage
      health: 80
      damage: 50
      speed: 5.5
    - name: Archer
      health: 100
      damage: 40
      speed: 6.0
  maps:
    - name: Forest
      maxPlayers: 8
      spawnPoints: 10
    - name: Desert
      maxPlayers: 6
      spawnPoints: 8
    - name: City
      maxPlayers: 10
      spawnPoints: 12
""")

# prefab
prefab_file = LOCAL_INPUT / "Assets" / "Scenes" / "PlayerPrefab.prefab"
prefab_file.write_text("""
%YAML 1.1
--- !u!1 &2850000
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 2850001}
  - component: {fileID: 2850002}
  - component: {fileID: 2850003}
  m_Layer: 0
  m_Name: PlayerPrefab
  m_TagString: Player
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &2850001
Transform:
  m_ObjectHideFlags: 1
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalScale: {x: 1, y: 1, z: 1}
--- !u!114 &2850002
MonoBehaviour:
  m_ObjectHideFlags: 1
  m_Script: {fileID: 11500000, guid: player}
  playerName: DefaultPlayer
  playerLevel: 1
  experience: 0
  health: 100
--- !u!65 &2850003
BoxCollider:
  m_ObjectHideFlags: 1
  m_Size: {x: 1, y: 2, z: 1}
""")

# Settings ini
settings_ini = LOCAL_INPUT / "Assets" / "Config" / "settings.ini"
settings_ini.write_text("""[Graphics]
quality=High
resolution=1920x1080
fps=60
vsync=false

[Audio]
masterVolume=0.8
musicVolume=0.6
sfxVolume=0.9

[Network]
autoReconnect=true
timeout=30
retryAttempts=3

[Gameplay]
difficulty=Hard
language=en""")

# localization.xml
localization_xml = LOCAL_INPUT / "Assets" / "Config" / "localization.xml"
localization_xml.write_text("""<?xml version="1.0" encoding="utf-8"?>
<languages>
    <language id="en">
        <string name="welcome">Welcome to Ultimate Battle Lands</string>
        <string name="play">Play Game</string>
        <string name="settings">Settings</string>
        <string name="quit">Exit</string>
    </language>
    <language id="ar">
        <string name="welcome">أهلا بك في معركة الأراضي النهائية</string>
        <string name="play">العب اللعبة</string>
        <string name="settings">الإعدادات</string>
        <string name="quit">خروج</string>
    </language>
</languages>""")

# README
readme = LOCAL_INPUT / "README.md"
readme.write_text("""# Ultimate Battle Lands - Game Assets

## Project Structure
- Assets/Scenes: Game scenes and prefabs
- Assets/Scripts: C# scripts including networking code
- Assets/Config: Configuration files and game settings
- Assets/Data: Game data (stats, player info, etc.)

## Networking
This project uses **Photon PUN 2** for multiplayer networking.

## Build Information
- Version: 1.2.5
- Platform: Android/iOS
- Max Players: 4-10
""")

files_created = len(list(LOCAL_INPUT.rglob("*")))
print(f"✅ Created sample project with {files_created} files:")
for f in sorted(LOCAL_INPUT.rglob("*")):
    if f.is_file():
        rel_path = f.relative_to(LOCAL_INPUT)
        size = f.stat().st_size
        print(f"   ✓ {rel_path} ({size} bytes)")

# ============================================================
# Phase 3: Configuration (from original pipeline)
# ============================================================
print("\n" + "=" * 70)
print("Phase 3: Configuration & Analysis Rules")
print("=" * 70 + "\n")

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
TEXT_LOGIC_EXTS = {".cs", ".json", ".yaml", ".yml", ".asset", ".prefab", ".txt", ".xml", ".ini", ".cfg", ".c", ".md"}
CSV_EXTS = {".csv"}
USABLE_MESH_EXTS = {".glb", ".gltf", ".fbx", ".obj"}

NETWORK_CONTENT_KEYWORDS = ["photon", "quantum", "exitgames", "enet", "photonnetwork", "rpc", "networkrunner", "irpcallback"]
NETWORK_PATH_KEYWORDS = ["photon", "quantum", "exitgames", "network", "multiplayer"]

print("✓ Configuration loaded")
print("✓ Analysis rules initialized\n")

# ============================================================
# Phase 4: Parse and Organize Files
# ============================================================
print("=" * 70)
print("Phase 4: Parsing & Organizing Files")
print("=" * 70 + "\n")

def parse_unity_yaml(path: Path):
    """Parse Unity YAML files"""
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
    """Build clean structure from parsed objects"""
    result = {"game_objects": []}
    for file_id, obj in objects.items():
        if obj["class_name"] != "GameObject":
            continue
        go_data = obj["data"].get("GameObject", {}) if obj["data"] else {}
        name = go_data.get("m_Name", "Unnamed")
        components_resolved = []
        for comp_ref in go_data.get("m_Component", []) or []:
            comp_file_id = str(comp_ref.get("component", {}).get("fileID", ""))
            comp_obj = objects.get(comp_file_id)
            if not comp_obj:
                continue
            comp_class = comp_obj["class_name"]
            comp_data = comp_obj["data"].get(comp_class, {}) if comp_obj["data"] else {}
            useful_fields = {k: v for k, v in comp_data.items() if k not in IGNORED_FIELDS}
            components_resolved.append({"type": comp_class, "fields": useful_fields})
        result["game_objects"].append({"name": name, "components": components_resolved})
    return result

def extract_all_config_values(work_dir: Path, output_dir: Path, log: dict):
    """Extract configuration values from asset files"""
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$")
    all_values = {}
    asset_files = [p for p in work_dir.rglob("*") if p.suffix.lower() in {".asset", ".prefab"}]
    total = len(asset_files)
    
    if total == 0:
        return
    
    print(f"استخراج القيم من {total} ملف .asset/.prefab...")
    for idx, f in enumerate(asset_files):
        if idx % 50 == 0 and idx > 0:
            print(f"  ... {idx}/{total} معالج")
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
    print(f"✓ تم استخراج {len(all_values)} ملف تكوين")

def decompose_all_prefabs_assets(work_dir: Path, output_dir: Path, log: dict):
    """Decompose prefabs and assets"""
    out_dir = output_dir / "01_Logic_Configs" / "decomposed_prefabs_assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = [p for p in work_dir.rglob("*") if p.suffix.lower() in {".prefab", ".asset"}]
    total = len(targets)
    
    if total == 0:
        return
    
    print(f"تفكيك هرمي لـ {total} ملف .prefab/.asset...")
    decomposed = 0
    for idx, f in enumerate(targets):
        if idx % 50 == 0 and idx > 0:
            print(f"  ... {idx}/{total} ملف مُعالَج")
        objects, err = parse_unity_yaml(f)
        if err:
            log["failed"].append(f"{f} — خطأ: {err}")
            continue
        clean = build_clean_structure(objects) if objects else {"game_objects": []}
        if not clean["game_objects"]:
            continue
        out_path = out_dir / f"{f.stem}.json"
        out_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        decomposed += 1
    
    log["prefabs_decomposed"] = decomposed
    print(f"✓ تم تفكيك {decomposed} ملف")

def run_pipeline(work_dir: Path, output_dir: Path):
    """Main pipeline function"""
    log = {"extracted": [], "failed": []}
    
    # 1. Extract Archives
    print("📦 خطوة 1: فك الأرشيفات...")
    pass_num = 0
    while True:
        pass_num += 1
        archives = list(work_dir.rglob("*.zip")) + list(work_dir.rglob("*.7z"))
        if not archives:
            break
        print(f"[الجولة {pass_num}] فك {len(archives)} أرشيف...")
        for i, archive in enumerate(archives):
            if i % 20 == 0 and i > 0:
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
    
    print(f"�� تم فك {len(log['extracted'])} أرشيف\n")
    
    # 2. Verify Meshes
    print("🎨 خطوة 2: التحقق من الـ Meshes...")
    usable = [p for p in work_dir.rglob("*") if p.suffix.lower() in USABLE_MESH_EXTS]
    broken = [p for p in work_dir.rglob("*") if p.suffix.lower() == ".mesh"]
    log["meshes_usable"] = len(usable)
    log["meshes_broken"] = len(broken)
    print(f"✓ ملفات الـ Meshes الصالحة: {len(usable)}\n")
    
    # 3. Extract Configs
    print("⚙️ خطوة 3: استخراج التكوينات...")
    extract_all_config_values(work_dir, output_dir, log)
    
    # 4. Decompose Prefabs
    print("\n🔧 خطوة 4: تفكيك الـ Prefabs...")
    decompose_all_prefabs_assets(work_dir, output_dir, log)
    
    # 5. Organize Files
    print("\n📂 خطوة 5: تنظيم الملفات...")
    counts = defaultdict(int)
    for c in ["01_Logic_Configs", "02_Assets_Media", "03_CSV_Data", "04_Network_Backend", "05_Unclassified", "06_DLLs_Raw_Original"]:
        (output_dir / c).mkdir(parents=True, exist_ok=True)
    
    all_files = [p for p in work_dir.rglob("*") if p.is_file()]
    total_files = len(all_files)
    print(f"��نظيم {total_files} ملف...")
    
    for idx, f in enumerate(all_files):
        if idx % 200 == 0 and idx > 0:
            print(f"  ... تمت معالجة {idx}/{total_files} ملف")
        
        ext = f.suffix.lower()
        path_lower = str(f).lower()
        
        # Skip irrelevant SDKs
        if any(p in path_lower for p in IRRELEVANT_SDK_PATTERNS):
            counts["00_Excluded"] += 1
            try:
                f.unlink()
            except:
                pass
            continue
        
        # Check for network code
        is_net = any(kw in path_lower for kw in NETWORK_PATH_KEYWORDS)
        if not is_net and ext in {".cs", ".c"}:
            try:
                is_net = any(kw in f.read_text(encoding="utf-8", errors="ignore").lower() for kw in NETWORK_CONTENT_KEYWORDS)
            except:
                pass
        
        # Categorize
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
    
    print(f"✓ تم تنظيم الملفات\n")
    
    # Generate manifest
    manifest = {
        "counts": dict(counts),
        "archives_extracted": len(log["extracted"]),
        "meshes_usable": log.get("meshes_usable", 0),
        "meshes_broken": log.get("meshes_broken", 0),
        "config_files_extracted": log.get("config_files_extracted", 0),
        "prefabs_decomposed": log.get("prefabs_decomposed", 0),
        "failed_items": len(log["failed"]),
        "failed_list": log["failed"][:20] if log["failed"] else [],
    }
    
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest

print("✓ Functions defined\n")

# ============================================================
# Phase 5: Execute Pipeline
# ============================================================
print("=" * 70)
print("Phase 5: Running Pipeline")
print("=" * 70 + "\n")

manifest = run_pipeline(LOCAL_INPUT, LOCAL_OUTPUT)

# ============================================================
# Phase 6: Results & Report
# ============================================================
print("\n" + "=" * 70)
print("✅ PIPELINE EXECUTION COMPLETE!")
print("=" * 70 + "\n")

print("📊 FINAL RESULTS:\n")
print(json.dumps(manifest, indent=2, ensure_ascii=False))

print("\n" + "=" * 70)
print("📍 Output Location")
print("=" * 70 + "\n")
print(f"Base:     {LOCAL_OUTPUT}")
print(f"Manifest: {LOCAL_OUTPUT / 'manifest.json'}\n")

print("📂 Categories:")
for cat in sorted(LOCAL_OUTPUT.glob("*")):
    if cat.is_dir():
        count = len(list(cat.glob("*")))
        print(f"   ✓ {cat.name}: {count} items")

print("\n" + "=" * 70)
print("✨ CODESPACE PIPELINE SUCCESS!")
print("=" * 70 + "\n")

# List all files
print("📄 ALL OUTPUT FILES:\n")
for root, dirs, files in os.walk(LOCAL_OUTPUT):
    level = root.replace(str(LOCAL_OUTPUT), '').count(os.sep)
    indent = ' ' * 2 * level
    folder_name = os.path.basename(root)
    if folder_name:
        print(f'{indent}📁 {folder_name}/')
    subindent = ' ' * 2 * (level + 1)
    for file in sorted(files):
        file_path = os.path.join(root, file)
        size = os.path.getsize(file_path)
        print(f'{subindent}✓ {file} ({size} bytes)')

print("\n" + "=" * 70)
print("🎯 NEXT STEPS")
print("=" * 70)
print("""
1. ✅ Review manifest.json for detailed statistics
2. ✅ Check each category folder for organized assets
3. ✅ Analyze extracted configurations
4. ✅ Review network code in 04_Network_Backend
5. ✅ Import CSV data for further processing
6. ✅ Deploy to game engine or cloud
""")

print("🚀 Pipeline ready for deployment!\n")
