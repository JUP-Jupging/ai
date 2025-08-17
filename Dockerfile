# 베이스 이미지 선택
FROM python:3.13.6-slim


# 시스템 라이브러리 설치 (문제 해결을 위해 임시로 남겨둡니다)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .

# 의존성 설치 후 문제가 되는 opencv-python을 강제로 삭제
RUN pip install --no-cache-dir --upgrade -r requirements.txt && \
    pip uninstall -y opencv-python opencv-python-headless && \
    pip install opencv-python-headless==4.12.0.88

# 프로젝트 전체 코드 복사
COPY ./app ./app
COPY ./models ./models

# 컨테이너 내부에서 사용할 포트
EXPOSE 8082

# 컨테이너 시작 명령어
# 0.0.0.0 호스트로 실행해야 외부에서 접근 가능합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]