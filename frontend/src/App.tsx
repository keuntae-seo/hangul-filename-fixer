import React, { useState, DragEvent } from 'react';
import { uploadForZip, uploadSingleFile } from './api';

export default function App() {
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('파일을 드래그하거나 선택하세요.');

  const onDrop = async (e: DragEvent) => {
    e.preventDefault(); setDrag(false);
    const files = Array.from(e.dataTransfer.files || []);
    if (!files.length) return;
    await run(files);
  };

  async function run(files: File[]) {
    try {
      setBusy(true); setMessage('처리 중...');
      
      // 단일 파일인 경우
      if (files.length === 1) {
        const { blob, filename } = await uploadSingleFile(files[0]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; 
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        setMessage(`완료! "${filename}" 파일이 다운로드되었습니다.`);
      } 
      // 여러 파일인 경우
      else {
        const zip = await uploadForZip(files);
        const url = URL.createObjectURL(zip);
        const a = document.createElement('a');
        a.href = url; 
        a.download = 'renamed-files.zip'; 
        a.click();
        URL.revokeObjectURL(url);
        setMessage(`완료! ${files.length}개 파일이 ZIP으로 다운로드되었습니다.`);
      }
    } catch (e) {
      setMessage('오류가 발생했습니다.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{maxWidth: 720, margin: '40px auto', padding: 16, fontFamily: 'system-ui'}}>
      <h1>한글 파일명 고쳐주기</h1>

      <div
        onDragOver={(e)=>{e.preventDefault(); setDrag(true);}}
        onDragLeave={()=>setDrag(false)}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${drag? '#4a90e2':'#aaa'}`,
          borderRadius: 16, padding: 24, textAlign: 'center'
        }}
      >
        <p>{message}</p>
        <input id="picker" type="file" multiple onChange={e=>{
          const files = Array.from(e.target.files || []);
          if (files.length) run(files);
        }} />
        <p style={{fontSize: 12, color: '#666'}}>
          📄 단일 파일: 정규화된 파일명으로 바로 다운로드<br/>
          📦 ZIP 파일: 내부 파일명도 정규화 후 다운로드<br/>
          📚 여러 파일: ZIP으로 묶어서 다운로드<br/>
          <span style={{fontSize: 11}}>파일은 서버에 저장되지 않습니다.</span>
        </p>
      </div>

      <details style={{marginTop: 16}}>
        <summary>설정</summary>
        <p>프록시: 개발 중 <code>/api</code> → <code>http://localhost:8000</code>로 프록시됩니다.</p>
      </details>
    </div>
  );
}