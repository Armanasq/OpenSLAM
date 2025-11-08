import React, { useState, useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Editor from '@monaco-editor/react';
class TutorialStep {
    constructor(id, title, content, codeExample, expectedOutput, hints) {
        this.id = id;
        this.title = title;
        this.content = content;
        this.codeExample = codeExample;
        this.expectedOutput = expectedOutput;
        this.hints = hints || [];
        this.completed = false;
        this.userCode = codeExample;
        this.executionResult = null;
    }
}
class TutorialManager {
    constructor() {
        this.tutorials = {};
        this.currentTutorial = null;
        this.currentStep = 0;
        this.progress = {};
        this.initializeTutorials();
    }
    initializeTutorials() {
        this.tutorials['feature_detection'] = {
            id: 'feature_detection',
            title: 'Feature Detection and Matching',
            description: 'Learn how to detect and match features in images for visual SLAM',
            steps: [
                new TutorialStep('fd_1', 'Introduction to Feature Detection', 'Feature detection is the foundation of visual SLAM. Features are distinctive points in images that can be reliably detected and matched across different frames.', 'import cv2\nimport numpy as np\n\n# Load an image\nimage = cv2.imread("sample_image.jpg", cv2.IMREAD_GRAYSCALE)\nprint(f"Image shape: {image.shape}")', 'Image shape: (480, 640)', ['Make sure the image path is correct', 'Use grayscale images for feature detection']),
                new TutorialStep('fd_2', 'ORB Feature Detector', 'ORB (Oriented FAST and Rotated BRIEF) is a fast and efficient feature detector that combines FAST keypoint detector with BRIEF descriptor.', 'import cv2\n\n# Create ORB detector\norb = cv2.ORB_create(nfeatures=1000)\n\n# Detect keypoints and compute descriptors\nkeypoints, descriptors = orb.detectAndCompute(image, None)\n\nprint(f"Number of keypoints: {len(keypoints)}")\nprint(f"Descriptor shape: {descriptors.shape}")', 'Number of keypoints: 1000\nDescriptor shape: (1000, 32)', ['Adjust nfeatures parameter to control number of detected features', 'ORB descriptors are binary (32 bytes per descriptor)']),
                new TutorialStep('fd_3', 'Feature Matching', 'Feature matching finds correspondences between keypoints in different images using descriptor similarity.', 'import cv2\n\n# Create BF matcher for ORB descriptors\nbf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)\n\n# Match descriptors between two images\nmatches = bf.match(descriptors1, descriptors2)\n\n# Sort matches by distance\nmatches = sorted(matches, key=lambda x: x.distance)\n\nprint(f"Number of matches: {len(matches)}")\nprint(f"Best match distance: {matches[0].distance}")', 'Number of matches: 245\nBest match distance: 12', ['Use NORM_HAMMING for binary descriptors like ORB', 'Lower distance means better match'])
            ]
        };
        this.tutorials['visual_odometry'] = {
            id: 'visual_odometry',
            title: 'Visual Odometry Implementation',
            description: 'Implement a basic visual odometry system using feature tracking',
            steps: [
                new TutorialStep('vo_1', 'Camera Calibration', 'Camera calibration provides intrinsic parameters needed for 3D reconstruction from 2D images.', 'import numpy as np\n\n# Camera intrinsic matrix (example values)\nK = np.array([[718.856, 0, 607.1928],\n              [0, 718.856, 185.2157],\n              [0, 0, 1]])\n\nprint("Camera matrix:")\nprint(K)', 'Camera matrix:\n[[718.856   0.    607.1928]\n [  0.    718.856 185.2157]\n [  0.      0.      1.    ]]', ['Focal length is in pixels', 'Principal point is usually near image center']),
                new TutorialStep('vo_2', 'Essential Matrix Estimation', 'The essential matrix encodes the relative pose between two camera views.', 'import cv2\nimport numpy as np\n\n# Estimate essential matrix from matched points\nE, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)\n\nprint(f"Essential matrix shape: {E.shape}")\nprint(f"Inlier ratio: {np.sum(mask) / len(mask):.2f}")', 'Essential matrix shape: (3, 3)\nInlier ratio: 0.85', ['RANSAC helps remove outliers', 'Higher inlier ratio indicates better matches']),
                new TutorialStep('vo_3', 'Pose Recovery', 'Recover relative rotation and translation from the essential matrix.', 'import cv2\n\n# Recover pose from essential matrix\nretval, R, t, mask = cv2.recoverPose(E, pts1, pts2, K)\n\nprint(f"Rotation matrix:")\nprint(R)\nprint(f"Translation vector: {t.flatten()}")', 'Rotation matrix:\n[[ 0.999  0.001 -0.045]\n [-0.001  1.000  0.002]\n [ 0.045 -0.002  0.999]]\nTranslation vector: [-0.123  0.045  0.987]', ['Translation is up to scale', 'Rotation matrix should be orthogonal'])
            ]
        };
        this.tutorials['loop_closure'] = {
            id: 'loop_closure',
            title: 'Loop Closure Detection',
            description: 'Implement loop closure detection to reduce drift in SLAM systems',
            steps: [
                new TutorialStep('lc_1', 'Bag of Words', 'Bag of Words creates a vocabulary of visual words for efficient place recognition.', 'import numpy as np\nfrom sklearn.cluster import KMeans\n\n# Create vocabulary from descriptors\nall_descriptors = np.vstack([desc1, desc2, desc3])  # Combine all descriptors\nkmeans = KMeans(n_clusters=1000, random_state=42)\nvocabulary = kmeans.fit(all_descriptors)\n\nprint(f"Vocabulary size: {len(vocabulary.cluster_centers_)}")', 'Vocabulary size: 1000', ['Larger vocabulary provides better discrimination', 'Use k-means clustering to create visual words']),
                new TutorialStep('lc_2', 'Image Similarity', 'Compute similarity between images using bag of words histograms.', 'from sklearn.metrics.pairwise import cosine_similarity\n\n# Convert descriptors to bag of words\nhist1 = compute_bow_histogram(descriptors1, vocabulary)\nhist2 = compute_bow_histogram(descriptors2, vocabulary)\n\n# Compute similarity\nsimilarity = cosine_similarity([hist1], [hist2])[0][0]\n\nprint(f"Image similarity: {similarity:.3f}")', 'Image similarity: 0.847', ['Cosine similarity ranges from 0 to 1', 'Higher values indicate more similar images']),
                new TutorialStep('lc_3', 'Loop Detection', 'Detect loops by finding images with high similarity to current frame.', 'def detect_loop(current_histogram, database, threshold=0.8):\n    similarities = []\n    for hist in database:\n        sim = cosine_similarity([current_histogram], [hist])[0][0]\n        similarities.append(sim)\n    \n    max_sim = max(similarities)\n    if max_sim > threshold:\n        return similarities.index(max_sim), max_sim\n    return None, max_sim\n\nloop_id, similarity = detect_loop(current_hist, image_database)\nprint(f"Loop detected: {loop_id is not None}, Similarity: {similarity:.3f}")', 'Loop detected: True, Similarity: 0.892', ['Use threshold to control false positive rate', 'Consider temporal constraints to avoid recent matches'])
            ]
        };
    }
    getTutorial(tutorialId) {
        return this.tutorials[tutorialId];
    }
    listTutorials() {
        return Object.values(this.tutorials).map(t => ({
            id: t.id,
            title: t.title,
            description: t.description,
            steps: t.steps.length,
            completed: this.getTutorialProgress(t.id).completed
        }));
    }
    getTutorialProgress(tutorialId) {
        if (!this.progress[tutorialId]) {
            this.progress[tutorialId] = {
                currentStep: 0,
                completedSteps: [],
                completed: false,
                startedAt: null,
                completedAt: null
            };
        }
        return this.progress[tutorialId];
    }
    startTutorial(tutorialId) {
        this.currentTutorial = tutorialId;
        this.currentStep = 0;
        const progress = this.getTutorialProgress(tutorialId);
        if (!progress.startedAt) {
            progress.startedAt = new Date();
        }
    }
    completeStep(tutorialId, stepIndex) {
        const progress = this.getTutorialProgress(tutorialId);
        if (!progress.completedSteps.includes(stepIndex)) {
            progress.completedSteps.push(stepIndex);
        }
        const tutorial = this.getTutorial(tutorialId);
        if (tutorial && progress.completedSteps.length === tutorial.steps.length) {
            progress.completed = true;
            progress.completedAt = new Date();
        }
    }
}
const CodeEditor = ({ code, onChange, onExecute, executionResult, isExecuting }) => {
    const [localCode, setLocalCode] = useState(code);
    const editorRef = useRef(null);
    useEffect(() => {
        setLocalCode(code);
    }, [code]);
    const handleCodeChange = (value) => {
        const newCode = value || '';
        setLocalCode(newCode);
        if (onChange) {
            onChange(newCode);
        }
    };
    return (
        <div style={{ border: '1px solid #ddd', borderRadius: 4, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ background: '#f5f5f5', padding: 10, borderBottom: '1px solid #ddd', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold' }}>Code Editor</span>
                <button onClick={() => onExecute(localCode)} disabled={isExecuting} style={{ padding: '5px 15px', background: '#007bff', color: 'white', border: 'none', borderRadius: 3, cursor: isExecuting ? 'not-allowed' : 'pointer' }}>
                    {isExecuting ? 'Executing...' : 'Run Code'}
                </button>
            </div>
            <div style={{ height: 200, width: '100%' }}>
                <Editor
                    height="200px"
                    language="python"
                    value={localCode || ''}
                    onChange={handleCodeChange}
                    theme="vs"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                        lineNumbers: 'on',
                        roundedSelection: false,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                        insertSpaces: true,
                        wordWrap: 'on',
                        formatOnPaste: true,
                        formatOnType: true,
                        suggestOnTriggerCharacters: true,
                        acceptSuggestionOnCommitCharacter: true,
                        acceptSuggestionOnEnter: 'on',
                        snippetSuggestions: 'top',
                        tabCompletion: 'on',
                        wordBasedSuggestions: 'allDocuments',
                        quickSuggestions: {
                            other: true,
                            comments: false,
                            strings: false
                        },
                        parameterHints: {
                            enabled: true
                        },
                        hover: {
                            enabled: true
                        },
                        contextmenu: true,
                        multiCursorModifier: 'ctrlCmd',
                        bracketPairColorization: {
                            enabled: true
                        },
                        guides: {
                            indentation: true,
                            bracketPairs: true
                        }
                    }}
                />
            </div>
            {executionResult && (
                <div style={{ background: executionResult.success ? '#d4edda' : '#f8d7da', padding: 10, borderTop: '1px solid #ddd' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: 5, color: executionResult.success ? '#155724' : '#721c24' }}>
                        {executionResult.success ? 'Execution Successful' : 'Execution Error'}
                    </div>
                    {executionResult.output && (
                        <pre style={{ margin: 0, fontSize: 12, color: '#333' }}>{executionResult.output}</pre>
                    )}
                    {executionResult.error && (
                        <pre style={{ margin: 0, fontSize: 12, color: '#721c24' }}>{executionResult.error}</pre>
                    )}
                </div>
            )}
        </div>
    );
};
const TutorialInterface = ({ onTutorialComplete, onStepComplete, isDarkMode }) => {
    const [activeTab, setActiveTab] = useState('tutorials');
    const [tutorialManager] = useState(new TutorialManager());
    const [selectedTutorial, setSelectedTutorial] = useState(null);
    const [currentStep, setCurrentStep] = useState(0);
    const [userCode, setUserCode] = useState('');
    const [executionResult, setExecutionResult] = useState(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const [showHints, setShowHints] = useState(false);
    const [tutorials, setTutorials] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    useEffect(() => {
        setTutorials(tutorialManager.listTutorials());
    }, [tutorialManager]);
    const handleTutorialSelect = (tutorialId) => {
        const tutorial = tutorialManager.getTutorial(tutorialId);
        setSelectedTutorial(tutorial);
        setCurrentStep(0);
        setUserCode(tutorial.steps[0].codeExample);
        setExecutionResult(null);
        setShowHints(false);
        tutorialManager.startTutorial(tutorialId);
    };
    const handleStepNavigation = (stepIndex) => {
        if (selectedTutorial && stepIndex >= 0 && stepIndex < selectedTutorial.steps.length) {
            setCurrentStep(stepIndex);
            setUserCode(selectedTutorial.steps[stepIndex].codeExample);
            setExecutionResult(null);
            setShowHints(false);
        }
    };
    const handleCodeExecution = async (code) => {
        setIsExecuting(true);
        try {
            const response = await fetch('/api/execute-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: code, context: 'tutorial' })
            });
            const result = await response.json();
            setExecutionResult(result);
            if (result.success && selectedTutorial) {
                const step = selectedTutorial.steps[currentStep];
                const isCorrect = result.output.trim() === step.expectedOutput.trim();
                if (isCorrect) {
                    tutorialManager.completeStep(selectedTutorial.id, currentStep);
                    if (onStepComplete) {
                        onStepComplete(selectedTutorial.id, currentStep);
                    }
                }
            }
        } catch (error) {
            setExecutionResult({ success: false, error: error.message });
        } finally {
            setIsExecuting(false);
        }
    };
    const renderTutorialList = () => (
        <div style={{ padding: 20 }}>
            <h2>Available Tutorials</h2>
            <div style={{ display: 'grid', gap: 20, gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
                {tutorials.map(tutorial => (
                    <div key={tutorial.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 20, cursor: 'pointer', background: tutorial.completed ? '#e8f5e8' : 'white' }} onClick={() => handleTutorialSelect(tutorial.id)}>
                        <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>{tutorial.title}</h3>
                        <p style={{ margin: '0 0 15px 0', color: '#666', fontSize: 14 }}>{tutorial.description}</p>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: '#888' }}>
                            <span>{tutorial.steps} steps</span>
                            {tutorial.completed && <span style={{ color: '#28a745', fontWeight: 'bold' }}>✓ Completed</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
    const renderTutorialContent = () => {
        if (!selectedTutorial) return null;
        const step = selectedTutorial.steps[currentStep];
        const progress = tutorialManager.getTutorialProgress(selectedTutorial.id);
        return (
            <div style={{ display: 'flex', height: '100vh' }}>
                <div style={{ width: '50%', padding: 20, borderRight: '1px solid #ddd', overflow: 'auto' }}>
                    <div style={{ marginBottom: 20 }}>
                        <button onClick={() => setSelectedTutorial(null)} style={{ padding: '5px 10px', background: '#6c757d', color: 'white', border: 'none', borderRadius: 3, marginBottom: 10 }}>
                            ← Back to Tutorials
                        </button>
                        <h2 style={{ margin: '0 0 5px 0' }}>{selectedTutorial.title}</h2>
                        <div style={{ fontSize: 14, color: '#666', marginBottom: 15 }}>
                            Step {currentStep + 1} of {selectedTutorial.steps.length}
                        </div>
                        <div style={{ background: '#e9ecef', borderRadius: 4, height: 8, marginBottom: 20 }}>
                            <div style={{ background: '#007bff', height: '100%', borderRadius: 4, width: `${((currentStep + 1) / selectedTutorial.steps.length) * 100}%` }} />
                        </div>
                    </div>
                    <h3>{step.title}</h3>
                    <div style={{ marginBottom: 20, lineHeight: 1.6 }}>
                        {step.content}
                    </div>
                    <div style={{ marginBottom: 20 }}>
                        <h4>Expected Output:</h4>
                        <pre style={{ background: '#f8f9fa', padding: 10, borderRadius: 4, fontSize: 12, border: '1px solid #dee2e6' }}>
                            {step.expectedOutput}
                        </pre>
                    </div>
                    {step.hints.length > 0 && (
                        <div style={{ marginBottom: 20 }}>
                            <button onClick={() => setShowHints(!showHints)} style={{ padding: '5px 10px', background: '#ffc107', color: '#212529', border: 'none', borderRadius: 3, marginBottom: 10 }}>
                                {showHints ? 'Hide Hints' : 'Show Hints'}
                            </button>
                            {showHints && (
                                <ul style={{ background: '#fff3cd', padding: 15, borderRadius: 4, border: '1px solid #ffeaa7' }}>
                                    {step.hints.map((hint, index) => (
                                        <li key={index} style={{ marginBottom: 5 }}>{hint}</li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )}
                    <div style={{ display: 'flex', gap: 10 }}>
                        <button onClick={() => handleStepNavigation(currentStep - 1)} disabled={currentStep === 0} style={{ padding: '8px 15px', background: currentStep === 0 ? '#6c757d' : '#007bff', color: 'white', border: 'none', borderRadius: 3 }}>
                            Previous
                        </button>
                        <button onClick={() => handleStepNavigation(currentStep + 1)} disabled={currentStep === selectedTutorial.steps.length - 1} style={{ padding: '8px 15px', background: currentStep === selectedTutorial.steps.length - 1 ? '#6c757d' : '#007bff', color: 'white', border: 'none', borderRadius: 3 }}>
                            Next
                        </button>
                    </div>
                </div>
                <div style={{ width: '50%', padding: 20, display: 'flex', flexDirection: 'column' }}>
                    <CodeEditor code={userCode} onChange={setUserCode} onExecute={handleCodeExecution} executionResult={executionResult} isExecuting={isExecuting} />
                    <div style={{ marginTop: 20, flex: 1 }}>
                        <h4>Reference Code:</h4>
                        <SyntaxHighlighter language="python" style={tomorrow} customStyle={{ fontSize: 12, maxHeight: 300, overflow: 'auto' }}>
                            {step.codeExample}
                        </SyntaxHighlighter>
                    </div>
                </div>
            </div>
        );
    };
    const renderTutorialsTab = () => (
        <div style={{ padding: '20px' }}>
            <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '20px', alignItems: 'center' }}>
                    <input
                        type="text"
                        placeholder="Search tutorials..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            flex: 1,
                            padding: '10px 16px',
                            border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                            borderRadius: '8px',
                            background: isDarkMode ? '#334155' : 'white',
                            color: isDarkMode ? '#e2e8f0' : '#1e293b',
                            fontSize: '0.9rem'
                        }}
                    />
                    <select style={{
                        padding: '10px 16px',
                        border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                        borderRadius: '8px',
                        background: isDarkMode ? '#334155' : 'white',
                        color: isDarkMode ? '#e2e8f0' : '#1e293b',
                        fontSize: '0.9rem'
                    }}>
                        <option>All Levels</option>
                        <option>Beginner</option>
                        <option>Intermediate</option>
                        <option>Advanced</option>
                    </select>
                </div>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: '20px'
            }}>
                {tutorials.filter(tutorial => 
                    tutorial.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    tutorial.description.toLowerCase().includes(searchQuery.toLowerCase())
                ).map(tutorial => (
                    <div key={tutorial.id} style={{
                        background: isDarkMode ? '#1a1a1a' : 'white',
                        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                        borderRadius: '12px',
                        padding: '20px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: isDarkMode 
                            ? '0 1px 3px rgba(0,0,0,0.3)' 
                            : '0 1px 3px rgba(0,0,0,0.1)'
                    }}
                    onClick={() => handleTutorialSelect(tutorial.id)}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = isDarkMode 
                            ? '0 4px 12px rgba(0,0,0,0.4)' 
                            : '0 4px 12px rgba(0,0,0,0.15)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = isDarkMode 
                            ? '0 1px 3px rgba(0,0,0,0.3)' 
                            : '0 1px 3px rgba(0,0,0,0.1)';
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                            <h3 style={{ 
                                margin: '0 0 4px 0', 
                                fontSize: '1.1rem', 
                                fontWeight: '600',
                                color: isDarkMode ? '#e2e8f0' : '#1e293b'
                            }}>
                                {tutorial.title}
                            </h3>
                            {tutorial.completed && (
                                <span style={{
                                    fontSize: '0.8rem',
                                    color: '#22c55e',
                                    background: isDarkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)',
                                    padding: '2px 8px',
                                    borderRadius: '12px',
                                    fontWeight: '500'
                                }}>
                                    ✓ Completed
                                </span>
                            )}
                        </div>

                        <p style={{
                            margin: '0 0 16px 0',
                            fontSize: '0.85rem',
                            color: isDarkMode ? '#94a3b8' : '#64748b',
                            lineHeight: '1.4'
                        }}>
                            {tutorial.description}
                        </p>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ 
                                fontSize: '0.8rem', 
                                color: isDarkMode ? '#94a3b8' : '#64748b' 
                            }}>
                                {tutorial.steps} steps
                            </span>
                            <button style={{
                                padding: '6px 12px',
                                background: '#4f46e5',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontSize: '0.8rem',
                                fontWeight: '500',
                                cursor: 'pointer'
                            }}>
                                Start Tutorial
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderProgressTab = () => (
        <div style={{ padding: '20px' }}>
            <div style={{ marginBottom: '24px' }}>
                <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    Learning Progress
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    <div style={{
                        background: isDarkMode ? '#1a1a1a' : 'white',
                        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                        borderRadius: '8px',
                        padding: '16px',
                        textAlign: 'center'
                    }}>
                        <div style={{ fontSize: '2rem', fontWeight: '600', color: '#4f46e5', marginBottom: '4px' }}>
                            {tutorials.filter(t => t.completed).length}
                        </div>
                        <div style={{ fontSize: '0.9rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                            Completed Tutorials
                        </div>
                    </div>
                    
                    <div style={{
                        background: isDarkMode ? '#1a1a1a' : 'white',
                        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                        borderRadius: '8px',
                        padding: '16px',
                        textAlign: 'center'
                    }}>
                        <div style={{ fontSize: '2rem', fontWeight: '600', color: '#22c55e', marginBottom: '4px' }}>
                            {Math.round((tutorials.filter(t => t.completed).length / tutorials.length) * 100) || 0}%
                        </div>
                        <div style={{ fontSize: '0.9rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                            Overall Progress
                        </div>
                    </div>
                </div>
            </div>

            <div style={{
                background: isDarkMode ? '#1a1a1a' : 'white',
                border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                borderRadius: '8px',
                padding: '20px'
            }}>
                <h4 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    Tutorial Progress
                </h4>
                
                {tutorials.map(tutorial => (
                    <div key={tutorial.id} style={{ marginBottom: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.9rem', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                                {tutorial.title}
                            </span>
                            <span style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                                {tutorial.completed ? 'Completed' : 'In Progress'}
                            </span>
                        </div>
                        <div style={{
                            height: '8px',
                            background: isDarkMode ? '#334155' : '#e2e8f0',
                            borderRadius: '4px',
                            overflow: 'hidden'
                        }}>
                            <div style={{
                                height: '100%',
                                width: tutorial.completed ? '100%' : '0%',
                                background: tutorial.completed ? '#22c55e' : '#4f46e5',
                                borderRadius: '4px',
                                transition: 'width 0.3s ease'
                            }} />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderResourcesTab = () => (
        <div style={{ padding: '20px' }}>
            <div style={{ marginBottom: '24px' }}>
                <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    Learning Resources
                </h3>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
                <div style={{
                    background: isDarkMode ? '#1a1a1a' : 'white',
                    border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                    borderRadius: '8px',
                    padding: '20px'
                }}>
                    <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                        📚 Documentation
                    </h4>
                    <ul style={{ margin: 0, paddingLeft: '20px', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                        <li>SLAM Fundamentals</li>
                        <li>Algorithm Implementation Guide</li>
                        <li>Dataset Format Specifications</li>
                        <li>Performance Evaluation Metrics</li>
                    </ul>
                </div>

                <div style={{
                    background: isDarkMode ? '#1a1a1a' : 'white',
                    border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                    borderRadius: '8px',
                    padding: '20px'
                }}>
                    <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                        🎥 Video Tutorials
                    </h4>
                    <ul style={{ margin: 0, paddingLeft: '20px', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                        <li>Introduction to Visual SLAM</li>
                        <li>Feature Detection Techniques</li>
                        <li>Loop Closure Detection</li>
                        <li>Performance Optimization</li>
                    </ul>
                </div>

                <div style={{
                    background: isDarkMode ? '#1a1a1a' : 'white',
                    border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                    borderRadius: '8px',
                    padding: '20px'
                }}>
                    <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                        📖 Research Papers
                    </h4>
                    <ul style={{ margin: 0, paddingLeft: '20px', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                        <li>ORB-SLAM3 Paper</li>
                        <li>VINS-Mono Paper</li>
                        <li>LIO-SAM Paper</li>
                        <li>DSO Paper</li>
                    </ul>
                </div>
            </div>
        </div>
    );

    return (
        <div style={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            background: isDarkMode ? '#0f0f0f' : '#f8fafc',
            color: isDarkMode ? '#e0e0e0' : '#1e293b'
        }}>
            {selectedTutorial ? (
                renderTutorialContent()
            ) : (
                <>
                    <div style={{
                        padding: '16px 20px',
                        background: isDarkMode ? '#1a1a1a' : 'white',
                        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
                    }}>
                        <h1 style={{ margin: '0 0 4px 0', fontSize: '1.5rem', fontWeight: '600' }}>
                            Interactive Tutorials
                        </h1>
                        <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b', fontSize: '0.9rem' }}>
                            Learn SLAM concepts through hands-on coding exercises
                        </p>
                    </div>

                    <div style={{
                        display: 'flex',
                        background: isDarkMode ? '#1a1a1a' : 'white',
                        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
                    }}>
                        {[
                            { id: 'tutorials', label: 'Available Tutorials', icon: '📚' },
                            { id: 'progress', label: 'My Progress', icon: '📊' },
                            { id: 'resources', label: 'Resources', icon: '🔗' }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                style={{
                                    padding: '12px 20px',
                                    border: 'none',
                                    background: activeTab === tab.id 
                                        ? (isDarkMode ? '#334155' : '#f1f5f9') 
                                        : 'transparent',
                                    color: activeTab === tab.id 
                                        ? (isDarkMode ? '#e2e8f0' : '#4f46e5') 
                                        : (isDarkMode ? '#94a3b8' : '#64748b'),
                                    borderBottom: activeTab === tab.id ? '2px solid #4f46e5' : '2px solid transparent',
                                    cursor: 'pointer',
                                    fontSize: '0.9rem',
                                    fontWeight: '500',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                <span>{tab.icon}</span>
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <div style={{ flex: 1, overflow: 'auto' }}>
                        {activeTab === 'tutorials' && renderTutorialsTab()}
                        {activeTab === 'progress' && renderProgressTab()}
                        {activeTab === 'resources' && renderResourcesTab()}
                    </div>
                </>
            )}
        </div>
    );
};
export default TutorialInterface;