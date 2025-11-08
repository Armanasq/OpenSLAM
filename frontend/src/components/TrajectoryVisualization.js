import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
class TrajectoryRenderer {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.controls = null;
        this.trajectoryLine = null;
        this.groundTruthLine = null;
        this.trajectoryPoints = [];
        this.groundTruthPoints = [];
        this.isPlaying = false;
        this.currentFrame = 0;
        this.animationId = null;
        this.init();
    }
    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setClearColor(0x222222);
        this.container.appendChild(this.renderer.domElement);
        this.camera.position.set(10, 10, 10);
        this.camera.lookAt(0, 0, 0);
        this.setupControls();
        this.setupLighting();
        this.setupGrid();
        this.animate();
    }
    setupControls() {
        const OrbitControls = require('three/examples/jsm/controls/OrbitControls').OrbitControls;
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableZoom = true;
        this.controls.enablePan = true;
    }
    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);
    }
    setupGrid() {
        const gridHelper = new THREE.GridHelper(100, 100, 0x444444, 0x444444);
        this.scene.add(gridHelper);
        const axesHelper = new THREE.AxesHelper(5);
        this.scene.add(axesHelper);
    }
    updateTrajectory(trajectoryData) {
        if (this.trajectoryLine) {
            this.scene.remove(this.trajectoryLine);
        }
        this.trajectoryPoints = trajectoryData.map(point => new THREE.Vector3(point.position[0], point.position[1], point.position[2]));
        const geometry = new THREE.BufferGeometry().setFromPoints(this.trajectoryPoints);
        const material = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 });
        this.trajectoryLine = new THREE.Line(geometry, material);
        this.scene.add(this.trajectoryLine);
        this.addTrajectoryMarkers();
    }
    updateGroundTruth(groundTruthData) {
        if (this.groundTruthLine) {
            this.scene.remove(this.groundTruthLine);
        }
        this.groundTruthPoints = groundTruthData.map(point => new THREE.Vector3(point.position[0], point.position[1], point.position[2]));
        const geometry = new THREE.BufferGeometry().setFromPoints(this.groundTruthPoints);
        const material = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 });
        this.groundTruthLine = new THREE.Line(geometry, material);
        this.scene.add(this.groundTruthLine);
    }
    addTrajectoryMarkers() {
        const markerGeometry = new THREE.SphereGeometry(0.1, 8, 8);
        const markerMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
        this.trajectoryPoints.forEach((point, index) => {
            if (index % 10 === 0) {
                const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                marker.position.copy(point);
                marker.userData = { frameIndex: index };
                this.scene.add(marker);
            }
        });
    }
    setCameraPosition(position, target) {
        this.camera.position.set(position.x, position.y, position.z);
        if (target) {
            this.camera.lookAt(target.x, target.y, target.z);
            this.controls.target.set(target.x, target.y, target.z);
        }
        this.controls.update();
    }
    zoomToFit() {
        if (this.trajectoryPoints.length === 0) return;
        const box = new THREE.Box3().setFromPoints(this.trajectoryPoints);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const distance = maxDim * 2;
        this.camera.position.set(center.x + distance, center.y + distance, center.z + distance);
        this.camera.lookAt(center);
        this.controls.target.copy(center);
        this.controls.update();
    }
    startPlayback() {
        this.isPlaying = true;
        this.playbackAnimation();
    }
    stopPlayback() {
        this.isPlaying = false;
    }
    seekToFrame(frameIndex) {
        this.currentFrame = Math.max(0, Math.min(frameIndex, this.trajectoryPoints.length - 1));
        this.updatePlaybackMarker();
    }
    playbackAnimation() {
        if (!this.isPlaying) return;
        this.currentFrame = (this.currentFrame + 1) % this.trajectoryPoints.length;
        this.updatePlaybackMarker();
        setTimeout(() => this.playbackAnimation(), 100);
    }
    updatePlaybackMarker() {
        if (this.playbackMarker) {
            this.scene.remove(this.playbackMarker);
        }
        if (this.currentFrame < this.trajectoryPoints.length) {
            const markerGeometry = new THREE.SphereGeometry(0.2, 16, 16);
            const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
            this.playbackMarker = new THREE.Mesh(markerGeometry, markerMaterial);
            this.playbackMarker.position.copy(this.trajectoryPoints[this.currentFrame]);
            this.scene.add(this.playbackMarker);
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
const TrajectoryVisualization = ({ trajectoryData, groundTruthData, onFrameSelect }) => {
    const containerRef = useRef();
    const rendererRef = useRef();
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentFrame, setCurrentFrame] = useState(0);
    const [cameraPreset, setCameraPreset] = useState('default');
    useEffect(() => {
        if (containerRef.current && !rendererRef.current) {
            rendererRef.current = new TrajectoryRenderer(containerRef.current);
        }
        return () => {
            if (rendererRef.current) {
                rendererRef.current.dispose();
                rendererRef.current = null;
            }
        };
    }, []);
    useEffect(() => {
        if (rendererRef.current && trajectoryData) {
            rendererRef.current.updateTrajectory(trajectoryData);
        }
    }, [trajectoryData]);
    useEffect(() => {
        if (rendererRef.current && groundTruthData) {
            rendererRef.current.updateGroundTruth(groundTruthData);
        }
    }, [groundTruthData]);
    useEffect(() => {
        const handleResize = () => {
            if (rendererRef.current) {
                rendererRef.current.resize();
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);
    const handlePlayPause = () => {
        if (rendererRef.current) {
            if (isPlaying) {
                rendererRef.current.stopPlayback();
            } else {
                rendererRef.current.startPlayback();
            }
            setIsPlaying(!isPlaying);
        }
    };
    const handleFrameSeek = (frameIndex) => {
        if (rendererRef.current) {
            rendererRef.current.seekToFrame(frameIndex);
            setCurrentFrame(frameIndex);
            if (onFrameSelect) {
                onFrameSelect(frameIndex);
            }
        }
    };
    const handleCameraPreset = (preset) => {
        if (!rendererRef.current) return;
        setCameraPreset(preset);
        switch (preset) {
            case 'top':
                rendererRef.current.setCameraPosition({ x: 0, y: 50, z: 0 }, { x: 0, y: 0, z: 0 });
                break;
            case 'side':
                rendererRef.current.setCameraPosition({ x: 50, y: 0, z: 0 }, { x: 0, y: 0, z: 0 });
                break;
            case 'front':
                rendererRef.current.setCameraPosition({ x: 0, y: 0, z: 50 }, { x: 0, y: 0, z: 0 });
                break;
            case 'fit':
                rendererRef.current.zoomToFit();
                break;
            default:
                rendererRef.current.setCameraPosition({ x: 10, y: 10, z: 10 }, { x: 0, y: 0, z: 0 });
        }
    };
    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
            <div style={{ position: 'absolute', top: 10, left: 10, background: 'rgba(0,0,0,0.7)', padding: 10, borderRadius: 5 }}>
                <div style={{ marginBottom: 10 }}>
                    <button onClick={handlePlayPause} style={{ marginRight: 10, padding: '5px 10px', background: '#007bff', color: 'white', border: 'none', borderRadius: 3 }}>
                        {isPlaying ? 'Pause' : 'Play'}
                    </button>
                    <input type="range" min="0" max={trajectoryData ? trajectoryData.length - 1 : 0} value={currentFrame} onChange={(e) => handleFrameSeek(parseInt(e.target.value))} style={{ width: 200 }} />
                    <span style={{ color: 'white', marginLeft: 10 }}>Frame: {currentFrame}</span>
                </div>
                <div>
                    <label style={{ color: 'white', marginRight: 10 }}>Camera:</label>
                    <select value={cameraPreset} onChange={(e) => handleCameraPreset(e.target.value)} style={{ padding: 5, marginRight: 5 }}>
                        <option value="default">Default</option>
                        <option value="top">Top View</option>
                        <option value="side">Side View</option>
                        <option value="front">Front View</option>
                        <option value="fit">Fit to View</option>
                    </select>
                </div>
            </div>
        </div>
    );
};
export default TrajectoryVisualization;