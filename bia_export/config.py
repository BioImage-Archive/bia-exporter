from pathlib import Path

from ruamel.yaml import YAML
from pydantic import BaseSettings


class Settings(BaseSettings):
    endpoint_url: str = "https://uk1s3.embassy.ebi.ac.uk"
    bucket_name: str = "bia-integrator-data"
    cache_root_dirpath: Path = Path.home()/".cache"
    bioformats2raw_java_home: str = ""
    bioformats2raw_bin: str = ""
    config_fpath: Path = Path("dome.yaml")

    bia_api_basepath: str = 'https://bia-cron-1.ebi.ac.uk:8080'
    bia_username: str = None
    bia_password: str = None
    disable_ssl_host_check: bool = True

    class Config:
        env_file = f"{Path(__file__).parent.parent / '.env'}"

settings = Settings()


def load_config():
    yaml = YAML()
    with open(settings.config_fpath) as fh:
        raw_config = yaml.load(fh)

    return raw_config
