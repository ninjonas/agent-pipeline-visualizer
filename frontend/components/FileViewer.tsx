import { useState, useEffect } from 'react';

interface FileViewerProps {
  stepId: string;
  selectedFile: string | null;
  onFileSelect: (filePath: string) => void;
  onSaveContent: (stepId: string, filePath: string, content: string) => Promise<boolean>;
}

export function FileViewer({ stepId, selectedFile, onFileSelect, onSaveContent }: FileViewerProps) {
  const [files, setFiles] = useState<string[]>([]);
  const [fileContent, setFileContent] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [editableContent, setEditableContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  
  useEffect(() => {
    if (stepId) {
      fetchStepFiles();
    }
  }, [stepId]);
  
  useEffect(() => {
    if (selectedFile) {
      fetchFileContent();
    } else {
      setFileContent('');
      setEditableContent('');
    }
  }, [selectedFile]);
  
  const fetchStepFiles = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/files`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      }
    } catch (error) {
      console.error('Error fetching step files:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const fetchFileContent = async () => {
    if (!selectedFile) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/files?path=${encodeURIComponent(selectedFile)}`);
      if (response.ok) {
        const data = await response.json();
        setFileContent(data.content || '');
        setEditableContent(data.content || '');
      }
    } catch (error) {
      console.error('Error fetching file content:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSaveContent = async () => {
    if (!selectedFile) return;
    
    setSaveStatus('saving');
    const success = await onSaveContent(stepId, selectedFile, editableContent);
    
    if (success) {
      setFileContent(editableContent);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 2000);
      setIsEditing(false);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };
  
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'json':
        return '📊';
      case 'txt':
        return '📝';
      case 'md':
        return '📑';
      case 'csv':
        return '📈';
      case 'py':
        return '🐍';
      case 'js':
      case 'ts':
        return '📜';
      default:
        return '📄';
    }
  };
  
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-3">
        <div className="md:col-span-1 border-r border-gray-200 bg-gray-50">
          <div className="p-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-700">Output Files</h3>
          </div>
          
          <div className="overflow-y-auto max-h-[400px]">
            {isLoading && files.length === 0 ? (
              <div className="flex justify-center items-center py-8">
                <span className="text-gray-500">Loading files...</span>
              </div>
            ) : files.length === 0 ? (
              <div className="flex justify-center items-center py-8">
                <span className="text-gray-500">No output files available</span>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {files.map((file) => (
                  <li 
                    key={file}
                    className={`p-3 cursor-pointer hover:bg-gray-100 ${selectedFile === file ? 'bg-primary-50' : ''}`}
                    onClick={() => onFileSelect(file)}
                  >
                    <div className="flex items-center">
                      <span className="mr-2">{getFileIcon(file)}</span>
                      <span className="text-sm truncate">{file.split('/').pop()}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        <div className="md:col-span-2">
          <div className="flex justify-between items-center p-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-700">
              {selectedFile ? selectedFile.split('/').pop() : 'File Content'}
            </h3>
            
            {selectedFile && (
              <div className="flex space-x-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => {
                        setEditableContent(fileContent);
                        setIsEditing(false);
                      }}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveContent}
                      className="px-3 py-1 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700"
                      disabled={saveStatus === 'saving'}
                    >
                      {saveStatus === 'saving' ? 'Saving...' : 
                       saveStatus === 'success' ? 'Saved!' : 
                       saveStatus === 'error' ? 'Error!' : 'Save'}
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Edit
                  </button>
                )}
              </div>
            )}
          </div>
          
          <div className="p-4 overflow-auto max-h-[400px]">
            {isLoading && selectedFile ? (
              <div className="flex justify-center items-center py-8">
                <span className="text-gray-500">Loading content...</span>
              </div>
            ) : !selectedFile ? (
              <div className="flex justify-center items-center py-8">
                <span className="text-gray-500">Select a file to view its content</span>
              </div>
            ) : isEditing ? (
              <textarea
                value={editableContent}
                onChange={(e) => setEditableContent(e.target.value)}
                className="w-full h-[350px] p-2 font-mono text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            ) : (
              <pre className="whitespace-pre-wrap font-mono text-sm">{fileContent}</pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
