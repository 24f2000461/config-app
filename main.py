from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

defaults = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000"
}

def parse_bool(val):
    return str(val).lower() in ("true", "1", "yes", "on")

def coerce(key, val):
    if key in ("port", "workers"):
        return int(val)
    if key == "debug":
        return parse_bool(val)
    return str(val)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/effective-config")
def effective_config(set: List[str] = Query(default=[])):
    config = defaults.copy()

    # Layer 2: YAML
    try:
        import yaml
        with open("config.development.yaml") as f:
            yaml_cfg = yaml.safe_load(f)
            for k, v in yaml_cfg.items():
                if k in config:
                    config[k] = coerce(k, v)
    except Exception:
        pass

    # Layer 3: .env
    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(".env")
    except Exception:
        env_vals = {}

    env_map = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        "NUM_WORKERS": "workers"
    }

    for env_key, cfg_key in env_map.items():
        if env_key in env_vals:
            config[cfg_key] = coerce(cfg_key, env_vals[env_key])

    # Layer 4: OS env
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            config[cfg_key] = coerce(cfg_key, val)

    # Layer 5: CLI overrides
    for item in set:
        if "=" in item:
            k, v = item.split("=", 1)
            if k in config:
                config[k] = coerce(k, v)

    config["api_key"] = "****"
    return config
