# 베이스 이미지 선택
FROM --platform=linux/arm64 python:3.13-slim

# 존재하지 않는 패키지 저장소 목록 파일(/etc/apt/sources.list)을 직접 생성
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://deb.debian.org/debian trixie main" > /etc/apt/sources.list

# 시스템 라이브러리 설치
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    # 이미지 처리에 필요한 라이브러리
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    # Oracle Instant Client에 필요한 라이브러리
    unzip \
    libaio1 \
    libnsl2 && \
    # 모든 설치가 끝난 후 마지막에 정리합니다.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
ENV LD_LIBRARY_PATH=/opt/oracle/${IC_VER_DIR}

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
# .env 파일 복사
COPY ./.env ./.env

# 컨테이너 내부에서 사용할 포트
EXPOSE 8082

# 컨테이너 시작 명령어
# 0.0.0.0 호스트로 실행해야 외부에서 접근 가능합니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]