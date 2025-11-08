import React, { useRef, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
const CodeEditor = ({ code, onChange, language = 'python', height = '300px', readOnly = false }) => {
  const editorRef = useRef(null);
  const [isEditorReady, setIsEditorReady] = useState(false);
  const handleEditorDidMount = (editor, monaco) => {
    if (!editor || !monaco) return;
    
    editorRef.current = editor;
    setIsEditorReady(true);
    
    try {
      monaco.editor.defineTheme('dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [],
        colors: {
          'editor.background': '#1a1a1a',
          'editor.foreground': '#e0e0e0',
          'editor.lineHighlightBackground': '#2d2d2d',
          'editor.selectionBackground': '#264f78',
          'editorCursor.foreground': '#ffffff',
          'editorWhitespace.foreground': '#3b3b3b',
          'editorIndentGuide.activeBackground': '#3b3b3b',
          'editorIndentGuide.background': '#2d2d2d'
        }
      });
      
      monaco.editor.defineTheme('light', {
        base: 'vs',
        inherit: true,
        rules: [],
        colors: {
          'editor.background': '#ffffff',
          'editor.foreground': '#1e293b',
          'editor.lineHighlightBackground': '#f8fafc',
          'editor.selectionBackground': '#add6ff',
          'editorCursor.foreground': '#000000',
          'editorWhitespace.foreground': '#e2e8f0',
          'editorIndentGuide.activeBackground': '#e2e8f0',
          'editorIndentGuide.background': '#f1f5f9'
        }
      });
      
      // Ensure proper layout
      requestAnimationFrame(() => {
        if (editor && editor.getModel()) {
          editor.layout();
        }
      });
      
    } catch (error) {
      console.warn('Monaco editor theme setup failed:', error);
    }
  };
  useEffect(() => {
    if (editorRef.current && isEditorReady) {
      try {
        editorRef.current.updateOptions({
          readOnly: readOnly
        });
        editorRef.current.layout();
      } catch (error) {
        console.warn('Monaco editor update failed:', error);
      }
    }
  }, [readOnly, isEditorReady]);

  useEffect(() => {
    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (editorRef.current && isEditorReady) {
          try {
            editorRef.current.layout();
          } catch (error) {
            console.warn('Monaco editor resize failed:', error);
          }
        }
      }, 100);
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(resizeTimeout);
    };
  }, [isEditorReady]);
  return (
    <div style={{ 
      height: height === '100%' ? '100%' : height, 
      width: '100%', 
      border: '1px solid #334155', 
      borderRadius: '8px', 
      overflow: 'hidden',
      position: 'relative'
    }}>
      <Editor
        height="100%"
        language={language}
        value={code || ''}
        onChange={(value) => onChange && onChange(value || '')}
        onMount={handleEditorDidMount}
        theme="dark"
        loading={<div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%',
          background: '#1a1a1a',
          color: '#e0e0e0'
        }}>Loading editor...</div>}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          readOnly: readOnly,
          automaticLayout: false,
          tabSize: 4,
          insertSpaces: true,
          wordWrap: 'on',
          formatOnPaste: false,
          formatOnType: false,
          suggestOnTriggerCharacters: false,
          acceptSuggestionOnCommitCharacter: false,
          acceptSuggestionOnEnter: 'off',
          snippetSuggestions: 'none',
          tabCompletion: 'off',
          wordBasedSuggestions: 'off',
          quickSuggestions: false,
          parameterHints: {
            enabled: false
          },
          hover: {
            enabled: false
          },
          contextmenu: false,
          multiCursorModifier: 'ctrlCmd',
          bracketPairColorization: {
            enabled: false
          },
          guides: {
            indentation: false,
            bracketPairs: false
          },
          scrollbar: {
            vertical: 'auto',
            horizontal: 'auto',
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8
          },
          overviewRulerLanes: 0,
          hideCursorInOverviewRuler: true,
          overviewRulerBorder: false,
          renderLineHighlight: 'none',
          occurrencesHighlight: false,
          selectionHighlight: false,
          codeLens: false,
          folding: false,
          foldingHighlight: false,
          unfoldOnClickAfterEndOfLine: false,
          showUnused: false
        }}
      />
    </div>
  );
};
export default CodeEditor;
