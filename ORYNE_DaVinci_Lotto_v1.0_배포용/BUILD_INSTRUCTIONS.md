# ORYNE 다빈치 로또 분석 시스템 - 배포용 요구사항

## 필수 라이브러리
tkinter (기본 포함)
requests>=2.31.0
math (기본 포함)
json (기본 포함)
os (기본 포함)
datetime (기본 포함)
collections (기본 포함)
concurrent.futures (기본 포함)
threading (기본 포함)
time (기본 포함)

## PyInstaller 명령어 (권장)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ORYNE_DaVinci_Lotto_v1.0" --icon=icon.ico genius_lotto.py
```

## 추가 옵션
- --onefile: 단일 실행파일 생성
- --windowed: 콘솔 창 숨김
- --name: 실행파일 이름 지정
- --icon: 아이콘 추가 (선택사항)

## 배포 파일 구조
```
ORYNE_DaVinci_Lotto_v1.0.exe
├── [자동 생성] lotto_cache.json
├── [자동 생성] lotto_predictions.json
└── [사용자 매뉴얼.txt]
```

## 시스템 요구사항
- Windows 10/11
- 인터넷 연결 (로또 API 접근용)
- 최소 100MB 디스크 여유 공간
- RAM 최소 512MB

## 배포 주의사항
1. 개인 사용 전용
2. 상업적 배포 금지
3. ORYNE 저작권 유지
4. 수정/역공학 금지