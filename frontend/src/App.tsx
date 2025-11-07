import React, { useState, DragEvent } from 'react';
import { uploadForZip } from './api';

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
      const zip = await uploadForZip(files);
      const url = URL.createObjectURL(zip);
      const a = document.createElement('a');
      a.href = url; a.download = 'renamed-files.zip'; a.click();
      setMessage('완료! ZIP이 내려받기 되었습니다.');
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
        <p style={{fontSize: 12, color: '#666'}}>서버에 업로드하여 ZIP으로 내려받습니다. 파일 자체는 저장하지 않도록 서버를 구성합니다.</p>
      </div>

      <details style={{marginTop: 16}}>
        <summary>설정</summary>
        <p>프록시: 개발 중 <code>/api</code> → <code>http://localhost:8000</code>로 프록시됩니다.</p>
      </details>
    </div>
  );
}