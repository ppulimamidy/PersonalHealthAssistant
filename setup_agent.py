import os
import platform
import subprocess
import shutil

log_file = "setup_agent.log"

def log(msg):
    print(msg)
    with open(log_file, "a") as f:
        f.write(f"{msg}\n")

def run_cmd(cmd, check=False):
    try:
        subprocess.run(cmd, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        log(f"❌ Command failed: {cmd}")

def is_installed(tool):
    return shutil.which(tool) is not None

def install_package_linux(pkg):
    log(f"📦 Installing {pkg} via apt...")
    run_cmd(f"sudo apt update && sudo apt install -y {pkg}", check=True)

def install_package_mac(pkg):
    log(f"📦 Installing {pkg} via brew...")
    run_cmd(f"brew install {pkg}", check=True)

def install_npm_package(pkg):
    if not is_installed(pkg):
        log(f"📦 Installing {pkg} via npm...")
        run_cmd(f"npm install -g {pkg}")

def install_pip_package(pkg):
    log(f"🐍 Installing Python package: {pkg}")
    run_cmd(f"pip install {pkg}")

def detect_os():
    sys = platform.system().lower()
    if "darwin" in sys:
        return "mac"
    elif "linux" in sys:
        return "linux"
    else:
        return "unsupported"

def install_tools():
    os_type = detect_os()
    if os_type == "unsupported":
        log("❌ Unsupported OS. Exiting.")
        return

    log(f"🧠 Detected OS: {os_type.upper()}")
    installer = install_package_mac if os_type == "mac" else install_package_linux

    # System tools
    for pkg in ["git", "curl", "wget", "make", "unzip", "jq"]:
        if not is_installed(pkg):
            installer(pkg)
        else:
            log(f"✅ {pkg} already installed.")

    # Python
    if not is_installed("python3"):
        installer("python3")
    if not is_installed("pip3"):
        installer("python3-pip")

    run_cmd("pip3 install --upgrade pip")

    # Docker
    if not is_installed("docker"):
        installer("docker.io" if os_type == "linux" else "docker")

    # Supabase CLI
    install_npm_package("supabase")

    # Kafka via Docker Compose
    log("📦 Preparing Kafka + Zookeeper via Docker Compose...")

    compose_yml = """version: '3'
services:
  zookeeper:
    image: bitnami/zookeeper:latest
    ports:
      - "2181:2181"
  kafka:
    image: bitnami/kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_ZOOKEEPER_CONNECT: zookeeper:2181
      ALLOW_PLAINTEXT_LISTENER: "yes"
"""
    with open("docker-compose.kafka.yml", "w") as f:
        f.write(compose_yml)

    # Pip packages
    for pkg in ["pytest", "pytest-asyncio", "duckdb", "langchain", "openai", "qdrant-client", "redis"]:
        install_pip_package(pkg)

    log("✅ Setup completed successfully.")

if __name__ == "__main__":
    install_tools()
