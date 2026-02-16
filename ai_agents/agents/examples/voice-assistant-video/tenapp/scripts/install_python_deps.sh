#!/usr/bin/env bash

# Set default pip install command
PIP_INSTALL_CMD=${PIP_INSTALL_CMD:-"uv pip install --system"}

install_python_requirements() {
  local app_dir=$1

  echo "Starting Python dependencies installation..."


  # Install Twilio server Python dependencies
  if [[ -f "$app_dir/../server/requirements.txt" ]]; then
    echo "Installing Twilio server Python dependencies..."
    ${PIP_INSTALL_CMD} -r "$app_dir/../server/requirements.txt"
  else
    echo "No requirements.txt found in server directory: $app_dir/../server"
  fi

  # Traverse ten_packages/extension directory to find requirements.txt
  if [[ -d "$app_dir/ten_packages/extension" ]]; then
    echo "Traversing ten_packages/extension directory..."
    for extension in "$app_dir/ten_packages/extension"/*; do
      if [[ -d "$extension" && -f "$extension/requirements.txt" ]]; then
        echo "Found requirements.txt in $extension, installing dependencies..."
        ${PIP_INSTALL_CMD} -r "$extension/requirements.txt"
      fi
    done
  else
    echo "ten_packages/extension directory not found"
  fi

  # Traverse ten_packages/system directory to find requirements.txt
  if [[ -d "$app_dir/ten_packages/system" ]]; then
    echo "Traversing ten_packages/system directory..."
    for extension in "$app_dir/ten_packages/system"/*; do
      if [[ -d "$extension" && -f "$extension/requirements.txt" ]]; then
        echo "Found requirements.txt in $extension, installing dependencies..."
        ${PIP_INSTALL_CMD} -r "$extension/requirements.txt"
      fi
    done
  else
    echo "ten_packages/system directory not found"
  fi

  echo "Python dependencies installation completed!"
}

create_extension_symlinks() {
  local app_dir=$1

  echo "Creating extension symlinks..."

  # Read manifest.json to get dependencies
  if [[ ! -f "$app_dir/manifest.json" ]]; then
    echo "Warning: manifest.json not found, skipping symlink creation"
    return
  fi

  local ext_dir="$app_dir/ten_packages/extension"
  mkdir -p "$ext_dir"

  # Parse manifest.json to find local path dependencies
  python3 << EOF
import json
import os
from pathlib import Path

app_dir = Path("$app_dir")
manifest_path = app_dir / "manifest.json"

if not manifest_path.exists():
    print("Warning: manifest.json not found")
    exit(0)

with open(manifest_path) as f:
    manifest = json.load(f)

ext_dir = Path("$ext_dir")
dependencies = manifest.get("dependencies", [])

for dep in dependencies:
    if "path" in dep:
        # Calculate absolute path
        dep_path = app_dir / dep["path"]
        if not dep_path.exists():
            continue

        # Get extension name from manifest.json in the dependency path
        dep_manifest_path = dep_path / "manifest.json"
        if not dep_manifest_path.exists():
            continue

        with open(dep_manifest_path) as f:
            dep_manifest = json.load(f)

        ext_name = dep_manifest.get("name")
        if not ext_name:
            continue

        # Create symlink
        symlink_path = ext_dir / ext_name
        if symlink_path.exists() or symlink_path.is_symlink():
            if symlink_path.is_symlink():
                symlink_path.unlink()
            else:
                print(f"Warning: {symlink_path} exists and is not a symlink, skipping")
                continue

        # Use relative path for symlink
        try:
            rel_path = os.path.relpath(dep_path, ext_dir)
            symlink_path.symlink_to(rel_path)
            print(f"Created symlink: {symlink_path} -> {rel_path}")
        except Exception as e:
            print(f"Failed to create symlink {symlink_path}: {e}")

EOF
}

build_go_app() {
  local app_dir=$1
  cd $app_dir

  go run "$app_dir/ten_packages/system/ten_runtime_go/tools/build/main.go" --verbose
  if [[ $? -ne 0 ]]; then
    echo "FATAL: failed to build go app, see logs for detail."
    exit 1
  fi
}

main() {
  # Get the parent directory of script location as app root directory
  APP_HOME=$(
    cd $(dirname $0)/..
    pwd
  )

  echo "App root directory: $APP_HOME"
  echo "Using pip command: $PIP_INSTALL_CMD"

  # Check if manifest.json exists
  if [[ ! -f "$APP_HOME/manifest.json" ]]; then
    echo "Error: manifest.json file not found"
    exit 1
  fi

  # Create extension symlinks first
  create_extension_symlinks "$APP_HOME"

  build_go_app "$APP_HOME"

  # Install Python dependencies
  install_python_requirements "$APP_HOME"
}

# If script is executed directly, run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
