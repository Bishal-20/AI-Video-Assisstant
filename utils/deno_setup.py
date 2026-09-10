import os
import subprocess


DENO_DIR = os.path.expanduser("~/.deno")
DENO_BIN = os.path.join(DENO_DIR, "bin", "deno")


def setup_deno():
    if os.path.exists(DENO_BIN):
        os.environ["PATH"] = f"{DENO_DIR}/bin:" + os.environ.get("PATH", "")
        return DENO_BIN

    print("Deno not found. Installing Deno...")

    subprocess.run(
        "curl -fsSL https://deno.land/install.sh | sh",
        shell=True,
        check=True,
    )

    os.environ["PATH"] = f"{DENO_DIR}/bin:" + os.environ.get("PATH", "")

    if not os.path.exists(DENO_BIN):
        raise RuntimeError("Deno installation failed.")

    print("Deno installed successfully.")

    return DENO_BIN