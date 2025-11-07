// 환경변수에서 API URL 가져오기
const API_URL = import.meta.env.VITE_API_URL || '/api';

// Content-Disposition 헤더에서 파일명 추출 (RFC 2231 지원)
function extractFilename(disposition: string | null): string {
  if (!disposition) return 'renamed-file';
  
  // RFC 2231 형식: filename*=UTF-8''encoded-name
  const rfc2231Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (rfc2231Match) {
    try {
      return decodeURIComponent(rfc2231Match[1]);
    } catch (e) {
      console.error('Failed to decode filename:', e);
    }
  }
  
  // 일반 형식: filename="name" 또는 filename=name
  const normalMatch = disposition.match(/filename="?([^";\n]+)"?/i);
  if (normalMatch) {
    return normalMatch[1];
  }
  
  return 'renamed-file';
}

export async function uploadForZip(files: File[]): Promise<{ blob: Blob, filename: string }> {
  const form = new FormData();
  files.forEach(f => form.append('files', f, f.name));
  const url = `${API_URL}/rename?zip=true`;
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  
  const disposition = res.headers.get('content-disposition');
  const filename = extractFilename(disposition);
  const blob = await res.blob();
  
  return { blob, filename };
}

export async function uploadSingleFile(file: File): Promise<{ blob: Blob, filename: string }> {
  const form = new FormData();
  form.append('files', file, file.name);
  const url = `${API_URL}/rename`;
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  
  const disposition = res.headers.get('content-disposition');
  const filename = extractFilename(disposition);
  const blob = await res.blob();
  
  return { blob, filename };
}