import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
class PointCloudRenderer {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.controls = null;
        this.pointCloud = null;
        this.trajectoryLine = null;
        this.currentPoseMarker = null;
        this.points = [];
        this.colors = [];
        this.selectedPoint = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.animationId = null;
        this.init();
    }
    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(0x000000);
        this.container.appendChild(this.renderer.domElement);
        this.camera.position.set(0, 5, 10);
        this.camera.lookAt(0, 0, 0);
        this.setupControls();
        this.setupLighting();
        this.setupEventListeners();
        this.animate();
    }
    setupControls() {
        const OrbitControls = require('three/examples/jsm/controls/OrbitControls').OrbitControls;
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableZoom = true;
        this.controls.enablePan = true;
        this.controls.maxDistance = 100;
        this.controls.minDistance = 1;
    }
    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);
    }
    setupEventListeners() {
        this.renderer.domElement.addEventListener('click', (event) => this.onMouseClick(event));
        this.renderer.domElement.addEventListener('mousemove', (event) => this.onMouseMove(event));
    }
    updatePointCloud(pointData, colorMode = 'depth') {
        if (this.pointCloud) {
            this.scene.remove(this.pointCloud);
        }
        this.points = [];
        this.colors = [];
        let minDepth = Infinity;
        let maxDepth = -Infinity;
        pointData.forEach(point => {
            this.points.push(point.x, point.y, point.z);
            const depth = Math.sqrt(point.x * point.x + point.y * point.y + point.z * point.z);
            minDepth = Math.min(minDepth, depth);
            maxDepth = Math.max(maxDepth, depth);
        });
        pointData.forEach(point => {
            const depth = Math.sqrt(point.x * point.x + point.y * point.y + point.z * point.z);
            let color;
            switch (colorMode) {
                case 'depth':
                    const normalizedDepth = (depth - minDepth) / (maxDepth - minDepth);
                    color = this.depthToColor(normalizedDepth);
                    break;
                case 'height':
                    const normalizedHeight = (point.y + 10) / 20;
                    color = this.heightToColor(normalizedHeight);
                    break;
                case 'intensity':
                    const intensity = point.intensity || 0.5;
                    color = new THREE.Color(intensity, intensity, intensity);
                    break;
                default:
                    color = new THREE.Color(1, 1, 1);
            }
            this.colors.push(color.r, color.g, color.b);
        });
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(this.points, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(this.colors, 3));
        const material = new THREE.PointsMaterial({ size: 0.05, vertexColors: true });
        this.pointCloud = new THREE.Points(geometry, material);
        this.scene.add(this.pointCloud);
    }
    depthToColor(normalizedDepth) {
        const hue = (1 - normalizedDepth) * 0.7;
        return new THREE.Color().setHSL(hue, 1, 0.5);
    }
    heightToColor(normalizedHeight) {
        const clampedHeight = Math.max(0, Math.min(1, normalizedHeight));
        if (clampedHeight < 0.5) {
            return new THREE.Color().setHSL(0.6, 1, 0.3 + clampedHeight * 0.4);
        } else {
            return new THREE.Color().setHSL(0.3, 1, 0.5 + (clampedHeight - 0.5) * 0.5);
        }
    }
    updateTrajectory(trajectoryData) {
        if (this.trajectoryLine) {
            this.scene.remove(this.trajectoryLine);
        }
        const trajectoryPoints = trajectoryData.map(point => new THREE.Vector3(point.position[0], point.position[1], point.position[2]));
        const geometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints);
        const material = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 3 });
        this.trajectoryLine = new THREE.Line(geometry, material);
        this.scene.add(this.trajectoryLine);
    }
    updateCurrentPose(poseMatrix) {
        if (this.currentPoseMarker) {
            this.scene.remove(this.currentPoseMarker);
        }
        const position = new THREE.Vector3(poseMatrix[0][3], poseMatrix[1][3], poseMatrix[2][3]);
        const markerGeometry = new THREE.ConeGeometry(0.2, 0.5, 8);
        const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
        this.currentPoseMarker = new THREE.Mesh(markerGeometry, markerMaterial);
        this.currentPoseMarker.position.copy(position);
        const rotation = new THREE.Matrix3().setFromMatrix4(new THREE.Matrix4().fromArray(poseMatrix.flat()));
        const quaternion = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().setFromMatrix3(rotation));
        this.currentPoseMarker.setRotationFromQuaternion(quaternion);
        this.scene.add(this.currentPoseMarker);
    }
    onMouseClick(event) {
        if (!this.pointCloud) return;
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObject(this.pointCloud);
        if (intersects.length > 0) {
            const intersection = intersects[0];
            const index = intersection.index;
            const position = new THREE.Vector3(this.points[index * 3], this.points[index * 3 + 1], this.points[index * 3 + 2]);
            this.selectPoint(position, index);
        }
    }
    onMouseMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }
    selectPoint(position, index) {
        if (this.selectedPoint) {
            this.scene.remove(this.selectedPoint);
        }
        const markerGeometry = new THREE.SphereGeometry(0.1, 16, 16);
        const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
        this.selectedPoint = new THREE.Mesh(markerGeometry, markerMaterial);
        this.selectedPoint.position.copy(position);
        this.scene.add(this.selectedPoint);
        if (this.onPointSelect) {
            this.onPointSelect({ position: position, index: index });
        }
    }
    setPointSize(size) {
        if (this.pointCloud) {
            this.pointCloud.material.size = size;
        }
    }
    setColorMode(mode) {
        if (this.lastPointData) {
            this.updatePointCloud(this.lastPointData, mode);
        }
    }
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    resize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.renderer.dispose();
        if (this.container.contains(this.renderer.domElement)) {
            this.container.removeChild(this.renderer.domElement);
        }
    }
}
const PointCloudVisualization = ({ pointCloudData, trajectoryData, currentPose, onPointSelect }) => {
    const containerRef = useRef();
    const rendererRef = useRef();
    const [colorMode, setColorMode] = useState('depth');
    const [pointSize, setPointSize] = useState(0.05);
    const [selectedPointInfo, setSelectedPointInfo] = useState(null);
    useEffect(() => {
        if (containerRef.current && !rendererRef.current) {
            rendererRef.current = new PointCloudRenderer(containerRef.current);
            rendererRef.current.onPointSelect = (pointInfo) => {
                setSelectedPointInfo(pointInfo);
                if (onPointSelect) {
                    onPointSelect(pointInfo);
                }
            };
        }
        return () => {
            if (rendererRef.current) {
                rendererRef.current.dispose();
                rendererRef.current = null;
            }
        };
    }, []);
    useEffect(() => {
        if (rendererRef.current && pointCloudData) {
            rendererRef.current.lastPointData = pointCloudData;
            rendererRef.current.updatePointCloud(pointCloudData, colorMode);
        }
    }, [pointCloudData, colorMode]);
    useEffect(() => {
        if (rendererRef.current && trajectoryData) {
            rendererRef.current.updateTrajectory(trajectoryData);
        }
    }, [trajectoryData]);
    useEffect(() => {
        if (rendererRef.current && currentPose) {
            rendererRef.current.updateCurrentPose(currentPose);
        }
    }, [currentPose]);
    useEffect(() => {
        if (rendererRef.current) {
            rendererRef.current.setPointSize(pointSize);
        }
    }, [pointSize]);
    useEffect(() => {
        const handleResize = () => {
            if (rendererRef.current) {
                rendererRef.current.resize();
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);
    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
            <div style={{ position: 'absolute', top: 10, right: 10, background: 'rgba(0,0,0,0.7)', padding: 10, borderRadius: 5, color: 'white' }}>
                <div style={{ marginBottom: 10 }}>
                    <label>Color Mode:</label>
                    <select value={colorMode} onChange={(e) => setColorMode(e.target.value)} style={{ marginLeft: 5, padding: 2 }}>
                        <option value="depth">Depth</option>
                        <option value="height">Height</option>
                        <option value="intensity">Intensity</option>
                    </select>
                </div>
                <div style={{ marginBottom: 10 }}>
                    <label>Point Size:</label>
                    <input type="range" min="0.01" max="0.2" step="0.01" value={pointSize} onChange={(e) => setPointSize(parseFloat(e.target.value))} style={{ marginLeft: 5, width: 100 }} />
                    <span style={{ marginLeft: 5 }}>{pointSize.toFixed(2)}</span>
                </div>
                {selectedPointInfo && (
                    <div style={{ marginTop: 10, padding: 5, background: 'rgba(255,255,255,0.1)', borderRadius: 3 }}>
                        <div>Selected Point:</div>
                        <div>X: {selectedPointInfo.position.x.toFixed(3)}</div>
                        <div>Y: {selectedPointInfo.position.y.toFixed(3)}</div>
                        <div>Z: {selectedPointInfo.position.z.toFixed(3)}</div>
                        <div>Index: {selectedPointInfo.index}</div>
                    </div>
                )}
            </div>
        </div>
    );
};
export default PointCloudVisualization;