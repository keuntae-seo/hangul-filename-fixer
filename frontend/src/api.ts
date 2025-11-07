// 환경변수에서 API URL 가져오기
const API_URL = import.meta.env.VITE_API_URL || '/api';

export async function uploadForZip(files: File[]): Promise<Blob> {
  const form = new FormData();
  files.forEach(f => form.append('files', f, f.name));
  const url = `${API_URL}/rename?zip=true`;
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  return await res.blob(); // application/zip
}

export async function uploadSingleFile(file: File): Promise<{ blob: Blob, filename: string }> {
  const form = new FormData();
  form.append('files', file, file.name);
  const url = `${API_URL}/rename`;
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  
  // Content-Disposition 헤더에서 파일명 추출
  const disposition = res.headers.get('content-disposition');
  let filename = 'renamed-file';
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match) filename = match[1];
  }
  
  const blob = await res.blob();
  return { blob, filename };
}