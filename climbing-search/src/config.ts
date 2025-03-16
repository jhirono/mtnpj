/**
 * Application configuration
 */

// R2 Configuration
export const useR2Storage = false; // Set to false to use local files
export const r2AccountId = import.meta.env.VITE_R2_ACCOUNT_ID || '';
export const r2BucketName = import.meta.env.VITE_R2_BUCKET_NAME || '';

// Base URL for data files
export const getDataUrl = (fileName: string): string => {
  if (useR2Storage && r2AccountId && r2BucketName) {
    // Use R2 storage
    return `https://${r2AccountId}.r2.cloudflarestorage.com/${r2BucketName}/${fileName}`;
  } else {
    // Use local storage
    return `/data/${fileName}`;
  }
};

// Index file path
export const indexFilePath = useR2Storage 
  ? getDataUrl('index.json')
  : '/data/index.json'; 