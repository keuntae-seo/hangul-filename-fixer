import React, { useState, useEffect, DragEvent } from 'react';
import { uploadForZip, uploadSingleFile } from './api';

interface Stats {
  total_views: number;
  today_views: number;
  total_files: number;
}

export default function App() {
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [stats, setStats] = useState<Stats>({ total_views: 0, today_views: 0, total_files: 0 });
  const [githubStars, setGithubStars] = useState<number>(0);

  useEffect(() => {
    // 페이지 로드 시 통계 기록 및 조회
    const API_URL = import.meta.env.VITE_API_URL || '/api';
    
    fetch(`${API_URL}/stats/view`, { method: 'POST' })
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Stats error:', err));
    
    // GitHub 스타 수 가져오기
    fetch('https://api.github.com/repos/keuntae-seo/hangul-filename-fixer')
      .then(res => res.json())
      .then(data => setGithubStars(data.stargazers_count || 0))
      .catch(err => console.error('GitHub API error:', err));
  }, []);

  const onDrop = async (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const droppedFiles = Array.from(e.dataTransfer.files || []);
    if (!droppedFiles.length) return;
    await run(droppedFiles);
  };

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDrag(true);
  };

  const onDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
  };

  async function run(uploadFiles: File[]) {
    try {
      setBusy(true);
      setMessage('처리 중...');

      if (uploadFiles.length === 1) {
        const { blob, filename } = await uploadSingleFile(uploadFiles[0]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        setMessage(`✓ ${filename}`);
      } else {
        const { blob, filename } = await uploadForZip(uploadFiles);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        setMessage(`✓ ${uploadFiles.length}개 파일 처리 완료`);
      }
    } catch (e) {
      setMessage('⚠ 오류가 발생했습니다');
      console.error(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0f0f23',
        color: '#e4e4e7',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        border: drag ? '8px solid #818cf8' : '8px solid transparent',
        boxSizing: 'border-box',
        boxShadow: drag ? 'inset 0 0 80px rgba(129,140,248,0.3)' : 'none',
        transition: 'all 0.3s ease',
      }}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
    >
      {/* Header */}
      <header style={{
        padding: '24px 32px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <h1 style={{
          margin: 0,
          fontSize: '20px',
          fontWeight: '600',
          background: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          한글 파일명 고쳐주기
        </h1>
      </header>

      {/* Main Content */}
      <main style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
      }}>
        <div style={{
          width: '100%',
          maxWidth: '600px',
          textAlign: 'center',
        }}>
          {/* Drop Zone */}
          <div
            style={{
              border: '2px dashed rgba(255,255,255,0.1)',
              borderRadius: '16px',
              padding: '80px 40px',
              background: drag ? 'rgba(167,139,250,0.1)' : 'rgba(255,255,255,0.02)',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onClick={() => document.getElementById('fileInput')?.click()}
          >
            <div style={{
              fontSize: '56px',
              marginBottom: '24px',
              opacity: 0.9,
            }}>
              {busy ? '⚙️' : drag ? '📥' : '📁'}
            </div>

            <div style={{
              fontSize: '18px',
              fontWeight: '500',
              marginBottom: '8px',
              color: '#e4e4e7',
            }}>
              {busy ? '처리 중...' : drag ? '파일을 놓으세요' : '파일을 드래그하거나 클릭하세요'}
            </div>

            <div style={{
              fontSize: '14px',
              color: 'rgba(228,228,231,0.5)',
              marginTop: '8px',
            }}>
              단일 파일, ZIP, 여러 파일 모두 지원
            </div>

            {message && (
              <div style={{
                marginTop: '24px',
                padding: '12px 20px',
                background: message.startsWith('⚠') 
                  ? 'rgba(239,68,68,0.1)' 
                  : 'rgba(34,197,94,0.1)',
                border: `1px solid ${message.startsWith('⚠') 
                  ? 'rgba(239,68,68,0.3)' 
                  : 'rgba(34,197,94,0.3)'}`,
                borderRadius: '8px',
                color: message.startsWith('⚠') ? '#fca5a5' : '#86efac',
                fontSize: '14px',
              }}>
                {message}
              </div>
            )}

            <input
              id="fileInput"
              type="file"
              multiple
              style={{ display: 'none' }}
              onChange={(e) => {
                const selectedFiles = Array.from(e.target.files || []);
                if (selectedFiles.length) run(selectedFiles);
              }}
            />
          </div>

          {/* Features */}
          <div style={{
            marginTop: '48px',
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px',
            fontSize: '13px',
            color: 'rgba(228,228,231,0.6)',
          }}>
            <div style={{
              padding: '16px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>📄</div>
              <div>파일명 자동 정규화</div>
            </div>
            <div style={{
              padding: '16px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>📦</div>
              <div>ZIP 내부 파일 처리</div>
            </div>
            <div style={{
              padding: '16px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>✨</div>
              <div>TXT/HWP 내용 수정</div>
            </div>
            <div style={{
              padding: '16px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.05)',
              borderRadius: '8px',
            }}>
              <div style={{ fontSize: '20px', marginBottom: '8px' }}>🔒</div>
              <div>서버 저장 없음</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        padding: '24px 32px',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '13px',
        color: '#e4e4e7',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div>
          © 2025 keuntae-seo. All rights reserved.
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* 통계 */}
          <div style={{
            display: 'flex',
            gap: '12px',
            padding: '8px 16px',
            background: 'rgba(255,255,255,0.02)',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.05)',
            fontSize: '12px',
            color: '#e4e4e7',
          }}>
            <span title="누적 방문자 수">
              <strong>방문</strong> {stats.total_views.toLocaleString()}
            </span>
            <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
            <span title="오늘 방문자 수">
              <strong>오늘</strong> {stats.today_views.toLocaleString()}
            </span>
            <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
            <span title="처리된 파일 수">
              <strong>파일</strong> {stats.total_files.toLocaleString()}
            </span>
          </div>
          
          {/* GitHub 버튼 */}
          <a
            href="https://github.com/keuntae-seo/hangul-filename-fixer"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#e4e4e7',
              textDecoration: 'none',
              fontSize: '12px',
              fontWeight: '500',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
              e.currentTarget.style.borderColor = 'rgba(167,139,250,0.5)';
              e.currentTarget.style.color = '#ffffff';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = '#e4e4e7';
            }}
          >
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>GitHub</span>
            {githubStars > 0 && (
              <>
                <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <svg width="14" height="14" fill="#fbbf24" viewBox="0 0 24 24">
                    <path d="M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279-7.416-3.967-7.417 3.967 1.481-8.279-6.064-5.828 8.332-1.151z"/>
                  </svg>
                  {githubStars.toLocaleString()}
                </span>
              </>
            )}
          </a>
        </div>
      </footer>
    </div>
  );
}