DOCKER_ENABLED = True
DOCKER_SOCKET = 'unix:///var/run/docker.sock'

BASE_IMAGES = {
    'ubuntu18': 'ubuntu:18.04',
    'ubuntu20': 'ubuntu:20.04',
    'ubuntu22': 'ubuntu:22.04',
    'ros_noetic': 'ros:noetic',
    'ros_melodic': 'ros:melodic'
}

DEFAULT_BASE_IMAGE = 'ubuntu20'
DEFAULT_TIMEOUT = 600
DEFAULT_MEMORY_LIMIT = '4g'

BUILD_CACHE_DIR = '.docker_cache'
IMAGE_PREFIX = 'openslam'

COMMON_APT_PACKAGES = ['build-essential', 'cmake', 'git', 'wget', 'curl']
SLAM_APT_PACKAGES = ['libeigen3-dev', 'libopencv-dev', 'libboost-all-dev']

DOCKERFILE_TEMPLATE = '''FROM {base_image}
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y {packages} && rm -rf /var/lib/apt/lists/*
{custom_commands}
WORKDIR {workdir}
{entrypoint}'''

MOUNT_PREFIX = '/data'
OUTPUT_PREFIX = '/output'
