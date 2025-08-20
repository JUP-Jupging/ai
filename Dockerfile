# ----- 디버깅용 Dockerfile 시작 -----

FROM python:3.13-slim

# 1단계: OS 정보와 패키지 저장소 목록을 직접 확인합니다.
# 이 로그를 통해 어떤 서버에서 패키지를 받아오려 하는지 알 수 있습니다.
RUN cat /etc/os-release && \
    echo "---" && \
    cat /etc/apt/sources.list

# 2단계: 패키지 목록 업데이트를 단독으로 실행하여 네트워크 오류 등이 있는지 확인합니다.
# 여기서 나오는 로그가 가장 중요합니다. (예: 404 Not Found, Could not resolve host 등)
RUN apt-get update

# 3단계: 업데이트된 목록에서 libaio1을 검색할 수 있는지 확인합니다.
# 여기서 아무것도 출력되지 않는다면, update가 실패했거나 저장소 목록에 문제가 있는 것입니다.
RUN apt-cache search libaio1

# ----- 디버깅용 Dockerfile 끝 -----