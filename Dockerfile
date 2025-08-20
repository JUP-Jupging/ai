# ----- 진단용 Dockerfile -----

FROM python:3.13-slim

# 1. 이전과 동일하게, 충돌을 막기 위해 기존 설정 파일을 제거하고 새로 만듭니다.
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://deb.debian.org/debian trixie main" > /etc/apt/sources.list

# 2. 패키지 목록을 업데이트한 직후,
#    다운로드된 목록 파일들 안에서 'libaio1'이라는 단어가 포함되어 있는지 직접 검색(grep)합니다.
#    - 만약 여기서 아무것도 출력되지 않는다면 -> update가 겉으로만 성공하고 실제로는 목록을 제대로 못 받아온 것입니다.
#    - 만약 여기서 무언가 출력된다면 -> apt-get install 명령어 자체에 다른 문제가 있는 것입니다.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    grep -r "libaio1" /var/lib/apt/lists/