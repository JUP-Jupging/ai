# 베이스 이미지 선택
FROM python:3.13-slim


# 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl unzip ca-certificates libaio1 libnsl2 \
#     && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends curl
RUN apt-get install -y --no-install-recommends unzip
RUN apt-get install -y --no-install-recommends ca-certificates
RUN apt-get install -y --no-install-recommends libaio1
RUN apt-get install -y --no-install-recommends libnsl2 # 아마 여기서 오류가 날 가능성이 높습니다.
RUN rm -rf /var/lib/apt/lists/*

# Oracle Instant Client 설치
ARG IC_VER_DIR=instantclient_23_9
ARG IC_ZIP=instantclient-basiclite-linux.x64-23.9.0.25.07.zip
COPY docker/instantclient/${IC_ZIP} /tmp/${IC_ZIP}
RUN mkdir -p /opt/oracle \
 && unzip /tmp/${IC_ZIP} -d /opt/oracle \
 && rm /tmp/${IC_ZIP}

# 런타임에서 클라이언트 찾도록 환경변수
ENV LD_LIBRARY_PATH=/opt/oracle/${IC_VER_DIR}
ENV ORACLE_CLIENT_LIB_DIR=/opt/oracle/${IC_VER_DIR}

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .

# 의존성 설치 후 문제가 되는 opencv-python을 강제로 삭제
RUN pip install --no-cache-dir --upgrade -r requirements.txt && \
    pip uninstall -y opencv-python opencv-python-headless && \
    pip install opencv-python-headless==4.12.0.88 && \
    pip install --no-cache-dir --upgrade pip setuptools wheel

# 프로젝트 전체 코드 복사
COPY ./app ./app
COPY ./models ./models

# 컨테이너 내부에서 사용할 포트
EXPOSE 8082

# 컨테이너 시작 명령어
# 0.0.0.0 호스트로 실행해야 외부에서 접근 가능합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]