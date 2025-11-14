# Zero-Code SLAM Integration System

## Implementation Complete

OpenSLAM now supports configuration-only SLAM integration through YAML-driven workflows.

## Core Architecture

### Components

**connector_config.py**
Configuration constants for connector system

**docker_config.py**
Docker orchestration settings

**core/connector_engine.py**
Executes data transforms, parsers, and generators based on YAML configs

**core/docker_orchestrator.py**
Builds Docker images and runs containers from configuration

**core/workflow_executor.py**
Orchestrates multi-stage workflows: prepare → execute → extract

### Workflow Stages

**prepare**
Load and transform input data using connectors

**execute**
Run SLAM in Docker container with mounted volumes

**extract**
Parse output trajectory and compute metrics

## Configuration Format

```yaml
name: "SLAM-Name"
version: "1.0.0"
input_types: [image]
output_format: trajectory

docker:
  image: "openslam/slam:latest"

interface:
  command: ["./slam_binary", "${vocab}", "${settings}", "${images}"]

  inputs:
    - name: vocabulary
      type: file
      source: download
      url: "https://example.com/vocab.txt"
      mount: /data/vocab.txt

    - name: calibration
      type: file
      source: dataset_metadata
      connector: kitti_to_orbslam_calib
      mount: /data/calib.yaml

    - name: image_directory
      type: directory
      source: dataset_images
      mount: /data/images

  outputs:
    - name: trajectory
      type: file
      format: tum
      file: trajectory.txt
      location: /output

  volumes:
    - host: "${TEMP_DIR}/vocab.txt"
      container: /data/vocab.txt
      mode: ro
    - host: "${OUTPUT_DIR}"
      container: /output
      mode: rw

execution:
  timeout: 600
  max_memory_mb: 4096
```

## Connector System

### Built-in Connectors

**Parsers**
tum_trajectory, kitti_trajectory

**Generators**
image_list

**Transforms**
quaternion_to_matrix, matrix_to_quaternion, tum_to_kitti, kitti_to_tum

### Creating Custom Connectors

```yaml
name: custom_transform
type: transform
method: mapping

input:
  type: dict

output:
  type: dict

mapping:
  Camera.fx: calibration.K[0][0]
  Camera.fy: calibration.K[1][1]
  Camera.cx: calibration.K[0][2]
  Camera.cy: calibration.K[1][2]
```

## Docker Integration

### Auto-Build from Config

```yaml
build:
  base: ubuntu20
  apt_packages: [libeigen3-dev, libopencv-dev]
  git_repos:
    - url: https://github.com/user/SLAM
      dest: /root
      branch: master
      build_script: "mkdir build && cd build && cmake .. && make -j4"
  workdir: /root/SLAM
  entrypoint: /root/SLAM/bin/slam
```

### Pre-built Images

```yaml
docker:
  image: "openslam/orbslam3:latest"
```

## Usage

### List Plugins

```bash
python3 openslam.py list-plugins
```

### Run Workflow Plugin

```bash
python3 openslam.py evaluate-plugin orbslam3_workflow \
  --dataset data/kitti_00.txt \
  --ground-truth data/kitti_00_gt.txt \
  --format kitti
```

## Plugin Detection

PluginExecutor automatically detects plugin type:

**Workflow plugins**: contain `workflow` or `interface` in config
**C++ plugins**: contain `language: cpp`
**Python plugins**: contain `entry_point` and `functions`

## Variable Substitution

All configuration strings support variable substitution:

**${TEMP_DIR}**: temporary directory for intermediate files
**${OUTPUT_DIR}**: output directory for results
**${DATASET_PATH}**: input dataset path
**${parameter_name}**: any parameter from default_params

## Adding New SLAM

Create `plugins/new_slam/slam_config.yaml`:

```yaml
name: "NewSLAM"
version: "1.0.0"
input_types: [image]
output_format: trajectory

docker:
  image: "user/new_slam:latest"

interface:
  command: ["./run_slam", "${images}", "${output}"]

  inputs:
    - name: image_directory
      type: directory
      source: dataset_images
      mount: /data/images

  outputs:
    - name: trajectory
      type: file
      format: tum
      file: output.txt
      location: /output

  volumes:
    - host: "${TEMP_DIR}/images"
      container: /data/images
      mode: ro
    - host: "${OUTPUT_DIR}"
      container: /output
      mode: rw
```

## Integration Requirements

Minimum requirements for SLAM integration:

1. Docker image available or buildable
2. Command to execute SLAM
3. Input format specification
4. Output trajectory file location and format

## Status

**Implemented**: Core workflow system, connector engine, Docker orchestration, plugin detection

**Working**: Workflow execution, variable substitution, volume mounting, trajectory parsing

**Example**: orbslam3_workflow plugin demonstrates complete configuration

## Next Steps

1. Implement auto-download for vocabulary files
2. Add calibration file auto-generation from dataset metadata
3. Create library of pre-built SLAM Docker images
4. Implement connector chaining for complex transformations
5. Add validation for workflow configurations
6. Create interactive plugin wizard
