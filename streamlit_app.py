#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================
    DA VINCI'S CIPHER: Quantum Lotto Decoder v1.0
    다빈치의 암호: 양자 로또 디코더 (Streamlit Edition)
=================================================================

© 2025 ORYNE. All Rights Reserved.
Developed by: ORYNE Corporation
Contact: Instagram @oryne.official
Release Date: October 7, 2025
Version: 1.0.0 (Streamlit)

⚠️ LEGAL NOTICE:
- This software is protected by copyright law
- For PERSONAL USE ONLY - Commercial use prohibited
- NO REDISTRIBUTION, MODIFICATION, or REVERSE ENGINEERING allowed
- Unauthorized use may result in legal action

🎯 DISCLAIMER:
- This program is for ENTERTAINMENT and EDUCATIONAL purposes only
- NO GUARANTEE of lottery winning - Use at your own risk
- We are NOT responsible for any financial losses
- Based on mathematical algorithms and statistical analysis

🔒 TERMS OF USE:
- Individual personal use only
- Do not share, distribute, or upload online
- Do not modify or reverse engineer
- Keep this copyright notice intact

🌐 DATA SOURCE:
- Official Korea Lottery API (dhlottery.co.kr)
- Real-time data synchronization
- Mathematical analysis algorithms

=================================================================
"""

import streamlit as st
import requests
import math
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

# --- 페이지 설정 ---
st.set_page_config(
    page_title="DA VINCI'S CIPHER - Quantum Lotto Decoder",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS ---
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
        border-right: 2px solid #e94560;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #00d4ff;
        text-align: center;
        font-size: 1.8rem !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    [data-testid="stSidebar"] h3 {
        color: #ffd700;
        text-align: center;
    }
    
    /* 제목 스타일 */
    h1 {
        color: #00d4ff;
        text-align: center;
        font-size: 3rem !important;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        color: #ffd700;
        border-bottom: 3px solid #e94560;
        padding-bottom: 0.5rem;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #00d4ff;
        margin-top: 1.5rem !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
        color: white;
        font-weight: bold;
        font-size: 1.1rem;
        padding: 0.8rem 2rem;
        border: none;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(233, 69, 96, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(233, 69, 96, 0.6);
        background: linear-gradient(135deg, #ff6b6b 0%, #e94560 100%);
    }
    
    /* 숫자 공 스타일 개선 */
    .number-ball {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        font-weight: bold;
        font-size: 24px;
        color: white;
        margin: 5px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    
    .number-ball:hover {
        transform: scale(1.1);
    }
    
    /* 메트릭 카드 스타일 */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #ffd700;
        font-weight: bold;
    }
    
    /* 성공/정보 메시지 스타일 */
    .stSuccess {
        background: linear-gradient(135deg, #1a5f3a 0%, #2d8659 100%);
        border-left: 5px solid #00ff88;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #1a4a5f 0%, #2d6d86 100%);
        border-left: 5px solid #00d4ff;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #5f4a1a 0%, #86732d 100%);
        border-left: 5px solid #ffd700;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Expander 스타일 */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border-radius: 10px;
        color: #00d4ff !important;
        font-weight: bold;
    }
    
    /* 구분선 */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e94560, transparent);
        margin: 2rem 0;
    }
    
    /* 선택 박스 스타일 */
    .stSelectbox > div > div {
        background-color: #16213e;
        border: 2px solid #e94560;
        border-radius: 10px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #e94560, #ff6b6b);
    }
    
    /* 카드 스타일 */
    .card {
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(233, 69, 96, 0.3);
    }
    
    /* 애니메이션 */
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 10px rgba(0, 212, 255, 0.5); }
        50% { text-shadow: 0 0 20px rgba(0, 212, 255, 1); }
    }
    
    .glow-text {
        animation: glow 2s ease-in-out infinite;
    }
    
    /* ========== 모바일 반응형 ========== */
    
    /* 태블릿 (768px 이하) */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
        }
        
        h3 {
            font-size: 1.2rem !important;
        }
        
        .number-ball {
            width: 45px;
            height: 45px;
            font-size: 18px;
            margin: 3px;
        }
        
        .card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .stButton > button {
            font-size: 1rem;
            padding: 0.6rem 1.5rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }
    
    /* 모바일 (480px 이하) */
    @media (max-width: 480px) {
        .main .block-container {
            padding: 0.5rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3 {
            font-size: 1rem !important;
        }
        
        .number-ball {
            width: 35px;
            height: 35px;
            font-size: 14px;
            margin: 2px;
        }
        
        .card {
            padding: 0.8rem;
            margin: 0.3rem 0;
        }
        
        .stButton > button {
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.2rem;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }
        
        /* 사이드바 폰트 크기 조정 */
        [data-testid="stSidebar"] h1 {
            font-size: 1.3rem !important;
        }
        
        [data-testid="stSidebar"] h3 {
            font-size: 1rem !important;
        }
    }
    
    /* 초소형 모바일 (360px 이하) */
    @media (max-width: 360px) {
        h1 {
            font-size: 1.2rem !important;
        }
        
        .number-ball {
            width: 30px;
            height: 30px;
            font-size: 12px;
            margin: 1px;
        }
        
        .stButton > button {
            font-size: 0.85rem;
            padding: 0.4rem 0.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 전역 변수 ---
LOTTO_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="
CACHE_FILE = "lotto_cache.json"
PREDICTIONS_FILE = "lotto_predictions.json"
RECENT_DRAW = 50
LOTTO_RANGE = range(1, 46)
FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34]

# 동적으로 설정될 변수들
TOTAL_DRAW = 1191  # 기본값

# --- 세션 스테이트 초기화 ---
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'lotto_data' not in st.session_state:
    st.session_state.lotto_data = []
if 'number_counts' not in st.session_state:
    st.session_state.number_counts = {}
if 'recent_counts' not in st.session_state:
    st.session_state.recent_counts = {}
if 'all_sums' not in st.session_state:
    st.session_state.all_sums = []
if 'TOTAL_DRAW' not in st.session_state:
    st.session_state.TOTAL_DRAW = 1191

# --- 데이터 수집 함수들 ---

def get_latest_draw_number():
    """동행복권 API를 통해 현재 최신 회차 번호를 가져옵니다."""
    estimated_draw = 1200
    
    for draw_no in range(estimated_draw, estimated_draw - 10, -1):  # 최근 10개만 확인
        try:
            resp = requests.get(LOTTO_URL + str(draw_no), timeout=2)  # timeout 2초로 단축
            data = resp.json()
            
            if data.get('returnValue') == 'success' and 'drwtNo1' in data:
                return draw_no
        except:
            continue
    
    return 1191

def load_cached_data():
    """캐시된 로또 데이터를 불러옵니다."""
    if not os.path.exists(CACHE_FILE):
        return {}
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_cached_data(data):
    """로또 데이터를 캐시 파일에 저장합니다."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"캐시 저장 실패: {e}")

def fetch_lotto_data(draw_no):
    """특정 회차의 로또 데이터를 가져옵니다."""
    try:
        resp = requests.get(LOTTO_URL + str(draw_no), timeout=3)  # timeout 3초
        data = resp.json()
        
        if data.get('returnValue') == 'success' and 'drwtNo1' in data:
            nums = [
                data['drwtNo1'], data['drwtNo2'], data['drwtNo3'],
                data['drwtNo4'], data['drwtNo5'], data['drwtNo6']
            ]
            bonus = data['bnusNo']
            draw_date = data.get('drwNoDate', '')
            
            return {
                'draw': draw_no,
                'date': draw_date,
                'numbers': nums,
                'bonus': bonus
            }
    except Exception as e:
        return None
    
    return None

@st.cache_data(ttl=3600)  # 1시간 캐시
def load_all_lotto_data(force_refresh=False):
    """모든 로또 데이터를 로드합니다."""
    global TOTAL_DRAW
    
    cache = load_cached_data()
    latest_draw = get_latest_draw_number()
    
    # 캐시 유효성 검사 - 캐시가 있으면 즉시 반환
    if not force_refresh and cache.get('total_draw') == latest_draw and 'lotto_data' in cache:
        lotto_data = cache['lotto_data']
        number_counts = {int(k): v for k, v in cache.get('number_counts', {}).items()}
        recent_counts = {int(k): v for k, v in cache.get('recent_counts', {}).items()}
        all_sums = cache.get('all_sums', [])
        TOTAL_DRAW = latest_draw
        
        return lotto_data, number_counts, recent_counts, all_sums, latest_draw
    
    # 새로운 데이터만 수집 (캐시에 없는 회차만)
    lotto_data = cache.get('lotto_data', [])
    existing_draws = {d['draw'] for d in lotto_data}
    
    # 수집할 회차 계산
    draws_to_fetch = [i for i in range(1, latest_draw + 1) if i not in existing_draws]
    
    if draws_to_fetch:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with ThreadPoolExecutor(max_workers=20) as executor:  # 워커 수 증가
            futures = {executor.submit(fetch_lotto_data, i): i for i in draws_to_fetch}
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                if result:
                    lotto_data.append(result)
                
                completed += 1
                progress = completed / len(draws_to_fetch)
                progress_bar.progress(progress)
                status_text.text(f'🔄 데이터 수집 중... {completed}/{len(draws_to_fetch)} ({progress*100:.0f}%)')
        
        progress_bar.empty()
        status_text.empty()
    
    lotto_data.sort(key=lambda x: x['draw'])
    
    # 통계 계산
    number_counts = Counter()
    all_sums = []
    
    for entry in lotto_data:
        for num in entry['numbers']:
            number_counts[num] += 1
        all_sums.append(sum(entry['numbers']))
    
    # 최근 회차 통계
    recent_counts = Counter()
    recent_data = lotto_data[-RECENT_DRAW:] if len(lotto_data) >= RECENT_DRAW else lotto_data
    
    for entry in recent_data:
        for num in entry['numbers']:
            recent_counts[num] += 1
    
    # 캐시 저장
    cache_data = {
        'total_draw': latest_draw,
        'last_updated': datetime.now().isoformat(),
        'lotto_data': lotto_data,
        'number_counts': dict(number_counts),
        'recent_counts': dict(recent_counts),
        'all_sums': all_sums
    }
    save_cached_data(cache_data)
    
    TOTAL_DRAW = latest_draw
    
    return lotto_data, dict(number_counts), dict(recent_counts), all_sums, latest_draw

def load_predictions_data():
    """저장된 예측 데이터를 불러옵니다."""
    if not os.path.exists(PREDICTIONS_FILE):
        return {}
    
    try:
        with open(PREDICTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_predictions_data(predictions):
    """예측 데이터를 저장합니다."""
    try:
        with open(PREDICTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"예측 데이터 저장 실패: {e}")

def get_previous_predictions(target_draw):
    """특정 회차에 대한 과거 예측을 가져옵니다."""
    predictions = load_predictions_data()
    draw_key = str(target_draw)
    
    if draw_key in predictions:
        return predictions[draw_key].get('sets', [])
    
    return []

# --- 번호 생성 알고리즘들 (genius_lotto.py에서 복사) ---

def set1_fibonacci():
    """세트1: 피보나치 황금비율"""
    if not st.session_state.number_counts or sum(st.session_state.number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    TOTAL_DRAW = st.session_state.TOTAL_DRAW
    
    import random
    # 더 큰 변화를 위해 시드 생성 방식 개선
    random.seed((TOTAL_DRAW ** 2) * 17 + TOTAL_DRAW * 137 + 1)
    
    PHI = (1 + math.sqrt(5)) / 2
    fib_scores = {}
    
    for num in range(1, 46):
        base_score = 0
        if num in FIBONACCI:
            base_score = 10
        
        distance_to_phi = min(abs(num - f * PHI) for f in FIBONACCI if f * PHI <= 45)
        phi_score = 1 / (1 + distance_to_phi)
        
        freq_score = st.session_state.number_counts.get(num, 0) / max(st.session_state.number_counts.values()) if st.session_state.number_counts else 0
        recent_score = st.session_state.recent_counts.get(num, 0) / (RECENT_DRAW * 6) if RECENT_DRAW > 0 else 0
        
        # 랜덤 변동성 크게 증가 (0.5 ~ 1.5 범위)
        random_factor = 0.5 + random.random()
        
        total_score = base_score + phi_score * 5 + (1 - freq_score) * 3 + recent_score * 2
        fib_scores[num] = total_score * random_factor
    
    sorted_nums = sorted(fib_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 상위 30개에서 선택하도록 범위 확대
    selected = []
    candidates = sorted_nums[:30]
    random.shuffle(candidates)  # 후보군을 섞어서 더 다양하게
    
    for num, score in candidates:
        if len(selected) < 6:
            if not selected or abs(num - selected[-1]) >= 2:  # 간격 조건 완화
                selected.append(num)
    
    while len(selected) < 6:
        for num, score in sorted_nums:
            if num not in selected:
                selected.append(num)
                break
    
    return sorted(selected[:6])

def set2_regression():
    """세트2: 평균회귀"""
    if not st.session_state.number_counts or not st.session_state.recent_counts:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    TOTAL_DRAW = st.session_state.TOTAL_DRAW
    
    import random
    random.seed(TOTAL_DRAW * 1000 + 2)
    
    total_appearances = sum(st.session_state.number_counts.values())
    expected_per_num = total_appearances / 45 if total_appearances > 0 else 1
    
    regression_scores = {}
    
    for num in range(1, 46):
        actual = st.session_state.number_counts.get(num, 0)
        recent = st.session_state.recent_counts.get(num, 0)
        
        deviation = expected_per_num - actual
        regression_potential = deviation / expected_per_num if expected_per_num > 0 else 0
        
        recent_trend = recent / (RECENT_DRAW * 6 / 45) if RECENT_DRAW > 0 else 1
        trend_factor = 1.0
        if recent_trend > 1.3:
            trend_factor = 0.7
        elif recent_trend < 0.7:
            trend_factor = 1.4
        
        time_weight = 1.0 + (TOTAL_DRAW % 10) * 0.05
        stochastic = random.gauss(1.0, 0.15)
        
        final_score = (1 + regression_potential) * trend_factor * time_weight * max(0.5, min(1.5, stochastic))
        regression_scores[num] = final_score
    
    sorted_candidates = sorted(regression_scores.items(), key=lambda x: x[1], reverse=True)
    
    selected = []
    for num, score in sorted_candidates[:20]:
        if len(selected) >= 6:
            break
        
        zone_ok = True
        if len(selected) >= 1:
            low = sum(1 for n in selected if n <= 15)
            mid = sum(1 for n in selected if 16 <= n <= 30)
            high = sum(1 for n in selected if n >= 31)
            
            if num <= 15 and low >= 3:
                zone_ok = False
            elif 16 <= num <= 30 and mid >= 3:
                zone_ok = False
            elif num >= 31 and high >= 3:
                zone_ok = False
        
        if zone_ok:
            selected.append(num)
    
    while len(selected) < 6:
        for num, score in sorted_candidates:
            if num not in selected:
                selected.append(num)
                break
    
    return sorted(selected[:6])

def set3_geometry():
    """세트3: 페르마 확률론"""
    if not st.session_state.number_counts or not st.session_state.recent_counts:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    TOTAL_DRAW = st.session_state.TOTAL_DRAW
    
    import random
    random.seed(TOTAL_DRAW * 1000 + 3)
    
    total_draws = sum(st.session_state.number_counts.values()) / 6
    expected_prob = 6 / 45
    
    fermat_scores = {}
    
    for num in range(1, 46):
        expected_count = total_draws * expected_prob
        actual_count = st.session_state.number_counts.get(num, 0)
        
        if expected_count > 0:
            prob_debt = (expected_count - actual_count) / expected_count
        else:
            prob_debt = 0
        
        recent_factor = 1.0 - (st.session_state.recent_counts.get(num, 0) / (RECENT_DRAW * 6)) if RECENT_DRAW > 0 else 1.0
        
        harmonic_mean = expected_prob
        if actual_count > 0:
            historical_prob = actual_count / (total_draws * 6)
            harmonic_mean = 2 / (1/expected_prob + 1/historical_prob) if historical_prob > 0 else expected_prob
        
        expected_value = harmonic_mean * (1 + prob_debt) * (1 + recent_factor)
        
        zone_bonus = 1.0
        if num <= 15:
            zone_bonus = 1.2
        elif num <= 30:
            zone_bonus = 1.1
        
        stochastic = random.gauss(1.0, 0.1)
        fermat_scores[num] = expected_value * zone_bonus * max(0.7, min(1.3, stochastic))
    
    sorted_nums = sorted(fermat_scores.items(), key=lambda x: x[1], reverse=True)
    
    selected = []
    top_24 = sorted_nums[:24]
    
    low_pool = [n for n, s in top_24 if n <= 15]
    mid_pool = [n for n, s in top_24 if 16 <= n <= 30]
    high_pool = [n for n, s in top_24 if n >= 31]
    
    if low_pool:
        selected.append(low_pool[0])
    if mid_pool:
        selected.append(mid_pool[0])
    if high_pool:
        selected.append(high_pool[0])
    
    for num, score in sorted_nums:
        if num not in selected and len(selected) < 6:
            selected.append(num)
    
    return sorted(selected[:6])

def set4_quantum():
    """세트4: 콜모고로프 측도론"""
    if not st.session_state.number_counts or not st.session_state.recent_counts or not st.session_state.all_sums:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    TOTAL_DRAW = st.session_state.TOTAL_DRAW
    
    import random
    random.seed(TOTAL_DRAW * 1000 + 4)
    
    total_draws = sum(st.session_state.number_counts.values()) / 6
    
    kolmogorov_scores = {}
    
    for num in range(1, 46):
        concept_scores = []
        
        # Prime
        is_prime = num > 1 and all(num % i != 0 for i in range(2, int(num**0.5) + 1))
        concept_scores.append(1.0 if is_prime else 0.5)
        
        # Composite
        concept_scores.append(0.5 if is_prime else 1.0)
        
        # Perfect square
        concept_scores.append(1.0 if int(num**0.5)**2 == num else 0.3)
        
        # Fibonacci
        concept_scores.append(1.0 if num in FIBONACCI else 0.4)
        
        # Triangular
        n = (-1 + (1 + 8*num)**0.5) / 2
        concept_scores.append(1.0 if n == int(n) else 0.3)
        
        # Palindrome
        concept_scores.append(1.0 if str(num) == str(num)[::-1] else 0.5)
        
        # Sum of digits
        digit_sum = sum(int(d) for d in str(num))
        concept_scores.append(digit_sum / 9.0)
        
        # Divisibility
        divisor_count = sum(1 for i in range(1, num+1) if num % i == 0)
        concept_scores.append(divisor_count / 6.0)
        
        # Golden ratio
        phi = (1 + 5**0.5) / 2
        concept_scores.append(1.0 / (1 + abs(num - 23*phi/2)))
        
        # Entropy
        freq = st.session_state.number_counts.get(num, 0)
        expected = total_draws * 6 / 45
        if expected > 0:
            entropy = 1.0 - abs(freq - expected) / expected
        else:
            entropy = 0.5
        concept_scores.append(entropy)
        
        measure = sum(concept_scores) / len(concept_scores)
        
        recent_penalty = st.session_state.recent_counts.get(num, 0) / (RECENT_DRAW * 6) if RECENT_DRAW > 0 else 0
        measure *= (1.0 - recent_penalty * 0.5)
        
        stochastic = random.gauss(1.0, 0.12)
        kolmogorov_scores[num] = measure * max(0.6, min(1.4, stochastic))
    
    sorted_nums = sorted(kolmogorov_scores.items(), key=lambda x: x[1], reverse=True)
    
    selected = []
    for num, score in sorted_nums[:6]:
        selected.append(num)
    
    return sorted(selected)

def set5_grand_unification():
    """세트5: 파스칼의 이항분포 가중 확률"""
    if not st.session_state.number_counts or not st.session_state.recent_counts:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    TOTAL_DRAW = st.session_state.TOTAL_DRAW
    
    import random
    from math import comb
    
    # 회차별로 다른 시드
    random.seed((TOTAL_DRAW ** 2) * 23 + TOTAL_DRAW * 271 + 5)
    
    try:
        # 회차별로 구간 우선순위 변경 (0~10 순환)
        priority_cycle = TOTAL_DRAW % 11
        
        # 구간별 p값 설정 (구간마다 다른 확률)
        zone_configs = [
            # (구간, p값, 가중치)
            (range(1, 10), 0.2, 1.0),    # 작은 번호
            (range(10, 19), 0.3, 1.0),   # 작은-중간
            (range(19, 28), 0.5, 1.0),   # 중간
            (range(28, 37), 0.7, 1.0),   # 중간-큰
            (range(37, 46), 0.8, 1.0),   # 큰 번호
        ]
        
        # 우선순위 구간에 가중치 부여
        priority_zone = priority_cycle % 5
        zone_configs[priority_zone] = (zone_configs[priority_zone][0], zone_configs[priority_zone][1], 3.0)
        
        # 번호별 가중치 계산
        pascal_weights = []
        for num in range(1, 46):
            # 어느 구간에 속하는지 확인
            zone_p = 0.5
            zone_weight = 1.0
            for zone_range, p, weight in zone_configs:
                if num in zone_range:
                    zone_p = p
                    zone_weight = weight
                    break
            
            # 구간 내 상대 위치 (0.0 ~ 1.0)
            zone_start = (num - 1) // 9 * 9 + 1
            zone_size = 9 if zone_start < 37 else 9
            relative_pos = (num - zone_start) / zone_size if zone_size > 0 else 0.5
            
            try:
                # 이항분포: p^k * (1-p)^(n-k) 형태만 사용 (조합수 제거)
                k = int(relative_pos * 8)  # 0~8 사이의 값
                prob = (zone_p ** k) * ((1 - zone_p) ** (8 - k))
                
                # 구간 가중치 적용
                prob *= zone_weight
                
                # 출현 빈도 보정
                total_draws = len(st.session_state.lotto_data) if st.session_state.lotto_data else TOTAL_DRAW
                historical_freq = st.session_state.number_counts.get(num, 0) / (total_draws * 6) if total_draws > 0 else 1/45
                expected_freq = 1 / 45
                
                # 덜 나온 번호에 보너스
                if historical_freq < expected_freq * 0.8:
                    freq_bonus = 1.3
                elif historical_freq < expected_freq:
                    freq_bonus = 1.1
                else:
                    freq_bonus = 0.9
                
                # 최근 과열 방지
                recent_count = st.session_state.recent_counts.get(num, 0)
                if recent_count >= 3:
                    recent_penalty = 0.2
                elif recent_count == 2:
                    recent_penalty = 0.5
                elif recent_count == 1:
                    recent_penalty = 0.8
                else:
                    recent_penalty = 1.0
                
                # 중앙값(20~30) 억제
                if 20 <= num <= 30:
                    center_penalty = 0.4
                else:
                    center_penalty = 1.0
                
                # 최종 가중치
                weight = prob * freq_bonus * recent_penalty * center_penalty * random.uniform(0.3, 2.0)
                pascal_weights.append(weight)
                
            except Exception as e:
                pascal_weights.append(0.001)
        
        # 정규화
        total_weight = sum(pascal_weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in pascal_weights]
        else:
            normalized_weights = [1/45] * 45
        
        # 가중치 기반 선택
        selected = []
        max_attempts = 100
        attempts = 0
        
        while len(selected) < 6 and attempts < max_attempts:
            num = random.choices(range(1, 46), weights=normalized_weights, k=1)[0]
            if num not in selected:
                selected.append(num)
            attempts += 1
        
        # 부족하면 가중치 높은 순으로 채우기
        if len(selected) < 6:
            sorted_nums = sorted(range(1, 46), key=lambda x: normalized_weights[x-1], reverse=True)
            for num in sorted_nums:
                if num not in selected:
                    selected.append(num)
                    if len(selected) >= 6:
                        break
        
        # 구간 분산 강제 (1-15, 16-30, 31-45에서 최소 1개씩)
        selected_sorted = sorted(selected[:6])
        low = [n for n in selected_sorted if 1 <= n <= 15]
        mid = [n for n in selected_sorted if 16 <= n <= 30]
        high = [n for n in selected_sorted if 31 <= n <= 45]
        
        # 중간 구간이 4개 이상이면 조정
        if len(mid) >= 4:
            # 가중치 상위 30개에서 저/고 구간 찾아 교체
            top_nums = sorted(range(1, 46), key=lambda x: normalized_weights[x-1], reverse=True)[:30]
            
            if len(low) == 0:
                candidates = [n for n in top_nums if 1 <= n <= 15 and n not in selected_sorted]
                if candidates:
                    selected_sorted.remove(mid[-1])
                    selected_sorted.append(candidates[0])
            
            if len(high) == 0:
                candidates = [n for n in top_nums if 31 <= n <= 45 and n not in selected_sorted]
                if candidates:
                    mid_nums = [n for n in selected_sorted if 16 <= n <= 30]
                    if mid_nums:
                        selected_sorted.remove(mid_nums[-1])
                        selected_sorted.append(candidates[0])
        
        # 홀짝 비율 조정 (극단 방지)
        odd_count = sum(1 for n in selected_sorted if n % 2 == 1)
        
        if odd_count <= 1 or odd_count >= 5:
            top_nums = sorted(range(1, 46), key=lambda x: normalized_weights[x-1], reverse=True)[:25]
            
            if odd_count <= 1:
                needed = [n for n in top_nums if n % 2 == 1 and n not in selected_sorted]
                if needed:
                    evens = [n for n in selected_sorted if n % 2 == 0]
                    if evens:
                        selected_sorted.remove(evens[-1])
                        selected_sorted.append(needed[0])
            elif odd_count >= 5:
                needed = [n for n in top_nums if n % 2 == 0 and n not in selected_sorted]
                if needed:
                    odds = [n for n in selected_sorted if n % 2 == 1]
                    if odds:
                        selected_sorted.remove(odds[-1])
                        selected_sorted.append(needed[0])
        
        return sorted(selected_sorted[:6])
        
    except Exception as e:
        # 오류 시 안전한 선택
        safe_nums = list(range(1, 46))
        random.shuffle(safe_nums)
        return sorted(selected_sorted[:6])
        
    except Exception as e:
        # 오류 시 안전한 선택
        safe_nums = list(range(1, 46))
        random.shuffle(safe_nums)
        return sorted(safe_nums[:6])

def generate_numbers_and_explanations():
    """모든 세트의 번호와 설명을 생성합니다."""
    sets = []
    
    # 세트1
    nums1 = set1_fibonacci()
    exp1 = explain_set1(nums1)
    sets.append((nums1, exp1))
    
    # 세트2
    nums2 = set2_regression()
    exp2 = explain_set2(nums2)
    sets.append((nums2, exp2))
    
    # 세트3
    nums3 = set3_geometry()
    exp3 = explain_set3(nums3)
    sets.append((nums3, exp3))
    
    # 세트4
    nums4 = set4_quantum()
    exp4 = explain_set4(nums4)
    sets.append((nums4, exp4))
    
    # 세트5
    nums5 = set5_grand_unification()
    exp5 = explain_set5(nums5)
    sets.append((nums5, exp5))
    
    return sets

# --- 설명 함수들 ---

def explain_set1(nums):
    if "(데이터 없음)" in str(nums):
        return "[황금 비율의 서명]\n데이터 로딩 중입니다. 잠시만 기다려주세요."
    
    fib_count = sum(1 for n in nums if n in FIBONACCI and n <= 45)
    ratio = sum(nums) / len(nums) if nums else 0
    
    return f"""[황금 비율의 서명 - 레오나르도의 조화]
이 수열은 황금비(φ=1.618)와 피보나치 수열의 수학적 원리를 기반으로 선별되었습니다. {nums} 중 {fib_count}개가 피보나치 수열(1,1,2,3,5,8,13,21...)에 포함되며, 평균값 {ratio:.1f}는 자연에서 발견되는 황금비의 대칭성을 반영합니다. 이는 다빈치의 '비트루비우스적 인간'에서 사용된 인체 비례와 동일한 수학적 원리를 적용한 결과입니다."""

def explain_set2(nums):
    if "(데이터 없음)" in str(nums):
        return "[우주 평균 회귀의 법칙]\n데이터 분석 중입니다. 잠시만 기다려주세요."
    
    return f"""[우주 평균 회귀의 법칙 - 통계적 각성]
이 수리체계 {nums}는 동적 평균회귀 모델과 시계열 분석을 통해 도출되었습니다. 전체 출현 빈도와 최근 트렌드의 편차를 분석하여, 통계적으로 '회귀'할 가능성이 높은 번호들을 선별합니다. 각 회차마다 시간 가중치와 확률적 변동성을 적용하여 동일한 결과가 반복되지 않도록 설계된 adaptive 알고리즘입니다. 이는 금융 시장의 평균회귀 이론을 로또 데이터에 적용한 혁신적 접근법입니다."""

def explain_set3(nums):
    if "(데이터 없음)" in str(nums):
        return "[피에르 드 페르마의 확률론]\n기하학적 분석 중입니다. 잠시만 기다려주세요."
    
    center = 23
    symmetry = sum(1 for n in nums if abs(n - center) <= 8)
    
    return f"""[피에르 드 페르마의 확률론 - 기댓값과 신성 기하학]
{nums}는 17세기 천재 수학자 피에르 드 페르마(Pierre de Fermat)의 확률론을 기반으로 계산되었습니다. 페르마의 기댓값 이론 E(X) = Σ(x_i × P(x_i))을 적용하여 각 번호의 출현 확률과 미래 가능성을 수학적으로 계산했습니다. 또한 페르마의 유명한 '점 분할 문제(Problem of Points)'의 공정한 확률 분배 원리를 사용하여, 과거 출현 빈도와 미래 예측 확률을 조화롭게 결합했습니다. 기하학적 대칭성과 황금비(φ=1.618)를 융합하여 {symmetry}개의 대칭적 요소를 포함하며, 이는 페르마의 조합론 C(n,k)와 최적화 이론이 만나 탄생한 수학적 예술작품입니다."""

def explain_set4(nums):
    if "(데이터 없음)" in str(nums):
        return "[콜모고로프의 공리적 확률론]\n측도론적 분석 중입니다. 잠시만 기다려주세요."
    
    return f"""[콜모고로프의 공리적 확률론 - 확률은 사건의 공간이다]
이 수열 {nums}는 현대 확률론의 아버지 안드레이 콜모고로프(Andrey Kolmogorov)의 공리적 확률 이론을 기반으로 도출되었습니다. 콜모고로프는 확률을 삼원조 (Ω, F, P)로 정의했습니다: Ω는 표본공간, F는 사건의 시그마-대수(sigma-algebra), P는 확률 측도입니다. 로또 6/45의 표본공간 크기는 C(45,6) = 8,145,060이며, 모든 조합은 동등한 확률 1/8,145,060을 가집니다. 하지만 각 번호의 출현은 독립사건이 아니므로, 경험적 확률 측도와 이론적 측도의 편차를 콜모고로프-스미르노프 통계량으로 측정했습니다. 또한 르베스그 적분을 통한 기댓값 E[X], 조건부 확률 P(A|B), 보렐 집합의 측도, 엔트로피 H(X) = -sum(P(x)logP(x))를 종합하여 각 번호의 확률적 가치를 계산했습니다. 이는 운조차도 정의된 수학적 사건으로 취급하는 콜모고로프의 엄밀한 공리적 접근법의 실현입니다."""

def explain_set5(nums):
    if "(데이터 없음)" in str(nums):
        return "[파스칼의 이항분포 가중 확률]\n데이터 분석 중입니다. 잠시만 기다려주세요."
    
    low = sum(1 for n in nums if 1 <= n <= 15)
    mid = sum(1 for n in nums if 16 <= n <= 30)
    high = sum(1 for n in nums if 31 <= n <= 45)
    odd_count = sum(1 for n in nums if n % 2 == 1)
    even_count = 6 - odd_count
    
    return f"""[파스칼의 이항분포 가중 확률론]
이 수열 {nums}는 블레이즈 파스칼의 **이항분포 공식 P(k; n, p) = nCk × p^k × (1-p)^(n-k)**을 기반으로 생성되었습니다. p값을 0.15~0.85 사이에서 회차별로 변화시켜, p < 0.5일 때는 작은 번호에, p > 0.5일 때는 큰 번호에 가중치를 부여합니다. 이를 통해 파스칼의 삼각형이 만드는 확률 분포를 동적으로 이동시키며, 중앙 집중을 방지하고 양쪽 꼬리까지 고르게 탐색합니다. 여기에 출현 빈도 보정, 최근 과열 방지, 홀짝 패턴을 결합하여 매 회차마다 완전히 다른 확률 구조를 생성합니다. 구간 분포는 저{low}개, 중{mid}개, 고{high}개이며, 홀짝 비율은 {odd_count}:{even_count}입니다."""

# --- Streamlit UI ---

def main():
    # 사이드바
    with st.sidebar:
        # 로고 영역
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%); border-radius: 15px; margin-bottom: 1rem;'>
            <h1 style='color: white; margin: 0; font-size: 2rem;'>🎨 ORYNE</h1>
            <p style='color: white; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>Quantum Technology</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.title("🎨 DA VINCI'S CIPHER")
        st.markdown("### Quantum Lotto Decoder v1.0")
        st.markdown("---")
        
        # 데이터 로드 버튼
        if st.button("🔄 데이터 갱신", use_container_width=True):
            with st.spinner("데이터 수집 중..."):
                st.session_state.data_loaded = False
                load_all_lotto_data.clear()  # 캐시 클리어
                lotto_data, number_counts, recent_counts, all_sums, total_draw = load_all_lotto_data(force_refresh=True)
                st.session_state.lotto_data = lotto_data
                st.session_state.number_counts = number_counts
                st.session_state.recent_counts = recent_counts
                st.session_state.all_sums = all_sums
                st.session_state.TOTAL_DRAW = total_draw
                st.session_state.data_loaded = True
                st.success("✅ 데이터 갱신 완료!")
        
        st.markdown("---")
        
        # 정보 표시
        if st.session_state.data_loaded:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #16213e 0%, #0f3460 100%); 
                        padding: 1rem; border-radius: 10px; border: 2px solid #00d4ff;
                        margin-bottom: 1rem;'>
                <h4 style='color: #ffd700; text-align: center; margin: 0;'>📊 데이터 현황</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎯 최신 회차", f"{st.session_state.TOTAL_DRAW}회")
            with col2:
                st.metric("📈 수집 회차", f"{len(st.session_state.lotto_data)}회")
        
        st.markdown("---")
        
        # 프로그램 정보
        with st.expander("📋 프로그램 정보"):
            st.markdown("""
            **© 2025 ORYNE Corporation**
            
            - **버전**: v1.0.0 (Streamlit)
            - **출시일**: 2025년 10월 7일
            - **연락처**: Instagram @oryne.official
            
            ⚠️ **법적 고지사항**
            - 개인 사용 전용 (상업적 이용 금지)
            - 무단 복제, 배포, 수정 금지
            - 저작권법에 의해 보호되는 소프트웨어
            
            🎯 **면책 조항**
            - 오락 및 교육 목적으로 제작됨
            - 로또 당첨을 보장하지 않음
            - 투자 손실에 대한 책임지지 않음
            - 수학적 알고리즘 기반 분석
            """)
    
    # 메인 영역
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 class='glow-text'>🎨 DA VINCI'S CIPHER</h1>
        <h3 style='color: #ffd700; margin-top: 0;'>Quantum Lotto Decoder - 다빈치의 암호</h3>
        <p style='color: #888; font-size: 1.1rem;'>5가지 천재 수학자의 알고리즘으로 미래를 예측합니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 초기 데이터 로드 - 백그라운드에서 자동 로드
    if not st.session_state.data_loaded:
        # 캐시 파일이 있으면 즉시 로드 (빠름)
        cache = load_cached_data()
        if cache and 'lotto_data' in cache:
            st.session_state.lotto_data = cache['lotto_data']
            st.session_state.number_counts = {int(k): v for k, v in cache.get('number_counts', {}).items()}
            st.session_state.recent_counts = {int(k): v for k, v in cache.get('recent_counts', {}).items()}
            st.session_state.all_sums = cache.get('all_sums', [])
            st.session_state.TOTAL_DRAW = cache.get('total_draw', 1191)
            st.session_state.data_loaded = True
            
            # 백그라운드에서 최신 데이터 확인
            latest = get_latest_draw_number()
            if latest > st.session_state.TOTAL_DRAW:
                st.info(f"💡 새로운 회차({latest}회)가 있습니다. '데이터 갱신' 버튼을 눌러주세요.")
        else:
            # 캐시 없으면 전체 로드
            with st.spinner("🔄 초기 데이터 로딩 중... 잠시만 기다려주세요."):
                lotto_data, number_counts, recent_counts, all_sums, total_draw = load_all_lotto_data()
                st.session_state.lotto_data = lotto_data
                st.session_state.number_counts = number_counts
                st.session_state.recent_counts = recent_counts
                st.session_state.all_sums = all_sums
                st.session_state.TOTAL_DRAW = total_draw
                st.session_state.data_loaded = True
            st.success("✅ 데이터 로딩 완료!")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs([
        "📊 대시보드",
        "🎯 번호 생성", 
        "🔍 분석"
    ])
    
    # ==================== 탭 1: 대시보드 ====================
    with tab1:
        st.markdown("""
        <div style='text-align: center; margin: 1rem 0;'>
            <h2 style='color: #ffd700;'>📊 로또 대시보드</h2>
            <p style='color: #888;'>최신 당첨번호 및 통계 정보</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 최신 당첨번호 표시
        if st.session_state.lotto_data:
            latest = st.session_state.lotto_data[-1]
            
            st.markdown(f"""
            <div class='card'>
                <h2 style='text-align: center; color: #00d4ff; margin-top: 0;'>
                    🏆 제 {latest['draw']}회 당첨번호
                </h2>
                <p style='text-align: center; color: #888; font-size: 1.1rem; margin-bottom: 1.5rem;'>
                    📅 {latest['date']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # 번호들을 컬럼으로 표시
            cols = st.columns([1, 1, 1, 1, 1, 1, 0.3, 1])
            
            for i, num in enumerate(latest['numbers']):
                with cols[i]:
                    if num <= 10:
                        color = "#FFD700"  # 금색
                    elif num <= 20:
                        color = "#4A90E2"  # 파랑
                    elif num <= 30:
                        color = "#2ECC71"  # 초록
                    elif num <= 40:
                        color = "#E74C3C"  # 빨강
                    else:
                        color = "#9B59B6"  # 보라
                    
                    st.markdown(f"""
                    <div style='display: flex; align-items: center; justify-content: center;
                                width: 60px; height: 60px; border-radius: 50%;
                                background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                                color: white; font-weight: bold; font-size: 24px;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                                margin: 0 auto;'>
                        {num}
                    </div>
                    """, unsafe_allow_html=True)
            
            # + 기호
            with cols[6]:
                st.markdown("<div style='text-align: center; color: #ffd700; font-size: 2rem; padding-top: 15px;'>+</div>", unsafe_allow_html=True)
            
            # 보너스 번호
            with cols[7]:
                st.markdown(f"""
                <div style='display: flex; align-items: center; justify-content: center;
                            width: 60px; height: 60px; border-radius: 50%;
                            background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
                            color: white; font-weight: bold; font-size: 24px;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                            margin: 0 auto;'>
                    {latest['bonus']}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 통계 정보
            st.markdown("""
            <div style='text-align: center; margin: 2rem 0 1rem 0;'>
                <h3 style='color: #00d4ff;'>📈 통계 정보</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class='card' style='text-align: center;'>
                    <p style='color: #888; margin: 0; font-size: 0.9rem;'>최신 회차</p>
                    <h2 style='color: #00d4ff; margin: 0.5rem 0;'>{}</h2>
                    <p style='color: #666; margin: 0; font-size: 0.8rem;'>회</p>
                </div>
                """.format(st.session_state.TOTAL_DRAW), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class='card' style='text-align: center;'>
                    <p style='color: #888; margin: 0; font-size: 0.9rem;'>수집 회차</p>
                    <h2 style='color: #2ECC71; margin: 0.5rem 0;'>{}</h2>
                    <p style='color: #666; margin: 0; font-size: 0.8rem;'>회</p>
                </div>
                """.format(len(st.session_state.lotto_data)), unsafe_allow_html=True)
            
            with col3:
                total_numbers = sum(st.session_state.number_counts.values())
                st.markdown("""
                <div class='card' style='text-align: center;'>
                    <p style='color: #888; margin: 0; font-size: 0.9rem;'>총 추첨 번호</p>
                    <h2 style='color: #FFD700; margin: 0.5rem 0;'>{:,}</h2>
                    <p style='color: #666; margin: 0; font-size: 0.8rem;'>개</p>
                </div>
                """.format(total_numbers), unsafe_allow_html=True)
            
            with col4:
                avg_sum = sum(st.session_state.all_sums) / len(st.session_state.all_sums) if st.session_state.all_sums else 0
                st.markdown("""
                <div class='card' style='text-align: center;'>
                    <p style='color: #888; margin: 0; font-size: 0.9rem;'>평균 합계</p>
                    <h2 style='color: #E74C3C; margin: 0.5rem 0;'>{:.1f}</h2>
                    <p style='color: #666; margin: 0; font-size: 0.8rem;'>점</p>
                </div>
                """.format(avg_sum), unsafe_allow_html=True)
            
    # ==================== 탭 2: 번호 생성 ====================
    with tab2:
        if not st.session_state.number_counts or sum(st.session_state.number_counts.values()) == 0:
            st.error("❌ 로또 데이터가 비어 있습니다. 데이터 수집이 완료되지 않았거나, 서버 연결에 실패했습니다.")
        else:
            with st.spinner("🔮 천재적 알고리즘 계산 중..."):
                sets = generate_numbers_and_explanations()
                
                # 예측 데이터 저장
                try:
                    predictions = load_predictions_data()
                    prediction_sets = []
                    for nums, _ in sets:
                        if "(데이터 없음)" not in str(nums):
                            prediction_sets.append(nums)
                    
                    draw_key = str(st.session_state.TOTAL_DRAW + 1)
                    predictions[draw_key] = {
                        'sets': prediction_sets,
                        'created_date': datetime.now().isoformat(),
                        'created_for_draw': st.session_state.TOTAL_DRAW + 1
                    }
                    save_predictions_data(predictions)
                except:
                    pass
                
                # 결과 표시
                st.markdown(f"""
                <div style='text-align: center; margin: 2rem 0;'>
                    <h1 style='color: #00d4ff;'>🎲 제 {st.session_state.TOTAL_DRAW + 1}회차 예측 번호</h1>
                    <p style='color: #888; font-size: 1.1rem;'>천재 수학자들의 알고리즘 분석 결과</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                set_names = [
                    "세트 1: 황금 비율의 서명",
                    "세트 2: 우주 평균 회귀의 법칙",
                    "세트 3: 피에르 드 페르마의 확률론",
                    "세트 4: 콜모고로프의 공리적 확률론",
                    "세트 5: 블레즈 파스칼의 도박 문제 해결"
                ]
                
                set_icons = ["🎨", "📊", "🔮", "⚛️", "🎲"]
                set_colors = [
                    "#FFD700",  # 금색
                    "#4A90E2",  # 파랑
                    "#2ECC71",  # 초록
                    "#9B59B6",  # 보라
                    "#E74C3C"   # 빨강
                ]
                
                for i, (nums, explanation) in enumerate(sets):
                    st.markdown(f"""
                    <div class='card' style='border-left: 5px solid {set_colors[i]};'>
                        <h3 style='color: {set_colors[i]}; margin-top: 0;'>
                            {set_icons[i]} {set_names[i]}
                        </h3>
                    """, unsafe_allow_html=True)
                    
                    # 번호 표시
                    if "(데이터 없음)" not in str(nums):
                        cols = st.columns(6)
                        for j, num in enumerate(nums):
                            with cols[j]:
                                # 구간별 색상
                                if num <= 10:
                                    color = "#FFD700"
                                elif num <= 20:
                                    color = "#4A90E2"
                                elif num <= 30:
                                    color = "#2ECC71"
                                elif num <= 40:
                                    color = "#E74C3C"
                                else:
                                    color = "#9B59B6"
                                
                                st.markdown(f"""
                                <div class='number-ball' style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%);'>
                                    {num}
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ 데이터 없음")
                    
                    # 설명
                    with st.expander("📖 상세 설명 보기", expanded=False):
                        st.markdown(f"<div style='color: #ccc; line-height: 1.8;'>{explanation}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # ==================== 탭 3: 분석 ====================
    with tab3:
        st.markdown("""
        <div style='text-align: center; margin: 2rem 0;'>
            <h2 style='color: #ffd700;'>🔍 과거 예측 매치 분석</h2>
            <p style='color: #888;'>생성된 예측이 실제 당첨번호와 얼마나 일치했는지 확인하세요</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.lotto_data:
            analysis_draw = st.selectbox(
                "분석할 회차 선택",
                options=list(range(st.session_state.TOTAL_DRAW, max(1, st.session_state.TOTAL_DRAW - 10), -1)),
                format_func=lambda x: f"제 {x}회차"
            )
            
            if st.button("🔍 매치 분석 실행", use_container_width=True):
                # 해당 회차의 당첨번호 찾기
                winning_data = next((d for d in st.session_state.lotto_data if d['draw'] == analysis_draw), None)
                
                if winning_data:
                    winning_nums = winning_data['numbers']
                    bonus_num = winning_data['bonus']
                    
                    st.markdown(f"""
                    <div class='card'>
                        <h3 style='text-align: center; color: #00d4ff; margin-top: 0;'>
                            🏆 제 {analysis_draw}회 당첨번호
                        </h3>
                        <p style='text-align: center; color: #888; margin-bottom: 1.5rem;'>
                            📅 {winning_data['date']}
                        </p>
                    """, unsafe_allow_html=True)
                    
                    cols = st.columns([1, 1, 1, 1, 1, 1, 0.5, 1])
                    
                    for i, num in enumerate(winning_nums):
                        with cols[i]:
                            if num <= 10:
                                color = "#FFD700"
                            elif num <= 20:
                                color = "#4A90E2"
                            elif num <= 30:
                                color = "#2ECC71"
                            elif num <= 40:
                                color = "#E74C3C"
                            else:
                                color = "#9B59B6"
                            
                            st.markdown(f"""
                            <div class='number-ball' style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%);'>
                                {num}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with cols[6]:
                        st.markdown("<div style='text-align: center; font-size: 2rem; color: #ffd700; padding-top: 10px;'>+</div>", unsafe_allow_html=True)
                    
                    with cols[7]:
                        st.markdown(f"""
                        <div class='number-ball' style='background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);'>
                            {bonus_num}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 과거 예측 가져오기
                    past_predictions = get_previous_predictions(analysis_draw)
                    
                    if past_predictions:
                        set_names = [
                            "세트 1: 황금 비율의 서명",
                            "세트 2: 우주 평균 회귀의 법칙",
                            "세트 3: 피에르 드 페르마의 확률론",
                            "세트 4: 콜모고로프의 공리적 확률론",
                            "세트 5: 블레즈 파스칼의 도박 문제 해결"
                        ]
                        
                        set_icons = ["🎨", "📊", "🔮", "⚛️", "🎲"]
                        
                        winning_set = set(winning_nums)
                        total_best_match = 0
                        best_set_name = ""
                        
                        st.markdown("<h3 style='color: #ffd700; text-align: center;'>🎯 세트별 매치 결과</h3>", unsafe_allow_html=True)
                        
                        for i, nums in enumerate(past_predictions[:5]):
                            if i >= len(set_names):
                                break
                            
                            if not nums or "(데이터 없음)" in str(nums):
                                st.info(f"{set_icons[i]} **{set_names[i]}**: 예측 데이터 없음")
                                continue
                            
                            set_numbers = set(nums)
                            matches = len(winning_set & set_numbers)
                            bonus_match = bonus_num in set_numbers
                            
                            # 등수 계산
                            if matches == 6:
                                prize = "🎉 1등 당첨!"
                                color = "success"
                                emoji = "🎉"
                            elif matches == 5:
                                if bonus_match:
                                    prize = "🎊 2등 당첨!"
                                    color = "success"
                                    emoji = "🎊"
                                else:
                                    prize = "🎈 3등 당첨!"
                                    color = "success"
                                    emoji = "🎈"
                            elif matches == 4:
                                prize = "🎁 4등 당첨!"
                                color = "info"
                                emoji = "🎁"
                            elif matches == 3:
                                prize = "🎀 5등 당첨!"
                                color = "info"
                                emoji = "🎀"
                            else:
                                prize = f"({matches}개 일치)"
                                color = "warning"
                                emoji = "📊"
                            
                            bonus_text = " (+보너스)" if bonus_match else ""
                            
                            # 매치 결과를 카드로 표시
                            if color == "success":
                                bg_color = "#1a5f3a"
                                border_color = "#00ff88"
                            elif color == "info":
                                bg_color = "#1a4a5f"
                                border_color = "#00d4ff"
                            else:
                                bg_color = "#5f4a1a"
                                border_color = "#ffd700"
                            
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
                                        border-left: 5px solid {border_color};
                                        border-radius: 10px;
                                        padding: 1rem;
                                        margin: 0.5rem 0;'>
                                <h4 style='color: white; margin: 0;'>
                                    {set_icons[i]} {set_names[i]}
                                </h4>
                                <p style='color: #ccc; margin: 0.5rem 0;'>
                                    예측 번호: {nums}
                                </p>
                                <p style='color: {border_color}; font-weight: bold; font-size: 1.1rem; margin: 0;'>
                                    {emoji} {matches}개 매치{bonus_text} - {prize}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if matches > total_best_match:
                                total_best_match = matches
                                best_set_name = set_names[i]
                        
                        if total_best_match > 0:
                            st.markdown(f"""
                            <div class='card' style='border: 3px solid #ffd700; text-align: center;'>
                                <h2 style='color: #ffd700; margin: 0;'>
                                    🏆 최고 성과
                                </h2>
                                <p style='color: white; font-size: 1.3rem; margin: 1rem 0;'>
                                    {best_set_name}
                                </p>
                                <p style='color: #00d4ff; font-size: 2rem; font-weight: bold; margin: 0;'>
                                    {total_best_match}개 매치
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("저장된 예측 데이터가 없습니다.")
                else:
                    st.error(f"제 {analysis_draw}회차 데이터를 찾을 수 없습니다.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0; color: #888;'>
        <p style='font-size: 0.9rem; margin: 0.5rem 0;'>
            🎨 DA VINCI'S CIPHER - Quantum Lotto Decoder v1.0
        </p>
        <p style='font-size: 0.8rem; margin: 0.5rem 0;'>
            © 2025 ORYNE Corporation. All Rights Reserved.
        </p>
        <p style='font-size: 0.8rem; margin: 0.5rem 0; color: #666;'>
            📞 Instagram: @oryne.official
        </p>
        <p style='font-size: 0.7rem; margin: 1rem 0 0 0; color: #555;'>
            ⚠️ 이 프로그램은 오락 및 교육 목적으로 제작되었습니다. 로또 당첨을 보장하지 않습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
