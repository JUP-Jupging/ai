# 베이스 이미지 선택
FROM python:3.13.6-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 먼저 복사 및 설치
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 프로젝트 전체 코드 복사
COPY . /app

# 컨테이너 내부에서 사용할 포트
EXPOSE 8082

# 컨테이너 시작 명령어
# 0.0.0.0 호스트로 실행해야 외부에서 접근 가능합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]