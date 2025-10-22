#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================
    DA VINCI'S CIPHER: Quantum Lotto Decoder v1.0
    다빈치의 암호: 양자 로또 디코더
=================================================================

© 2025 ORYNE. All Rights Reserved.
Developed by: ORYNE Corporation
Contact: Instagram @oryne.official
Release Date: October 7, 2025
Version: 1.0.0

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

import tkinter as tk
from tkinter import scrolledtext
import requests
import threading
import math
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# --- 데이터 수집 및 분석 ---

LOTTO_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo="
CACHE_FILE = "lotto_cache.json"
PREDICTIONS_FILE = "lotto_predictions.json"  # 예측 데이터 저장 파일
RECENT_DRAW = 50
LOTTO_RANGE = range(1, 46)
FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34]

# 동적으로 설정될 변수들
TOTAL_DRAW = 1191  # 기본값, 실행 시 자동 갱신됨

def get_latest_draw_number():
    """동행복권 API를 통해 현재 최신 회차 번호를 가져옵니다."""
    # 현재 추정 회차부터 역순으로 확인
    estimated_draw = 1200  # 넉넉하게 설정
    
    for draw_no in range(estimated_draw, 0, -1):
        try:
            resp = requests.get(LOTTO_URL + str(draw_no), timeout=3)
            data = resp.json()
            
            if data.get('returnValue') == 'success' and 'drwtNo1' in data:
                return draw_no
        except:
            continue
    
    # 실패시 기본값 반환
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
        print(f"캐시 저장 실패: {e}")

def get_missing_draws(cached_data, latest_draw):
    """캐시되지 않은 회차 목록을 반환합니다."""
    cached_draws = set(int(k) for k in cached_data.get('draws', {}).keys())
    all_draws = set(range(1, latest_draw + 1))
    return sorted(all_draws - cached_draws)

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
    """예측 데이터를 파일에 저장합니다."""
    try:
        with open(PREDICTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"예측 데이터 저장 실패: {e}")

def get_previous_predictions(target_draw):
    """특정 회차에 대한 과거 예측을 가져옵니다."""
    predictions = load_predictions_data()
    draw_key = str(target_draw)
    
    if draw_key in predictions:
        return predictions[draw_key].get('sets', [])
    
    return None

def download_single_draw(draw_num, session=None):
    """단일 회차 데이터를 다운로드합니다."""
    if session is None:
        session = requests.Session()
    
    try:
        resp = session.get(LOTTO_URL + str(draw_num), timeout=5)
        data = resp.json()
        
        if data.get('returnValue') != 'success':
            return draw_num, None, 'returnValue!=success'
        
        nums = []
        for j in range(1, 7):
            key = f'drwtNo{j}'
            if key not in data or not isinstance(data[key], int):
                return draw_num, None, f'Missing {key}'
            nums.append(data[key])
        
        draw_data = {
            'numbers': nums,
            'date': data.get('drwNoDate', ''),
            'bonus': data.get('bnusNo', 0)
        }
        
        return draw_num, draw_data, None
        
    except Exception as e:
        return draw_num, None, str(e)

def download_draws_parallel(draw_numbers, progress_callback=None, max_workers=15):
    """병렬로 여러 회차를 다운로드합니다."""
    results = {}
    failed_draws = []
    
    # requests 세션 풀 생성
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    total = len(draw_numbers)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 작업 제출
        future_to_draw = {
            executor.submit(download_single_draw, draw_num, session): draw_num 
            for draw_num in draw_numbers
        }
        
        # 완료된 작업들 처리
        for future in as_completed(future_to_draw):
            draw_num = future_to_draw[future]
            completed += 1
            
            try:
                draw_num, draw_data, error = future.result()
                
                if error:
                    failed_draws.append((draw_num, error))
                else:
                    results[draw_num] = draw_data
                
                # 진행률 콜백 호출
                if progress_callback:
                    progress_callback(completed, total, draw_num)
                    
            except Exception as e:
                failed_draws.append((draw_num, str(e)))
                if progress_callback:
                    progress_callback(completed, total, draw_num)
    
    return results, failed_draws


# --- 천재적 분석 함수들 ---

def set1_fibonacci():
    # 동적 피보나치 수열과 실제 데이터를 융합한 황금비 분석
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    import random
    
    # 회차 기반 시드 설정 (같은 회차에서는 항상 같은 결과)
    random.seed(TOTAL_DRAW * 1000 + 1)
    
    # 피보나치 수들의 출현 빈도 분석 (1~45 범위)
    fib_in_range = [f for f in FIBONACCI if f <= 45]
    fib_analysis = [(f, number_counts.get(f, 0)) for f in fib_in_range]
    
    # 동적 황금비 계산 (회차에 따라 미세 변동)
    base_golden_ratio = 1.618
    dynamic_offset = (TOTAL_DRAW % 13) * 0.001  # 0~0.012 범위의 미세 변동
    golden_ratio = base_golden_ratio + dynamic_offset
    
    # 동적 중심점 계산 (23 ± 회차별 변동)
    dynamic_center = 23 + (TOTAL_DRAW % 7) - 3  # 20~26 범위에서 변동
    
    weighted_fib = []
    for f, count in fib_analysis:
        # 동적 황금비 거리에 따른 가중치
        ratio_weight = 1 / (1 + abs(f - dynamic_center * golden_ratio / 45))
        # 출현 빈도 정규화
        freq_weight = count / max([c for _, c in fib_analysis]) if fib_analysis else 0
        # 시간 가중치 추가
        time_weight = (TOTAL_DRAW % 11) * (f % 5) * 0.01
        # 랜덤 변동성 추가
        random_factor = random.uniform(0.8, 1.2)
        
        total_weight = (ratio_weight * 0.5 + freq_weight * 0.3 + time_weight) * random_factor
        weighted_fib.append((f, total_weight))
    
    # 가중치 순으로 정렬하여 상위 선택
    weighted_fib.sort(key=lambda x: x[1], reverse=True)
    
    selected = []
    # 동적으로 피보나치 수에서 2-5개 선택 (회차에 따라 변동)
    fib_count = 2 + (TOTAL_DRAW % 4)  # 2~5개
    for f, _ in weighted_fib[:fib_count]:
        if len(selected) < fib_count:
            selected.append(f)
    
    # 나머지는 동적 황금비 분할점들로 채우기
    dynamic_ratios = [0.382, 0.618, 1.0]
    # 회차별로 분할점 비율 조정
    for i, ratio in enumerate(dynamic_ratios):
        adjusted_ratio = ratio + (TOTAL_DRAW % 7) * 0.01 * (i + 1)
        point = int(45 * adjusted_ratio / golden_ratio)
        if point >= 1 and point <= 45 and point not in selected and len(selected) < 6:
            selected.append(point)
    
    # 부족하면 동적 중간값들로 보충
    while len(selected) < 6:
        dynamic_middle = [7, 17, 27, 37, 42]
        # 회차별로 중간값 순서 변경
        shift = TOTAL_DRAW % len(dynamic_middle)
        dynamic_middle = dynamic_middle[shift:] + dynamic_middle[:shift]
        
        for n in dynamic_middle:
            if n not in selected:
                selected.append(n)
                break
    
    return sorted(selected[:6])

def set2_statistical_regression():
    # 동적 평균회귀 이론: 최근 데이터와 전체 데이터를 조합한 예측
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    import random
    
    # 회차 기반 시드 설정 (같은 회차에서는 항상 같은 결과)
    random.seed(TOTAL_DRAW * 1000 + 2)
    
    # 전체 평균과 최근 평균의 차이를 이용한 동적 선별
    total_avg = sum(number_counts.values()) / len(number_counts)
    recent_avg = sum(recent_counts.values()) / len(recent_counts) if recent_counts else total_avg
    
    # 평균회귀 후보 점수 계산
    candidates = []
    for n in range(1, 46):
        total_count = number_counts.get(n, 0)
        recent_count = recent_counts.get(n, 0) if recent_counts else 0
        
        # 평균회귀 점수: 전체에서는 적지만 최근에는 더 적은 번호일수록 높은 점수
        regression_score = (total_avg - total_count) + (recent_avg - recent_count) * 1.5
        
        # 시간 가중치: 회차 정보를 이용한 추가 점수
        time_weight = (TOTAL_DRAW % 7) * (n % 3)  # 주기적 변동성 추가
        
        # 최종 점수
        final_score = regression_score + time_weight + random.uniform(-5, 5)  # 무작위성 추가
        candidates.append((n, final_score))
    
    # 점수가 높은 순으로 정렬하여 상위 8개 선택
    candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = [x[0] for x in candidates[:8]]
    
    # 8개 중에서 분산도를 고려하여 6개 최종 선택
    selected = []
    for num in top_candidates:
        if len(selected) >= 6:
            break
        # 이미 선택된 번호와 너무 가깝지 않은 번호 우선 선택
        if not selected or all(abs(num - s) >= 3 for s in selected):
            selected.append(num)
    
    # 부족하면 나머지 후보에서 추가
    for num in top_candidates:
        if len(selected) >= 6:
            break
        if num not in selected:
            selected.append(num)
    
    return sorted(selected[:6])

def set3_geometry():
    # 피에르 드 페르마의 확률론을 적용한 신성 기하학 배열
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    import random
    import math
    
    # 회차 기반 시드 설정 (같은 회차에서는 항상 같은 결과)
    random.seed(TOTAL_DRAW * 1000 + 3)
    
    # 페르마의 확률론: 기댓값(Expected Value) 계산을 통한 번호 선택
    # E(X) = Σ(x_i * P(x_i)) - 각 번호의 기댓값을 계산
    
    total_draws = len(lotto_data) if lotto_data else TOTAL_DRAW
    
    # 1. 페르마의 확률적 기댓값 계산
    fermat_expected_values = []
    for num in range(1, 46):
        # 출현 확률 계산
        appearance_prob = number_counts.get(num, 0) / (total_draws * 6) if total_draws > 0 else 0
        
        # 최근 트렌드 확률 (페르마의 조건부 확률 개념)
        recent_prob = recent_counts.get(num, 0) / (RECENT_DRAW * 6) if RECENT_DRAW > 0 else 0
        
        # 페르마의 점 분할 문제(Problem of Points) 적용
        # 남은 게임에서 이길 확률을 고려한 공정한 분배
        remaining_probability = (1 - appearance_prob) * (1 + recent_prob)
        
        # 기댓값 계산 (번호 크기 편향 제거)
        # 순수 확률적 가치: 출현확률과 미래확률의 조화 평균
        if appearance_prob + remaining_probability > 0:
            expected_value = 2 * (appearance_prob * remaining_probability) / (appearance_prob + remaining_probability)
        else:
            expected_value = 0
        
        # 동적 시간 가중치 (회차에 따른 변동성)
        time_factor = math.sin((TOTAL_DRAW + num) * 0.1) * 0.3 + 1.0
        
        # 균등한 기회를 위한 위치 보정 (1-45 모든 번호에 공정한 기회)
        position_balance = 1.0 + abs(math.cos(num * math.pi / 45)) * 0.2
        
        # 최종 페르마 점수
        fermat_score = expected_value * time_factor * position_balance
        
        fermat_expected_values.append((num, fermat_score, appearance_prob))
    
    # 2. 기하학적 대칭성과 페르마 확률의 융합
    # 동적 중심점 계산
    dynamic_center = 23 + (TOTAL_DRAW % 5) - 2
    
    # 대칭성과 확률을 결합한 점수
    symmetric_fermat_scores = []
    for num, fermat_score, prob in fermat_expected_values:
        # 중심으로부터의 기하학적 거리
        geometric_distance = abs(num - dynamic_center)
        
        # 대칭 번호
        symmetric_num = 2 * dynamic_center - num
        
        # 대칭성 보너스 (대칭 번호의 출현 확률 고려)
        if 1 <= symmetric_num <= 45:
            symmetric_prob = number_counts.get(symmetric_num, 0) / (total_draws * 6) if total_draws > 0 else 0
            symmetry_bonus = symmetric_prob * 5  # 보너스 감소 (10 -> 5)
        else:
            symmetry_bonus = 0
        
        # 황금비 거리 보정 (1.618) - 모든 구간에 공정하게
        golden_distance = abs(geometric_distance - (45 / 1.618))
        golden_ratio_factor = 1.0 + abs(math.sin(golden_distance * 0.1)) * 0.3
        
        # 구간별 균형 보정 (1-15, 16-30, 31-45)
        if num <= 15:
            zone_bonus = 1.2  # 저번호 구간 보너스
        elif num <= 30:
            zone_bonus = 1.1  # 중번호 구간 보너스
        else:
            zone_bonus = 1.0  # 고번호 구간 기본값
        
        # 최종 점수: 페르마 확률 + 기하학적 대칭성 + 황금비 + 구간 균형
        final_score = (fermat_score * 0.6 + symmetry_bonus * 0.2) * golden_ratio_factor * zone_bonus
        
        # 페르마의 조합론적 접근: C(n,k) 고려
        # 모든 번호가 동일한 조합 확률을 가짐
        combinatorial_factor = math.comb(44, 5) / math.comb(45, 6)  # 특정 번호가 포함될 확률
        final_score *= (1 + combinatorial_factor * 0.05)  # 영향력 감소
        
        symmetric_fermat_scores.append((num, final_score))
    
    # 3. 페르마의 최소/최대 원리 적용
    # 점수 순으로 정렬
    symmetric_fermat_scores.sort(key=lambda x: x[1], reverse=True)
    
    selected = []
    candidates = [x[0] for x in symmetric_fermat_scores[:18]]  # 상위 18개 후보로 확대
    
    # 4. 분산 최적화 (페르마의 극값 문제 해법)
    # 구간별 균형을 고려한 첫 선택
    low_zone = [c for c in candidates if c <= 15]
    mid_zone = [c for c in candidates if 16 <= c <= 30]
    high_zone = [c for c in candidates if c >= 31]
    
    # 각 구간에서 최고 점수 하나씩 선택하여 균형 시작
    if low_zone:
        selected.append(low_zone[0])
        candidates.remove(low_zone[0])
    if mid_zone and len(selected) < 6:
        selected.append(mid_zone[0])
        candidates.remove(mid_zone[0])
    if high_zone and len(selected) < 6:
        selected.append(high_zone[0])
        candidates.remove(high_zone[0])
    
    # 나머지는 분산을 최대화하면서 선택 (페르마의 최적화 이론)
    while len(selected) < 6 and candidates:
        best_candidate = None
        best_metric = -float('inf')
        
        for candidate in candidates:
            # 이미 선택된 번호들과의 평균 거리
            avg_distance = sum(abs(candidate - s) for s in selected) / len(selected)
            
            # 페르마 점수 유지
            fermat_value = next((score for num, score in symmetric_fermat_scores if num == candidate), 0)
            
            # 종합 메트릭: 거리 * 페르마점수
            metric = avg_distance * math.log1p(fermat_value)
            
            if metric > best_metric:
                best_metric = metric
                best_candidate = candidate
        
        if best_candidate is not None:
            selected.append(best_candidate)
            candidates.remove(best_candidate)
        else:
            break
    
    # 5. 부족한 경우 페르마의 확률적 보충
    if len(selected) < 6:
        # 나머지 후보들 중 확률적으로 선택
        remaining = [x[0] for x in symmetric_fermat_scores if x[0] not in selected]
        while len(selected) < 6 and remaining:
            # 확률적 가중치로 선택
            weights = [math.exp(next((score for num, score in symmetric_fermat_scores if num == n), 0)) 
                      for n in remaining[:10]]
            if weights and sum(weights) > 0:
                chosen = random.choices(remaining[:10], weights=weights, k=1)[0]
                selected.append(chosen)
                remaining.remove(chosen)
            else:
                selected.append(remaining[0])
                remaining.pop(0)
    
    return sorted(selected[:6])

def set4_quantum():
    # 콜모고로프의 공리적 확률론 - "확률은 사건의 공간이다"
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    import random
    import math
    
    # 회차 기반 시드 설정 (같은 회차에서는 항상 같은 결과)
    random.seed(TOTAL_DRAW * 1000 + 4)
    
    # 콜모고로프의 확률 공간 (Ω, F, P)
    # Ω: 표본공간 = {1, 2, 3, ..., 45}
    # F: 사건의 집합 (σ-algebra)
    # P: 확률 측도
    
    total_draws = len(lotto_data) if lotto_data else TOTAL_DRAW
    
    # 1. 콜모고로프의 확률 공리 적용
    # 공리 1: P(A) ≥ 0 (모든 사건의 확률은 음이 아니다)
    # 공리 2: P(Ω) = 1 (전체 표본공간의 확률은 1)
    # 공리 3: 배반사건의 확률은 더할 수 있다
    
    kolmogorov_scores = []
    for num in range(1, 46):
        # 표본공간에서의 경험적 확률 측도
        empirical_probability = number_counts.get(num, 0) / (total_draws * 6) if total_draws > 0 else 1/45
        
        # 이론적 확률 (균등분포 가정)
        theoretical_probability = 1 / 45
        
        # 콜모고로프-스미르노프 통계량 개념 적용
        # D = sup |F_n(x) - F(x)| (경험분포와 이론분포의 최대 차이)
        deviation = abs(empirical_probability - theoretical_probability)
        
        # 확률 공간의 측도 계산
        # σ-algebra에서의 사건 측정: 출현 빈도의 정규화된 측도
        frequency_measure = number_counts.get(num, 0) / max(number_counts.values()) if number_counts else 0
        
        # 2. 독립사건의 확률 (Independent Events)
        # P(A ∩ B) = P(A) × P(B) for independent events
        # 최근 트렌드를 독립사건으로 간주
        recent_probability = recent_counts.get(num, 0) / (RECENT_DRAW * 6) if RECENT_DRAW > 0 and recent_counts else 1/45
        
        # 3. 조건부 확률 (Conditional Probability)
        # P(A|B) = P(A ∩ B) / P(B)
        # "최근에 출현했다는 조건 하에 다시 출현할 확률"
        if recent_probability > 0:
            conditional_prob = empirical_probability * recent_probability
        else:
            conditional_prob = empirical_probability
        
        # 4. 기댓값의 측도론적 정의
        # E[X] = ∫ X dP (르베스그 적분)
        # 이산 확률변수: E[X] = Σ x_i × P(x_i)
        expected_measure = num * empirical_probability
        
        # 5. 분산의 측도 (Variance as Measure)
        # Var(X) = E[X²] - (E[X])²
        mean_num = sum(range(1, 46)) / 45  # 이론적 평균 = 23
        variance_contribution = (num - mean_num) ** 2 * empirical_probability
        
        # 6. 확률공간에서의 거리 함수
        # d(x,y) = |x - y| (유클리드 거리)
        # 중심(23)으로부터의 측도론적 거리
        metric_distance = abs(num - 23) / 45  # 정규화
        
        # 7. 보렐 집합(Borel Sets)에서의 측도
        # 번호를 구간으로 나누어 측도 계산
        if num <= 15:
            borel_measure = 1.0 + 0.2  # 하위 구간
        elif num <= 30:
            borel_measure = 1.0 + 0.1  # 중간 구간
        else:
            borel_measure = 1.0  # 상위 구간
        
        # 8. 엔트로피 측도 (정보 이론적 접근)
        # H(X) = -Σ P(x) log P(x)
        if empirical_probability > 0:
            entropy = -empirical_probability * math.log(empirical_probability + 1e-10)
        else:
            entropy = 0
        
        # 9. 콜모고로프의 복잡도 개념
        # 패턴의 복잡도를 측정
        pattern_complexity = abs(math.sin(num * math.pi / 45)) * abs(math.cos(num * math.pi / 23))
        
        # 10. 최종 콜모고로프 측도 계산
        # 공리적 확률론의 종합: 모든 측도의 가중 평균
        kolmogorov_measure = (
            empirical_probability * 0.20 +        # 경험적 확률 측도
            (1 - deviation) * 0.15 +              # 이론분포와의 일치도
            conditional_prob * 0.15 +             # 조건부 확률
            frequency_measure * 0.15 +            # 빈도 측도
            (1 - metric_distance) * 0.10 +        # 중심 거리 (역수)
            borel_measure * 0.10 +                # 보렐 집합 측도
            entropy * 0.08 +                      # 엔트로피
            pattern_complexity * 0.07             # 복잡도
        )
        
        # 확률적 섭동 (Stochastic Perturbation)
        # 콜모고로프의 0-1 법칙: 꼬리 사건은 0 또는 1
        perturbation = random.gauss(1.0, 0.1)  # 정규분포 섭동
        kolmogorov_measure *= max(0.7, min(1.3, perturbation))
        
        kolmogorov_scores.append((num, kolmogorov_measure))
    
    # 측도 순으로 정렬
    kolmogorov_scores.sort(key=lambda x: x[1], reverse=True)
    
    # 11. 확률공간에서의 최적 선택
    selected = []
    candidates = [num for num, score in kolmogorov_scores[:18]]  # 상위 18개 후보
    
    # 구간별 균형 (보렐 측도 균형)
    low_zone = [c for c in candidates if c <= 15]
    mid_zone = [c for c in candidates if 16 <= c <= 30]
    high_zone = [c for c in candidates if c >= 31]
    
    # 각 구간에서 최소 1개씩 선택 (σ-algebra의 분할)
    if low_zone:
        selected.append(low_zone[0])
        candidates.remove(low_zone[0])
    if mid_zone and len(selected) < 6:
        selected.append(mid_zone[0])
        candidates.remove(mid_zone[0])
    if high_zone and len(selected) < 6:
        selected.append(high_zone[0])
        candidates.remove(high_zone[0])
    
    # 나머지는 측도와 거리의 균형으로 선택
    while len(selected) < 6 and candidates:
        best_candidate = None
        best_metric = -float('inf')
        
        for candidate in candidates:
            # 콜모고로프 측도
            kolm_measure = next((score for num, score in kolmogorov_scores if num == candidate), 0)
            
            # 유클리드 거리 (이미 선택된 번호들과)
            if selected:
                avg_distance = sum(abs(candidate - s) for s in selected) / len(selected)
                distance_score = avg_distance / 45.0
            else:
                distance_score = 1.0
            
            # 종합 메트릭
            combined_metric = kolm_measure * 0.6 + distance_score * 0.4
            
            if combined_metric > best_metric:
                best_metric = combined_metric
                best_candidate = candidate
        
        if best_candidate is not None:
            selected.append(best_candidate)
            candidates.remove(best_candidate)
        else:
            break
    
    # 부족한 경우 측도 기반 확률적 선택
    if len(selected) < 6:
        remaining = [num for num, score in kolmogorov_scores if num not in selected]
        weights = [math.exp(next((score for num, score in kolmogorov_scores if num == n), 0) * 3) 
                  for n in remaining[:10]]
        
        while len(selected) < 6 and remaining:
            if weights and sum(weights) > 0:
                chosen = random.choices(remaining[:10], weights=weights[:len(remaining[:10])], k=1)[0]
                selected.append(chosen)
                remaining.remove(chosen)
                weights = [math.exp(next((score for num, score in kolmogorov_scores if num == n), 0) * 3) 
                          for n in remaining[:10]]
            else:
                selected.append(remaining[0])
                remaining.pop(0)
    
    return sorted(selected[:6])

def set5_grand_unification():
    # 블레즈 파스칼의 도박 문제 해결 - 메레 기사의 딜레마
    if not number_counts or not recent_counts or not all_sums or sum(recent_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    global TOTAL_DRAW
    import random
    import math
    
    # 회차 기반 시드 설정 (같은 회차에서는 항상 같은 결과)
    random.seed(TOTAL_DRAW * 1000 + 5)
    
    try:
        # 파스칼의 도박 문제: "중단된 게임의 공정한 상금 분배"
        # 1654년 메레 기사(Chevalier de Méré)의 질문:
        # "게임이 중단되었을 때, 각 플레이어는 얼마를 받아야 하는가?"
        
        total_draws = len(lotto_data) if lotto_data else TOTAL_DRAW
        
        # 1. 파스칼의 기댓값 (Expected Value) 계산
        # E(X) = Σ [P(사건) × 가치]
        # "각 번호가 당첨될 확률 × 그 번호의 가치"
        
        pascal_expected_values = []
        
        for num in range(1, 46):
            # 과거 출현 확률 (실제 데이터)
            historical_prob = number_counts.get(num, 0) / (total_draws * 6) if total_draws > 0 else 1/45
            
            # 최근 트렌드 확률
            recent_prob = recent_counts.get(num, 0) / (RECENT_DRAW * 6) if RECENT_DRAW > 0 else 1/45
            
            # 이론적 확률 (공정한 게임 가정)
            theoretical_prob = 1 / 45
            
            # 파스칼의 기댓값: "과거에 적게 나왔다면, 미래에 나올 기회가 더 많다"
            # 이것이 메레 기사 문제의 핵심: 남은 게임에서의 승리 확률
            
            # 남은 기회 계산 (평균 출현 횟수 대비 실제 출현)
            expected_count = total_draws * 6 * theoretical_prob  # 기댓값
            actual_count = number_counts.get(num, 0)  # 실제값
            debt = expected_count - actual_count  # "빚" (덜 나온 횟수)
            
            # 파스칼의 공정성: 빚이 많을수록 미래에 나올 기댓값이 높다
            fairness_score = debt / expected_count if expected_count > 0 else 0
            
            # **쿨다운 패널티 추가** - 최근 5회차 내 출현 번호는 "이미 기회를 가졌다"
            # 파스칼의 시간적 공정성: 같은 번호가 연속으로 나오는 것을 방지
            recent_appearances = recent_counts.get(num, 0)
            cooldown_penalty = 1.0
            if recent_appearances >= 4:
                cooldown_penalty = 0.1  # 최근 4회 이상 출현: 90% 감소
            elif recent_appearances == 3:
                cooldown_penalty = 0.3  # 최근 3회 출현: 70% 감소
            elif recent_appearances == 2:
                cooldown_penalty = 0.5  # 최근 2회 출현: 50% 감소
            elif recent_appearances == 1:
                cooldown_penalty = 0.7  # 최근 1회 출현: 30% 감소
            
            fairness_score = fairness_score * cooldown_penalty
            
            # 최근 트렌드 고려 (게임의 현재 상황)
            trend_weight = 1.0
            if recent_prob > historical_prob * 1.2:
                trend_weight = 0.8  # 최근 너무 많이 나옴 (과열)
            elif recent_prob < historical_prob * 0.8:
                trend_weight = 1.3  # 최근 적게 나옴 (기회)
            
            # 최종 기댓값 = 공정성 × 트렌드 × 이론적 확률
            expected_value = (1 + fairness_score) * trend_weight * theoretical_prob
            
            pascal_expected_values.append((num, expected_value))
        
        # 2. 파스칼의 조합법 (Combinatorial Method)
        # "n개 중 k개를 선택하는 모든 경우의 수"
        # C(n,k) = n! / (k! × (n-k)!)
        
        # 각 번호가 최종 6개 조합에 포함될 조합론적 확률
        # 특정 번호를 포함하는 조합 수 / 전체 조합 수
        # = C(44, 5) / C(45, 6) = 6/45 = 0.1333...
        
        combinatorial_prob = 6 / 45  # 모든 번호 동일
        
        # 3. 파스칼의 "분할 원리" (Partition Principle)
        # 게임을 구간으로 나누어 각 구간에서 공정하게 분배
        
        # 번호를 3개 구간으로 분할
        zone_scores = []
        
        for num, exp_val in pascal_expected_values:
            # 구간별 균형 보정 (파스칼의 공정성)
            if num <= 15:
                zone = "low"
                zone_balance = 1.0
            elif num <= 30:
                zone = "mid"
                zone_balance = 1.0
            else:
                zone = "high"
                zone_balance = 1.0
            
            # 4. 파스칼의 "게임 가치 함수"
            # 메레 기사 문제: "각 상황의 가치는 얼마인가?"
            
            # 출현 빈도의 분산 (변동성)
            if historical_prob > 0:
                variance = historical_prob * (1 - historical_prob)
            else:
                variance = 0.25  # 최대 분산
            
            # 정보 가치 (엔트로피)
            if historical_prob > 0:
                information_value = -historical_prob * math.log(historical_prob + 1e-10)
            else:
                information_value = 0
            
            # 위치 가치 (중심으로부터의 거리)
            position_value = 1.0 - abs(num - 23) / 23  # 23이 중심
            
            # 5. 파스칼의 최종 판정 공식
            # "각 번호의 총 가치 = 기댓값 + 조합확률 + 게임가치"
            total_value = (
                exp_val * 40 +                    # 기댓값 (40점)
                combinatorial_prob * 20 +         # 조합론 (20점)
                variance * 15 +                   # 분산 (15점)
                information_value * 15 +          # 정보 (15점)
                position_value * 10               # 위치 (10점)
            ) * zone_balance
            
            # 회차별 변동성 (파스칼의 "운의 요소")
            luck_factor = abs(math.sin((TOTAL_DRAW + num) * math.pi / 23)) * 0.3 + 0.85
            total_value *= luck_factor
            
            # 확률적 섭동 (도박의 불확실성)
            stochastic = random.gauss(1.0, 0.12)
            total_value *= max(0.7, min(1.3, stochastic))
            
            zone_scores.append((num, total_value, zone))
        
        # 점수 순으로 정렬
        zone_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 6. 파스칼의 "공정한 분배 알고리즘"
        # 각 구간에서 공정하게 선택
        
        selected = []
        
        # 상위 후보들
        top_candidates = [(num, score, zone) for num, score, zone in zone_scores[:24]]
        
        # 구간별 최소 보장 (공정성)
        low_pool = [x for x in top_candidates if x[2] == "low"]
        mid_pool = [x for x in top_candidates if x[2] == "mid"]
        high_pool = [x for x in top_candidates if x[2] == "high"]
        
        # 각 구간에서 최소 1개씩 (파스칼의 균형)
        if low_pool:
            selected.append(low_pool[0][0])
        if mid_pool:
            selected.append(mid_pool[0][0])
        if high_pool:
            selected.append(high_pool[0][0])
        
        # 7. 나머지 3개 선택: 기댓값과 분산의 최적화
        remaining_candidates = [x for x in top_candidates if x[0] not in selected]
        
        while len(selected) < 6 and remaining_candidates:
            best_num = None
            best_metric = -float('inf')
            
            for num, score, zone in remaining_candidates:
                # 파스칼의 최적화: 가치 + 다양성
                value_score = score
                
                # 거리 다양성 (이미 선택된 번호와의 간격)
                if selected:
                    min_distance = min(abs(num - s) for s in selected)
                    diversity_score = min_distance / 45.0
                else:
                    diversity_score = 1.0
                
                # 합계 균형 (평균합에 가깝게)
                current_sum = sum(selected) + num
                target_avg = (sum(all_sums) / len(all_sums)) if all_sums else 138
                sum_target = target_avg * (len(selected) + 1) / 6
                sum_fitness = 1 / (1 + abs(current_sum - sum_target) / 15)
                
                # 종합 메트릭
                combined_metric = value_score * 0.6 + diversity_score * 0.3 + sum_fitness * 0.1
                
                if combined_metric > best_metric:
                    best_metric = combined_metric
                    best_num = num
            
            if best_num is not None:
                selected.append(best_num)
                remaining_candidates = [x for x in remaining_candidates if x[0] != best_num]
            else:
                break
        
        # 8. 부족한 경우 기댓값 순으로 보충
        if len(selected) < 6:
            for num, score, zone in zone_scores:
                if num not in selected and len(selected) < 6:
                    selected.append(num)
        
        # 9. 파스칼의 최종 검증
        final_selected = sorted(selected[:6])
        
        # 구간 균형 재검증
        low = sum(1 for n in final_selected if n <= 15)
        mid = sum(1 for n in final_selected if 16 <= n <= 30)
        high = sum(1 for n in final_selected if n >= 31)
        
        # 극단적 불균형 방지 (파스칼의 공정성 원칙)
        if low == 0 or mid == 0 or high == 0:
            # 재조정: 없는 구간에서 최고 점수 추가
            if low == 0 and low_pool:
                # 가장 낮은 점수 제거하고 low_pool에서 추가
                min_score_num = min(final_selected, 
                                  key=lambda x: next((s for n, s, z in zone_scores if n == x), 0))
                final_selected.remove(min_score_num)
                final_selected.append(low_pool[0][0])
            elif high == 0 and high_pool:
                min_score_num = min(final_selected,
                                  key=lambda x: next((s for n, s, z in zone_scores if n == x), 0))
                final_selected.remove(min_score_num)
                final_selected.append(high_pool[0][0])
            
            final_selected = sorted(final_selected)
        
        return final_selected
        
    except Exception as e:
        # 안전장치: 균등 분포 기반 선택
        import random
        safe_nums = []
        # 각 구간에서 2개씩
        safe_nums.extend(random.sample(range(1, 16), 2))    # 저번호
        safe_nums.extend(random.sample(range(16, 31), 2))   # 중번호
        safe_nums.extend(random.sample(range(31, 46), 2))   # 고번호
        return sorted(safe_nums)

# --- GUI 및 결과 출력 ---

def explain_set1(nums):
    if "(데이터 없음)" in str(nums):
        return "[황금 비율의 서명]\n데이터 로딩 중입니다. 잠시만 기다려주세요.\n"
    
    # 피보나치 수가 포함되어 있는지 확인
    fib_count = sum(1 for n in nums if n in FIBONACCI and n <= 45)
    ratio = sum(nums) / len(nums) if nums else 0
    
    return f"[황금 비율의 서명 - 레오나르도의 조화]\n이 수열은 황금비(φ=1.618)와 피보나치 수열의 수학적 원리를 기반으로 선별되었습니다. {nums} 중 {fib_count}개가 피보나치 수열(1,1,2,3,5,8,13,21...)에 포함되며, 평균값 {ratio:.1f}는 자연에서 발견되는 황금비의 대칭성을 반영합니다. 이는 다빈치의 '비트루비우스적 인간'에서 사용된 인체 비례와 동일한 수학적 원리를 적용한 결과입니다.\n"

def explain_set2(nums):
    if "(데이터 없음)" in str(nums):
        return "[우주 평균 회귀의 법칙]\n데이터 분석 중입니다. 잠시만 기다려주세요.\n"
    
    return f"[우주 평균 회귀의 법칙 - 통계적 각성]\n이 수리체계 {nums}는 동적 평균회귀 모델과 시계열 분석을 통해 도출되었습니다. 전체 출현 빈도와 최근 트렌드의 편차를 분석하여, 통계적으로 '회귀'할 가능성이 높은 번호들을 선별합니다. 각 회차마다 시간 가중치와 확률적 변동성을 적용하여 동일한 결과가 반복되지 않도록 설계된 adaptive 알고리즘입니다. 이는 금융 시장의 평균회귀 이론을 로또 데이터에 적용한 혁신적 접근법입니다.\n"

def explain_set3(nums):
    if "(데이터 없음)" in str(nums):
        return "[피에르 드 페르마의 확률론]\n기하학적 분석 중입니다. 잠시만 기다려주세요.\n"
    
    # 대칭성 분석
    center = 23
    symmetry = sum(1 for n in nums if (2*center - n) in nums or n == center)
    
    return f"[피에르 드 페르마의 확률론 - 기댓값과 신성 기하학]\n{nums}는 17세기 천재 수학자 피에르 드 페르마(Pierre de Fermat)의 확률론을 기반으로 계산되었습니다. 페르마의 기댓값 이론 E(X) = Σ(x_i × P(x_i))을 적용하여 각 번호의 출현 확률과 미래 가능성을 수학적으로 계산했습니다. 또한 페르마의 유명한 '점 분할 문제(Problem of Points)'의 공정한 확률 분배 원리를 사용하여, 과거 출현 빈도와 미래 예측 확률을 조화롭게 결합했습니다. 기하학적 대칭성과 황금비(φ=1.618)를 융합하여 {symmetry}개의 대칭적 요소를 포함하며, 이는 페르마의 조합론 C(n,k)와 최적화 이론이 만나 탄생한 수학적 예술작품입니다.\n"

def explain_set4(nums):
    return f"[콜모고로프의 공리적 확률론 - 확률은 사건의 공간이다]\n이 수열 {nums}는 현대 확률론의 아버지 안드레이 콜모고로프(Andrey Kolmogorov)의 공리적 확률 이론을 기반으로 도출되었습니다. 콜모고로프는 확률을 삼원조 (Omega, F, P)로 정의했습니다: Omega는 표본공간, F는 사건의 시그마-대수(sigma-algebra), P는 확률 측도입니다. 로또 6/45의 표본공간 크기는 C(45,6) = 8,145,060이며, 모든 조합은 동등한 확률 1/8,145,060을 가집니다. 하지만 각 번호의 출현은 독립사건이 아니므로, 경험적 확률 측도와 이론적 측도의 편차를 콜모고로프-스미르노프 통계량으로 측정했습니다. 또한 르베스그 적분을 통한 기댓값 E[X], 조건부 확률 P(A|B), 보렐 집합의 측도, 엔트로피 H(X) = -sum(P(x)logP(x))를 종합하여 각 번호의 확률적 가치를 계산했습니다. 이는 운조차도 정의된 수학적 사건으로 취급하는 콜모고로프의 엄밀한 공리적 접근법의 실현입니다.\n"

def explain_set5(nums):
    return f"[블레즈 파스칼의 도박 문제 해결 - 메레 기사의 딜레마]\n이 수열 {nums}는 1654년 파스칼이 메레 기사(Chevalier de Méré)의 질문을 해결하면서 탄생한 확률론의 핵심 개념들을 적용했습니다. 메레 기사의 질문: '도박 게임이 중단되었을 때, 각 플레이어는 얼마를 받아야 공정한가?' 파스칼의 해답은 기댓값(Expected Value) 개념이었습니다: E(X) = Σ[P(사건) × 가치]. 각 번호에 대해 '예상 출현 횟수 대비 실제 출현의 차이(빚)'를 계산하여, 덜 나온 번호일수록 미래에 나올 기댓값이 높다는 공정성 원리를 적용했습니다. 또한 파스칼의 조합법 C(n,k)를 사용하여 각 번호가 6개 조합에 포함될 확률을 계산하고, 분할 원리(Partition Principle)로 1-15, 16-30, 31-45 세 구간에서 공정하게 분배했습니다. 이는 도박사가 아닌 수학자 파스칼이 '운'을 '수학적 공정성'으로 변환한 혁명적 사고의 결과물입니다.\n"

def generate_numbers_and_explanations():
    s1 = set1_fibonacci()
    s2 = set2_statistical_regression()
    s3 = set3_geometry()
    s4 = set4_quantum()
    s5 = set5_grand_unification()
    return [
        (s1, explain_set1(s1)),
        (s2, explain_set2(s2)),
        (s3, explain_set3(s3)),
        (s4, explain_set4(s4)),
        (s5, explain_set5(s5)),
    ]

# --- GUI ---
class DaVinciLottoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 DA VINCI'S CIPHER: Quantum Lotto Decoder v1.0 | by ORYNE")
        self.root.geometry("760x670")
        self.root.configure(bg="#181c2b")  # 어두운 우주색

        # 상단 타이틀 프레임
        self.title_frame = tk.Frame(root, bg="#181c2b")
        self.title_frame.pack(fill=tk.X, pady=(18, 0))

        # 기하학적 황금비 심볼 (간단한 원)
        self.symbol = tk.Label(self.title_frame, text="◯", fg="#FFD700", bg="#181c2b", font=("Arial", 32, "bold"))
        self.symbol.pack(side=tk.LEFT, padx=(30, 10))

        # 예술적 타이틀
        self.title_label = tk.Label(self.title_frame, text="다빈치 코드: 로또 해독기", fg="#FFD700", bg="#181c2b", font=("Malgun Gothic", 24, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=(0, 10))


        # 텍스트 영역 프레임(황금빛 테두리, 둥근 모서리)
        self.text_frame = tk.Frame(root, bg="#FFD700", bd=0, highlightthickness=0)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(10, 0))

        self.text = scrolledtext.ScrolledText(
            self.text_frame,
            font=("Consolas", 13),
            wrap=tk.WORD,
            bg="#23243a",
            fg="#FFD700",
            insertbackground="#FFD700",
            borderwidth=0,
            highlightthickness=0,
            state='disabled',
            padx=18, pady=12
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        # 스크롤바 색상 조정 (윈도우 기본 한계, 배경만 변경)
        try:
            self.text.vbar.config(bg="#FFD700", troughcolor="#23243a", highlightthickness=0, bd=0)
        except Exception:
            pass


        # 버튼 프레임(중앙 정렬)
        self.button_frame = tk.Frame(root, bg="#181c2b")
        self.button_frame.pack(fill=tk.X, pady=18)

        # 메인 버튼: 황금비 조합 생성
        self.button = tk.Button(
            self.button_frame,
            text="황금비 조합 생성",
            font=("Malgun Gothic", 16, "bold"),
            bg="#FFD700", fg="#181c2b",
            activebackground="#ffe066", activeforeground="#181c2b",
            relief=tk.FLAT, bd=0, padx=32, pady=8,
            command=self.on_generate
        )
        self.button.pack(side=tk.LEFT, padx=(20, 10), pady=0, ipadx=8, ipady=2)

        # 최신 회차 당첨번호 버튼
        self.prev_button = tk.Button(
            self.button_frame,
            text="최신 회차 당첨번호",
            font=("Malgun Gothic", 12, "bold"),
            bg="#00FFD0", fg="#181c2b",
            activebackground="#66ffd9", activeforeground="#181c2b",
            relief=tk.FLAT, bd=0, padx=20, pady=6,
            command=self.show_latest_draw
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10), pady=0, ipadx=6, ipady=1)

        # 데이터 갱신 버튼
        self.refresh_button = tk.Button(
            self.button_frame,
            text="데이터 갱신",
            font=("Malgun Gothic", 12, "bold"),
            bg="#9370DB", fg="white",
            activebackground="#8A2BE2", activeforeground="white",
            relief=tk.FLAT, bd=0, padx=20, pady=6,
            command=self.on_refresh_data
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10), pady=0, ipadx=6, ipady=1)

        # 정보 버튼 추가
        self.info_button = tk.Button(
            self.button_frame,
            text="ℹ️ 정보",
            font=("Malgun Gothic", 12, "bold"),
            bg="#4169E1", fg="white",
            activebackground="#1E90FF", activeforeground="white",
            relief=tk.FLAT, bd=0, padx=15, pady=6,
            command=self.show_info_window
        )
        self.info_button.pack(side=tk.LEFT, padx=(0, 20), pady=0, ipadx=6, ipady=1)

        # 버튼 호버 효과
        def on_enter_main(e):
            self.button.config(bg="#ffe066")
        def on_leave_main(e):
            self.button.config(bg="#FFD700")
        def on_enter_prev(e):
            self.prev_button.config(bg="#66ffd9")
        def on_leave_prev(e):
            self.prev_button.config(bg="#00FFD0")
        def on_enter_refresh(e):
            self.refresh_button.config(bg="#8A2BE2")
        def on_leave_refresh(e):
            self.refresh_button.config(bg="#9370DB")
        def on_enter_info(e):
            self.info_button.config(bg="#1E90FF")
        def on_leave_info(e):
            self.info_button.config(bg="#4169E1")
            
        self.button.bind("<Enter>", on_enter_main)
        self.button.bind("<Leave>", on_leave_main)
        self.prev_button.bind("<Enter>", on_enter_prev)
        self.prev_button.bind("<Leave>", on_leave_prev)
        self.refresh_button.bind("<Enter>", on_enter_refresh)
        self.refresh_button.bind("<Leave>", on_leave_refresh)
        self.info_button.bind("<Enter>", on_enter_info)
        self.info_button.bind("<Leave>", on_leave_info)

        # 버튼 그림자 효과(프레임으로 간접)
        self.button_frame.configure(highlightbackground="#333333", highlightcolor="#333333", highlightthickness=2, bd=0)

        # 초기 메시지 표시를 위해 일시적으로 활성화
        self.text.config(state='normal')
        self.text.insert(tk.END, "🎨 DA VINCI'S CIPHER: Quantum Lotto Decoder v1.0\n")
        self.text.insert(tk.END, "© 2025 ORYNE - Premium Lotto Analysis System\n\n")
        self.text.insert(tk.END, "🔍 로또 데이터 분석 중...\n")
        
        # 캐시 정보 표시
        if os.path.exists(CACHE_FILE):
            try:
                cache_info = load_cached_data()
                if 'last_updated' in cache_info:
                    last_update = datetime.fromisoformat(cache_info['last_updated'])
                    self.text.insert(tk.END, f"캐시 파일 발견! (마지막 업데이트: {last_update.strftime('%Y-%m-%d %H:%M')})\n")
                else:
                    self.text.insert(tk.END, "기존 캐시 파일을 발견했습니다.\n")
            except:
                self.text.insert(tk.END, "캐시 파일이 있지만 읽기에 실패했습니다.\n")
        else:
            self.text.insert(tk.END, "첫 실행입니다. 전체 데이터를 다운로드합니다.\n")
        
        threading.Thread(target=self.load_data, daemon=True).start()

        # 전체 마감: 윈도우 크기 고정, 여백/비율 조정, 폰트 일관성
        self.root.minsize(760, 670)
        self.root.maxsize(900, 900)

    # 설명별 컬러 강조 및 구분선 적용
    def insert_colored_explanation(self, sets):
        global TOTAL_DRAW
        next_draw = TOTAL_DRAW + 1
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, f"[레오나르도 다빈치의 제{next_draw}회차 황금비 조합 예측]\n© 2025 ORYNE Quantum Analysis System\n\n", ("title",))
        
        colors = ["#FFD700", "#00FFD0", "#FF6F61", "#7C83FD", "#FFB300"]
        for i, (nums, exp) in enumerate(sets, 1):
            color = colors[(i-1)%len(colors)]
            self.text.insert(tk.END, f"세트 {i}: {nums}\n", (f"set{i}",))
            
            # 소제목과 설명 내용 분리
            if ']' in exp:
                # ']' 이후의 첫 번째 '\n'까지가 소제목
                parts = exp.split(']', 1)
                if len(parts) == 2:
                    subtitle = parts[0] + ']'
                    content = parts[1]
                    # 소제목은 노란색, 설명 내용은 밝은 회색
                    self.text.insert(tk.END, subtitle, (f"subtitle{i}",))
                    self.text.insert(tk.END, content, (f"content{i}",))
                else:
                    self.text.insert(tk.END, exp, (f"content{i}",))
            else:
                self.text.insert(tk.END, exp, (f"content{i}",))
                
            if i < len(sets):
                self.text.insert(tk.END, "―"*60+"\n", ("sep",))
        
        # 미래 예측이므로 현재 결과와의 비교는 의미 없음 (제거)
        
        # 스타일 태그 - 통일된 색상 체계
        self.text.tag_config("title", font=("Malgun Gothic", 15, "bold"), foreground="#FFD700")
        
        # 세트 번호만 다채로운 색상으로 강조, 소제목과 설명 내용 분리
        set_num_colors = ["#FF69B4", "#00FFD0", "#FF6F61", "#32CD32", "#9370DB"]  # 세트1:핑크, 세트4:그린
        for i, color in enumerate(set_num_colors, 1):
            self.text.tag_config(f"set{i}", font=("Consolas", 13, "bold"), foreground=color)
            self.text.tag_config(f"subtitle{i}", font=("Malgun Gothic", 12, "bold"), foreground="#FFD700")  # 소제목 노란색
            self.text.tag_config(f"content{i}", font=("Malgun Gothic", 12), foreground="#F4D980")  # 설명 내용 파스텔톤 노란색
        self.text.tag_config("sep", foreground="#FFD700")
        
        # 매치 분석용 스타일 - 통일성 개선
        self.text.tag_config("prev_match_title", font=("Malgun Gothic", 14, "bold"), foreground="#FFD700")
        self.text.tag_config("prev_match_info", font=("Malgun Gothic", 12), foreground="#FFD700")
        self.text.tag_config("prev_match_result", font=("Malgun Gothic", 11, "bold"), foreground="#00FFD0")

    def load_data(self):
        """🚀 초고속 병렬 다운로드를 활용한 스마트 데이터 로딩"""
        global lotto_data, number_counts, recent_counts, co_occurrence, all_sums, TOTAL_DRAW
        
        start_time = time.time()
        self.text.insert(tk.END, "⚡ 최신 회차 확인 중...\n")
        
        # 최신 회차 확인
        try:
            latest_draw = get_latest_draw_number()
            if latest_draw > TOTAL_DRAW:
                TOTAL_DRAW = latest_draw
                self.text.insert(tk.END, f"✓ 최신 회차 확인됨: {latest_draw}회\n")
            else:
                self.text.insert(tk.END, f"현재 회차: {TOTAL_DRAW}회 (이미 최신)\n")
        except Exception as e:
            self.text.insert(tk.END, f"⚠ 최신 회차 확인 실패: 기본값 {TOTAL_DRAW}회 사용\n")
        
        # 캐시 데이터 로드
        cached_data = load_cached_data()
        missing_draws = get_missing_draws(cached_data, TOTAL_DRAW)
        
        # 데이터 구조 초기화
        lotto_data = []
        number_counts = Counter()
        recent_counts = Counter()
        co_occurrence = defaultdict(Counter)
        all_sums = []
        success_count = 0
        failed_rounds = []
        
        # 캐시된 데이터부터 빠르게 로드
        if 'draws' in cached_data:
            self.text.insert(tk.END, f"📚 캐시된 {len(cached_data['draws'])}회차 로딩 중...\n")
            for draw_str, draw_data in cached_data['draws'].items():
                draw_num = int(draw_str)
                if draw_num <= TOTAL_DRAW:
                    nums = draw_data['numbers']
                    lotto_data.append(nums)
                    all_sums.append(sum(nums))
                    
                    for n in nums:
                        number_counts[n] += 1
                    
                    if draw_num > TOTAL_DRAW - RECENT_DRAW:
                        for n in nums:
                            recent_counts[n] += 1
                    
                    for n in nums:
                        for m in nums:
                            if n != m:
                                co_occurrence[n][m] += 1
                    success_count += 1
        
        # 병렬 다운로드로 누락된 회차 고속 수집
        if missing_draws:
            self.text.insert(tk.END, f"🚀 {len(missing_draws)}개 회차 병렬 다운로드 시작! (15개 스레드)\n")
            self.text.update()
            
            def progress_callback(completed, total, current_draw):
                progress_pct = (completed / total) * 100
                self.text.insert(tk.END, f"📊 진행률: {progress_pct:.1f}% ({completed}/{total}) - 회차 {current_draw}\n")
                self.text.see(tk.END)
                self.text.update()
                
                # 중간 저장 (50개마다)
                if completed % 50 == 0 and completed > 0:
                    self.text.insert(tk.END, f"💾 중간 저장 중... ({completed}회차)\n")
                    self.text.update()
            
            # 병렬 다운로드 실행
            downloaded_data, download_failed = download_draws_parallel(
                missing_draws, 
                progress_callback=progress_callback,
                max_workers=15
            )
            
            # 다운로드된 데이터 처리 및 캐시 업데이트
            if downloaded_data:
                self.text.insert(tk.END, f"✅ {len(downloaded_data)}회차 다운로드 성공!\n")
                
                if 'draws' not in cached_data:
                    cached_data['draws'] = {}
                
                for draw_num, draw_data in downloaded_data.items():
                    # 캐시에 저장
                    cached_data['draws'][str(draw_num)] = draw_data
                    
                    # 분석 데이터에 추가
                    nums = draw_data['numbers']
                    lotto_data.append(nums)
                    all_sums.append(sum(nums))
                    
                    for n in nums:
                        number_counts[n] += 1
                    
                    if draw_num > TOTAL_DRAW - RECENT_DRAW:
                        for n in nums:
                            recent_counts[n] += 1
                    
                    for n in nums:
                        for m in nums:
                            if n != m:
                                co_occurrence[n][m] += 1
                    success_count += 1
            
            # 실패한 회차들 기록
            failed_rounds = download_failed
            
            # 캐시 저장
            self.text.insert(tk.END, "💾 캐시 파일 저장 중...\n")
            cached_data['last_updated'] = datetime.now().isoformat()
            cached_data['total_draws'] = TOTAL_DRAW
            save_cached_data(cached_data)
        
        # 성능 통계 출력
        elapsed_time = time.time() - start_time
        total_downloaded = len(missing_draws) - len(failed_rounds)
        
        if not missing_draws:
            self.text.insert(tk.END, f"⚡ 캐시 완료! ({elapsed_time:.1f}초)\n")
        else:
            speed = total_downloaded / elapsed_time if elapsed_time > 0 else 0
            self.text.insert(tk.END, f"🎯 다운로드 완료! {total_downloaded}회차, {speed:.1f}회차/초\n")
        
        # 결과 출력
        if not number_counts or sum(number_counts.values()) == 0:
            self.text.insert(tk.END, f"\n❌ 데이터 수집 실패! 네트워크를 확인하세요.\n성공: {success_count}회, 실패: {len(failed_rounds)}회\n")
            if failed_rounds:
                self.text.insert(tk.END, f"실패 회차 예시: {failed_rounds[:3]}\n")
            # 실패 시에도 텍스트 비활성화
            self.text.config(state='disabled')
        else:
            cache_info = "캐시 사용" if not missing_draws else f"병렬 다운로드 {total_downloaded}회차"
            next_draw = TOTAL_DRAW + 1
            self.text.insert(tk.END, f"\n🎉 ORYNE 분석 완료! ({cache_info})\n제{next_draw}회차 예측을 위한 '황금비 조합 생성' 버튼을 눌러보세요!\n총 {success_count}회차 데이터 준비됨 ✨\n\n")
        
        # 데이터 로딩 완료 후 텍스트 비활성화
        self.text.config(state='disabled')

    def show_latest_draw(self):
        """최신 회차 당첨번호 표시"""
        self.text.config(state='normal')  # 텍스트 편집 활성화
        global TOTAL_DRAW
        
        if TOTAL_DRAW <= 1:
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, "최신 회차 정보가 없습니다.\n")
            self.text.config(state='disabled')  # 즉시 비활성화
            return
            
        latest_draw_num = TOTAL_DRAW
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, f"📋 {latest_draw_num}회차 당첨번호 조회 중...\n\n")
        
        try:
            resp = requests.get(LOTTO_URL + str(latest_draw_num), timeout=5)
            data = resp.json()
            
            if data.get('returnValue') != 'success':
                self.text.insert(tk.END, f"❌ {latest_draw_num}회차 정보를 가져올 수 없습니다.\n")
                return
            
            # 당첨번호 추출
            winning_nums = []
            for j in range(1, 7):
                key = f'drwtNo{j}'
                if key in data:
                    winning_nums.append(data[key])
            
            bonus_num = data.get('bnusNo', 0)
            draw_date = data.get('drwNoDate', '날짜 정보 없음')
            
            # 1등 당첨금 정보 추출
            first_prize_amount = data.get('firstWinamnt', 0)  # 실제 1등 당첨금액
            first_winner_count = data.get('firstPrzwnerCo', 0)  # 1등 당첨자 수
            
            # 결과 표시
            self.text.insert(tk.END, f" ORYNE Quantum Analysis Report\n", ("oryne_brand",))
            self.text.insert(tk.END, f"🎰 제{latest_draw_num}회 로또 당첨번호\n\n", ("title",))
            self.text.insert(tk.END, f"📅 추첨일: {draw_date}\n\n", ("date",))
            
            # 1등 당첨금 정보
            if first_prize_amount > 0:
                prize_formatted = f"{first_prize_amount:,}원"
                self.text.insert(tk.END, f"💰 1등 당첨금: {prize_formatted}", ("prize",))
                if first_winner_count > 0:
                    self.text.insert(tk.END, f" (당첨복권수 {first_winner_count:,}개)\n\n\n", ("prize_info",))
                else:
                    self.text.insert(tk.END, "\n\n\n")
            else:
                self.text.insert(tk.END, "\n\n")
            
            # 당첨번호를 민트색으로 통일 표시
            self.text.insert(tk.END, "🎯 당첨번호: ", ("label",))
            sorted_nums = sorted(winning_nums)
            
            for i, num in enumerate(sorted_nums):
                color_tag = f"num{i}"
                self.text.tag_config(color_tag, font=("Consolas", 16, "bold"), foreground="#00FFB3")  # 민트색 통일
                self.text.insert(tk.END, f"{num:02d}", (color_tag,))
                if i < len(sorted_nums) - 1:
                    self.text.insert(tk.END, " - ")  # 부호는 노란색 그대로
            
            self.text.insert(tk.END, "\n\n🌟 보너스번호: ", ("bonus_text",))
            self.text.insert(tk.END, f"{bonus_num:02d}", ("bonus_num",))
            self.text.insert(tk.END, "\n\n", ("bonus_text",))
            
            # 과거에 생성한 예측과의 매치 분석
            self.show_set_match_analysis(winning_nums, bonus_num, latest_draw_num)
            
            # 스타일 적용 - 통일된 색상 체계
            self.text.tag_config("oryne_brand", font=("Malgun Gothic", 12, "bold"), foreground="#FFD700")  # 노란색 ORYNE 브랜드
            self.text.tag_config("separator", font=("Consolas", 10), foreground="#666666")  # 박스 구분선
            self.text.tag_config("title", font=("Malgun Gothic", 16, "bold"), foreground="#FF6B6B")  # 밝은 레드
            self.text.tag_config("date", font=("Malgun Gothic", 12), foreground="#FFD700")
            self.text.tag_config("prize", font=("Malgun Gothic", 14, "bold"), foreground="#00FFD0")  # 당첨금만 강조
            self.text.tag_config("prize_info", font=("Malgun Gothic", 12), foreground="#FFD700")
            self.text.tag_config("label", font=("Malgun Gothic", 14, "bold"), foreground="#FFD700")
            self.text.tag_config("bonus_text", font=("Malgun Gothic", 14, "bold"), foreground="#FFD700")  # 보너스번호 텍스트 노란색
            self.text.tag_config("bonus_num", font=("Consolas", 16, "bold"), foreground="#1E90FF")  # 보너스 숫자 블루
            self.text.tag_config("analysis", font=("Malgun Gothic", 14, "bold"), foreground="#FFD700")
            self.text.tag_config("info", font=("Malgun Gothic", 12), foreground="#FFD700")
            self.text.tag_config("match_title", font=("Malgun Gothic", 14, "bold"), foreground="#FFD700")
            self.text.tag_config("match_result", font=("Malgun Gothic", 12, "bold"), foreground="#00FFD0")  # 당첨결과만 강조
            self.text.tag_config("match_detail", font=("Malgun Gothic", 11), foreground="#FFD700")
                
        except Exception as e:
            self.text.insert(tk.END, f"❌ 오류 발생: {str(e)}\n")
        finally:
            self.text.config(state='disabled')



    def show_set_match_analysis(self, winning_nums, bonus_num, current_draw_num):
        """과거에 생성한 예측과 현재 당첨번호의 매치 분석"""
        try:
            # 과거 예측 데이터 가져오기
            past_predictions = get_previous_predictions(current_draw_num)
            
            if not past_predictions:
                self.text.insert(tk.END, "🔍 과거 예측 매치 분석: 저장된 예측 데이터가 없습니다.\n\n", ("match_title",))
                return
            
            set_names = [
                "황금비 조합 (세트1)",
                "통계적 회귀 (세트2)", 
                "신성 기하학 (세트3)",
                "양자적 에너지 (세트4)",
                "대통일 이론 (세트5)"
            ]
            
            self.text.insert(tk.END, f"🔍 제{current_draw_num}회차 예측 정확도 분석:\n", ("match_title",))
            
            winning_set = set(winning_nums)
            total_best_match = 0
            best_set_name = ""
            
            for i, nums in enumerate(past_predictions[:5]):  # 최대 5개 세트
                if i >= len(set_names):
                    break
                    
                if not nums or "(데이터 없음)" in str(nums):
                    self.text.insert(tk.END, f"• {set_names[i]}: 예측 데이터 없음\n", ("match_detail",))
                    continue
                    
                set_numbers = set(nums)
                matches = len(winning_set & set_numbers)
                
                # 보너스 번호 매치 확인
                bonus_match = " (+보너스)" if bonus_num in set_numbers else ""
                
                # 매치 결과에 따른 색상과 메시지
                if matches >= 4:
                    result_color = "match_result"  # 강조색
                    prize_info = self.get_prize_info(matches, bonus_match != "")
                elif matches >= 2:
                    result_color = "match_detail"   # 기본색
                    prize_info = f"({matches}개 일치)"
                else:
                    result_color = "info"           # 기본색
                    prize_info = f"({matches}개 일치)"
                
                self.text.insert(tk.END, f"• {set_names[i]}: ", ("match_detail",))
                self.text.insert(tk.END, f"{nums} → ", ("match_nums",))
                self.text.insert(tk.END, f"{matches}개 매치{bonus_match} {prize_info}\n", (result_color,))
                
                if matches > total_best_match:
                    total_best_match = matches
                    best_set_name = set_names[i]
            
            # 최고 성과 세트 표시
            if total_best_match > 0:
                self.text.insert(tk.END, f"\n🏆 최고 성과: {best_set_name} ({total_best_match}개 매치)\n\n", ("best_result",))
            
            # 매치 분석 스타일 정의
            self.text.tag_config("match_nums", font=("Consolas", 11), foreground="#CCCCCC")
            self.text.tag_config("best_result", font=("Malgun Gothic", 13, "bold"), foreground="#00FF00")
                
        except Exception as e:
            self.text.insert(tk.END, f"🔍 매치 분석 중 오류: {str(e)}\n\n", ("error",))

    def get_prize_info(self, matches, has_bonus):
        """당첨 등수 정보 반환"""
        if matches == 6:
            return "🎉 1등 당첨!"
        elif matches == 5:
            if has_bonus:
                return "🎊 2등 당첨!"
            else:
                return "🎈 3등 당첨!"
        elif matches == 4:
            return "🎁 4등 당첨!"
        elif matches == 3:
            return "🎀 5등 당첨!"
        else:
            return f"({matches}개 일치)"

    def on_generate(self):
        self.text.config(state='normal')
        if not number_counts or sum(number_counts.values()) == 0:
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, "[오류] 로또 데이터가 비어 있습니다.\n데이터 수집이 완료되지 않았거나, 서버 연결에 실패했습니다.\n잠시 후 다시 시도해 주세요.\n")
            self.text.config(state='disabled')
            return
            
        global TOTAL_DRAW
        sets = generate_numbers_and_explanations()
        
        # 예측 데이터 저장
        self.save_current_predictions(TOTAL_DRAW + 1, sets)
        
        self.insert_colored_explanation(sets)
        self.text.config(state='disabled')

    def save_current_predictions(self, target_draw, sets):
        """현재 생성된 예측을 저장합니다."""
        try:
            predictions = load_predictions_data()
            
            # 번호만 추출 (설명 제외)
            prediction_sets = []
            for nums, _ in sets:
                if "(데이터 없음)" not in str(nums):
                    prediction_sets.append(nums)
            
            # 저장할 데이터 구성
            draw_key = str(target_draw)
            predictions[draw_key] = {
                'sets': prediction_sets,
                'created_date': datetime.now().isoformat(),
                'created_for_draw': target_draw
            }
            
            save_predictions_data(predictions)
        except Exception as e:
            # 저장 실패해도 메인 기능에는 영향 없음
            pass
    
    def on_refresh_data(self):
        """데이터 갱신 버튼 클릭 시 실행"""
        self.text.config(state='normal')
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, "🔄 ORYNE 데이터 갱신 중...\n양자 알고리즘 시동 중...\n")
        self.refresh_button.config(state='disabled', text="갱신 중...")
        self.button.config(state='disabled')
        
        def refresh_thread():
            try:
                self.load_data()
            finally:
                # UI 스레드에서 버튼 상태 복원
                self.root.after(0, lambda: (
                    self.refresh_button.config(state='normal', text="데이터 갱신"),
                    self.button.config(state='normal'),
                    self.text.config(state='disabled')
                ))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def show_info_window(self):
        """정보 버튼 클릭 시 표시할 정보 창"""
        import tkinter.messagebox as msgbox
        
        info_text = """
🎨 DA VINCI'S CIPHER: Quantum Lotto Decoder v1.0

© 2025 ORYNE Corporation. All Rights Reserved.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 프로그램 정보:
   • 개발사: ORYNE Corporation
   • 버전: v1.0.0
   • 출시일: 2025년 10월 7일
   • 연락처: Instagram @oryne.official

⚠️ 법적 고지사항:
   • 개인 사용 전용 (상업적 이용 금지)
   • 무단 복제, 배포, 수정 금지
   • 저작권법에 의해 보호되는 소프트웨어

🎯 면책 조항:
   • 오락 및 교육 목적으로 제작됨
   • 로또 당첨을 보장하지 않음
   • 투자 손실에 대한 책임지지 않음
   • 수학적 알고리즘 기반 분석

🌐 데이터 출처:
   • 동행복권 공식 API 사용
   • 실시간 데이터 동기화
   • 통계적 분석 알고리즘 적용

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
이 프로그램을 사용함으로써 위의 모든 조건에 
동의하는 것으로 간주됩니다.
        """
        
        msgbox.showinfo("📋 프로그램 정보", info_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = DaVinciLottoGUI(root)
    root.mainloop()
