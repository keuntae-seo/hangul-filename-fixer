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