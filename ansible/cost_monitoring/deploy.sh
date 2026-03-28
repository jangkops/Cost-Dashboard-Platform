#!/bin/bash

# GPU 장치 감지
if [ -e "/dev/nvidia0" ]; then
    echo "✅ GPU Instance Detected"
    DOCKER_FLAGS="--gpus all --runtime=nvidia"
else
    echo "⚠️ CPU Instance Detected"
    DOCKER_FLAGS=""
fi

# 기존 컨테이너 정리
docker stop cost_monitoring_agent 2>/dev/null
docker rm cost_monitoring_agent 2>/dev/null

# 컨테이너 실행 (기존 이름 유지)
docker run -d \
  --name cost_monitoring_agent \
  --restart always \
  --pid=host \
  --privileged \
  -v /fsx:/fsx \
  -v ~/.aws:/root/.aws:ro \
  $DOCKER_FLAGS \
  cost_monitoring_agent:latest

echo "🚀 cost_monitoring_agent deployed and collecting data"
