import subprocess
import json
from pathlib import Path
import tempfile
import shutil
from config import docker_config as dcfg

class DockerOrchestrator:
    def __init__(self):
        self.client = None
        self.images = {}
        self.containers = {}
        self._check_docker()

    def _check_docker(self):
        result = subprocess.run(['which', 'docker'], capture_output=True)
        if result.returncode != 0:
            self.docker_available = False
            return
        result = subprocess.run(['docker', 'ps'], capture_output=True)
        self.docker_available = result.returncode == 0

    def build_image(self, config, plugin_name):
        if not self.docker_available:
            return None, 'docker_not_available'

        build_config = config.get('build', {})
        base_image = build_config.get('base', dcfg.DEFAULT_BASE_IMAGE)
        if base_image in dcfg.BASE_IMAGES:
            base_image = dcfg.BASE_IMAGES[base_image]

        apt_packages = build_config.get('apt_packages', [])
        all_packages = dcfg.COMMON_APT_PACKAGES + dcfg.SLAM_APT_PACKAGES + apt_packages
        packages_str = ' '.join(all_packages)

        custom_commands = self._generate_build_commands(build_config)
        workdir = build_config.get('workdir', '/root')
        entrypoint = build_config.get('entrypoint', '')
        if entrypoint:
            entrypoint = f'ENTRYPOINT ["{entrypoint}"]'

        dockerfile_content = dcfg.DOCKERFILE_TEMPLATE.format(base_image=base_image, packages=packages_str, custom_commands=custom_commands, workdir=workdir, entrypoint=entrypoint)

        temp_dir = Path(tempfile.mkdtemp())
        dockerfile_path = temp_dir / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        image_name = f'{dcfg.IMAGE_PREFIX}/{plugin_name}'
        image_tag = config.get('version', 'latest')
        full_image_name = f'{image_name}:{image_tag}'

        result = subprocess.run(['docker', 'build', '-t', full_image_name, str(temp_dir)], capture_output=True, text=True, timeout=1800)

        shutil.rmtree(temp_dir)

        if result.returncode != 0:
            return None, f'docker_build_failed: {result.stderr}'

        self.images[plugin_name] = full_image_name
        return full_image_name, None

    def _generate_build_commands(self, build_config):
        commands = []

        git_repos = build_config.get('git_repos', [])
        for repo in git_repos:
            url = repo.get('url')
            dest = repo.get('dest', '/root')
            branch = repo.get('branch', 'master')
            build_script = repo.get('build_script')

            commands.append(f'RUN cd {dest} && git clone --branch {branch} {url}')
            if build_script:
                repo_name = url.split('/')[-1].replace('.git', '')
                commands.append(f'RUN cd {dest}/{repo_name} && {build_script}')

        custom_steps = build_config.get('custom_steps', [])
        for step in custom_steps:
            commands.append(f'RUN {step}')

        return '\n'.join(commands)

    def get_image(self, plugin_name, config):
        docker_config = config.get('docker', {})

        if 'image' in docker_config:
            image_name = docker_config['image']
            self.images[plugin_name] = image_name
            return image_name, None

        if plugin_name in self.images:
            return self.images[plugin_name], None

        if 'build' in config:
            return self.build_image(config, plugin_name)

        return None, 'no_docker_image_specified'

    def run_container(self, image_name, command, volumes, environment=None, timeout=None):
        if not self.docker_available:
            return None, 'docker_not_available'

        cmd = ['docker', 'run', '--rm']

        for vol in volumes:
            cmd.extend(['-v', vol])

        if environment:
            for key, value in environment.items():
                cmd.extend(['-e', f'{key}={value}'])

        cmd.append(image_name)

        if isinstance(command, list):
            cmd.extend(command)
        else:
            cmd.append(command)

        timeout_value = timeout if timeout else dcfg.DEFAULT_TIMEOUT

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_value)

        output = {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}

        if result.returncode != 0:
            return output, 'container_execution_failed'

        return output, None

    def prepare_volumes(self, volume_config, temp_dir, output_dir):
        volumes = []

        for vol in volume_config:
            host_path = vol.get('host')
            container_path = vol.get('container')
            mode = vol.get('mode', dcfg.MOUNT_PREFIX)

            if host_path.startswith('${TEMP_DIR}'):
                host_path = host_path.replace('${TEMP_DIR}', str(temp_dir))
            elif host_path.startswith('${OUTPUT_DIR}'):
                host_path = host_path.replace('${OUTPUT_DIR}', str(output_dir))

            volume_str = f'{host_path}:{container_path}:{mode}'
            volumes.append(volume_str)

        return volumes

    def check_image_exists(self, image_name):
        result = subprocess.run(['docker', 'images', '-q', image_name], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
