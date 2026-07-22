# Local storage baseline

- Provisioner: Rancher Local Path Provisioner `v0.0.36`
- StorageClass: `local-path`
- Binding: `WaitForFirstConsumer`
- Reclaim policy: `Delete`
- Backend: node-local `/opt/local-path-provisioner`

관측 스택의 단일 인스턴스 PVC에만 사용한다. node-local storage이므로 HA 또는 node failure 복구를 주장하지 않는다. 요청한 PVC 크기는 스케줄링 metadata이며 실제 hostPath 용량 제한을 강제하지 않으므로 node disk headroom을 별도로 검사한다.

설치:

```bash
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.36/deploy/local-path-storage.yaml
```
