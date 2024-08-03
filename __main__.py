import subprocess
from pathlib import Path

__HERE__ = Path(__file__).parent


def run_streamlit():
    from streamlit.web import bootstrap

    app_path = __HERE__.joinpath("app.py").as_posix()
    bootstrap.run(app_path, False, [], {})


if __name__ == "__main__":
    reqs_path = __HERE__.joinpath("requirements.txt").as_posix()
    cmd = f"pip3 install -r {reqs_path}".split()
    install = subprocess.run(cmd)
    install.check_returncode()
    run_streamlit()
