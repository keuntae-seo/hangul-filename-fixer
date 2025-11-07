#!/bin/bash
# 로컬 백엔드 테스트 스크립트

echo "🧪 한글 파일명 고쳐주기 - 백엔드 테스트"
echo "========================================"
echo ""

# 1. Health check
echo "1️⃣  Health check 테스트..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [[ $HEALTH_RESPONSE == *"ok"* ]]; then
    echo "✅ Health check 성공: $HEALTH_RESPONSE"
else
    echo "❌ Health check 실패"
    exit 1
fi
echo ""

# 2. 테스트 파일 생성
echo "2️⃣  테스트 파일 생성..."
TEST_FILE="ㅂㅗㄱㅗㅅㅓ.txt"
echo "테스트 내용" > "$TEST_FILE"
echo "✅ 테스트 파일 생성: $TEST_FILE"
echo ""

# 3. API 테스트 (메타데이터만)
echo "3️⃣  API 테스트 (메타데이터)..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/rename?zip=false" \
  -F "files=@$TEST_FILE")
echo "응답: $RESPONSE"

if [[ $RESPONSE == *"보고서"* ]]; then
    echo "✅ 파일명 정규화 성공!"
else
    echo "❌ 파일명 정규화 실패"
fi
echo ""

# 4. 정리
echo "4️⃣  정리..."
rm -f "$TEST_FILE"
echo "✅ 테스트 파일 삭제"
echo ""

echo "🎉 테스트 완료!"
echo ""
echo "📚 API 문서 확인: http://localhost:8000/docs"

