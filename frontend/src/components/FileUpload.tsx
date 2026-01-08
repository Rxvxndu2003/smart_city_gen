import toast from 'react-hot-toast';

import { useState } from 'react';
import { Upload, FileText, Download, Trash2, Loader } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface FileUploadProps {
  projectId: number;
  onUploadComplete?: (files: any[]) => void;
  accept?: string;
  maxSizeMB?: number;
}

interface UploadedFile {
  filename: string;
  stored_name: string;
  size: number;
  file_path: string;
}

const FileUpload = ({ 
  projectId, 
  onUploadComplete, 
  accept = "*", 
  maxSizeMB = 50 
}: FileUploadProps) => {
  const [uploading, setUploading] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/uploads/list/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      }
    } catch (err) {
      console.error('Failed to load files:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;

    const fileList = Array.from(e.target.files);
    setUploading(true);

    try {
      const uploadPromises = fileList.map(async (file) => {
        // Check file size
        if (file.size > maxSizeMB * 1024 * 1024) {
          toast.error(`${file.name} exceeds ${maxSizeMB}MB limit`);
          return null;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId.toString());

        const response = await fetch(`${API_BASE_URL}/uploads/upload`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });

        if (!response.ok) throw new Error('Upload failed');
        return response.json();
      });

      const uploadedFiles = await Promise.all(uploadPromises);
      const validFiles = uploadedFiles.filter(f => f !== null);
      
      setFiles(prev => [...prev, ...validFiles]);
      onUploadComplete?.(validFiles);
      
      // Reset input
      e.target.value = '';
    } catch (err) {
      console.error('Upload failed:', err);
      toast.error('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      const response = await fetch(
        `${API_BASE_URL}/uploads/delete/${projectId}/${filename}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.ok) {
        setFiles(prev => prev.filter(f => f.filename !== filename));
      }
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Failed to delete file');
    }
  };

  const handleDownload = (filename: string) => {
    const url = `${API_BASE_URL}/uploads/download/${projectId}/${filename}`;
    const token = localStorage.getItem('token');
    
    fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
      .then(response => response.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
      })
      .catch(err => {
        console.error('Download failed:', err);
        toast.error('Failed to download file');
      });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-500 transition-colors">
        <input
          type="file"
          multiple
          accept={accept}
          onChange={handleUpload}
          className="hidden"
          id={`file-upload-${projectId}`}
          disabled={uploading}
        />
        <label htmlFor={`file-upload-${projectId}`} className="cursor-pointer">
          {uploading ? (
            <Loader className="mx-auto h-12 w-12 text-primary-600 animate-spin" />
          ) : (
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
          )}
          <p className="mt-2 text-sm font-medium text-gray-900">
            {uploading ? 'Uploading...' : 'Click to upload files'}
          </p>
          <p className="text-xs text-gray-500">
            or drag and drop (max {maxSizeMB}MB per file)
          </p>
        </label>
      </div>

      {/* File List */}
      {loading ? (
        <div className="text-center py-4">
          <Loader className="h-6 w-6 animate-spin mx-auto text-gray-400" />
        </div>
      ) : files.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-700">Uploaded Files</h4>
          {files.map((file, idx) => (
            <div 
              key={idx} 
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-3 flex-1">
                <FileText className="h-5 w-5 text-gray-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.filename}
                  </p>
                  {file.size && (
                    <p className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleDownload(file.filename)}
                  className="p-1 text-blue-600 hover:text-blue-800"
                  title="Download"
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(file.filename)}
                  className="p-1 text-red-600 hover:text-red-800"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4 text-sm text-gray-500">
          No files uploaded yet
        </div>
      )}

      {/* Load Files Button */}
      {files.length === 0 && !loading && (
        <button
          onClick={loadFiles}
          className="w-full text-sm text-primary-600 hover:text-primary-800"
        >
          Load existing files
        </button>
      )}
    </div>
  );
};

export default FileUpload;
