import subprocess
from pathlib import Path

__HERE__ = Path(__file__).parent


def set_config() -> None:
    from streamlit import config

    config.set_option("theme.primaryColor", "#FF4B4B")
    config.set_option("theme.backgroundColor", "#FFFFFF")
    config.set_option("theme.secondaryBackgroundColor", "#F0F2F6")
    config.set_option("theme.textColor", "#31333F")
    config.set_option("theme.font", "sans serif")


def run_streamlit():
    from streamlit.web import bootstrap

    set_config()
    app_path = __HERE__.joinpath("app.py").as_posix()
    bootstrap.run(app_path, False, [], {"theme.base": "light"})


if __name__ == "__main__":
    reqs_path = __HERE__.joinpath("requirements.txt").as_posix()
    cmd = f"pip3 install -r {reqs_path}".split()
    install = subprocess.run(cmd)
    install.check_returncode()
    run_streamlit()
