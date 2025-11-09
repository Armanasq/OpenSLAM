import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import Config
config = Config()
config.load("development")
def generate_docker_command():
    port = config.get("server.code_server_port")
    password = config.get("code_server.password")
    image = config.get("code_server.image")
    project_root = config.get("paths.project_root")
    abs_project_root = os.path.abspath(project_root)
    command = f'docker run -p {port}:{port} -e PASSWORD=\'{password}\' -v "{abs_project_root}:/home/coder/project" {image}'
    return command
def run_code_server():
    command = generate_docker_command()
    print(f"Starting code server with command:")
    print(command)
    os.system(command)
if __name__ == "__main__":
    run_code_server()
