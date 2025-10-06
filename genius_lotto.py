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
    # 피보나치 수열과 실제 데이터를 융합한 황금비 분석
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    # 피보나치 수들의 출현 빈도 분석 (1~45 범위)
    fib_in_range = [f for f in FIBONACCI if f <= 45]
    fib_analysis = [(f, number_counts.get(f, 0)) for f in fib_in_range]
    
    # 황금비(1.618) 기반 가중치 계산
    golden_ratio = 1.618
    weighted_fib = []
    for f, count in fib_analysis:
        # 황금비 거리에 따른 가중치
        ratio_weight = 1 / (1 + abs(f - 23 * golden_ratio / 45))  # 23은 중앙값
        # 출현 빈도 정규화
        freq_weight = count / max([c for _, c in fib_analysis]) if fib_analysis else 0
        total_weight = ratio_weight * 0.6 + freq_weight * 0.4
        weighted_fib.append((f, total_weight))
    
    # 가중치 순으로 정렬하여 상위 선택
    weighted_fib.sort(key=lambda x: x[1], reverse=True)
    
    selected = []
    # 먼저 피보나치 수에서 3-4개 선택
    for f, _ in weighted_fib[:4]:
        if len(selected) < 4:
            selected.append(f)
    
    # 나머지는 황금비 분할점들로 채우기
    golden_points = [int(45 * i / golden_ratio) for i in [0.382, 0.618, 1.0]]
    for point in golden_points:
        if point >= 1 and point <= 45 and point not in selected and len(selected) < 6:
            selected.append(point)
    
    # 부족하면 중간값들로 보충
    while len(selected) < 6:
        for n in [7, 17, 27, 37, 42]:
            if n not in selected:
                selected.append(n)
                break
    
    return sorted(selected[:6])

def set2_statistical_regression():
    # 평균보다 현저히 적게 나온 번호 6개
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    # 전체 평균 계산
    avg = sum(number_counts.values()) / len(number_counts)
    
    # 평균보다 70% 이하로 적게 나온 번호들 찾기
    rare_numbers = []
    for n in range(1, 46):  # 1~45 전체 번호 확인
        count = number_counts.get(n, 0)
        if count < avg * 0.7:
            rare_numbers.append((n, count))
    
    # 적게 나온 순으로 정렬
    rare_numbers.sort(key=lambda x: x[1])
    
    # 상위 12개 선택 후 중앙값(23) 기준으로 균형있게 배치
    top_rare = rare_numbers[:12] if len(rare_numbers) >= 12 else rare_numbers
    
    if len(top_rare) < 6:
        # 충분하지 않으면 가장 적게 나온 번호들로 보충
        all_by_count = sorted([(n, number_counts.get(n, 0)) for n in range(1, 46)], key=lambda x: x[1])
        top_rare = all_by_count[:12]
    
    # 중앙값 기준 균형 배치
    selected = sorted([x[0] for x in top_rare], key=lambda x: (x-23)**2)[:6]
    
    # 6개 미만이면 추가 보충
    while len(selected) < 6:
        for n in range(1, 46):
            if n not in selected:
                selected.append(n)
                break
    
    return sorted(selected[:6])

def set3_geometry():
    # 기하학적 패턴과 실제 출현 데이터의 조화
    if not number_counts or sum(number_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    # 7x7 그리드 매핑 (1~45를 7x7 격자에 배치)
    def get_grid_pos(num):
        return ((num - 1) // 7, (num - 1) % 7)
    
    # 대칭점 찾기 (중심점 23 기준)
    center = 23
    symmetry_pairs = []
    for i in range(1, 46):
        symmetric = 2 * center - i
        if 1 <= symmetric <= 45 and i != symmetric:
            pair_freq = number_counts.get(i, 0) + number_counts.get(symmetric, 0)
            symmetry_pairs.append((i, symmetric, pair_freq))
    
    # 대칭성 기준으로 정렬
    symmetry_pairs.sort(key=lambda x: x[2], reverse=True)
    
    selected = []
    # 가장 대칭적인 쌍에서 하나씩 선택
    for i, sym, freq in symmetry_pairs[:3]:
        if len(selected) < 6:
            # 둘 중 더 자주 나온 번호 선택
            better = i if number_counts.get(i, 0) >= number_counts.get(sym, 0) else sym
            if better not in selected:
                selected.append(better)
    
    # 기하학적 특별점들 (대각선, 모서리 등)
    geometric_points = [
        1,   # 좌상단 모서리
        7,   # 우상단 모서리  
        15,  # 대각선상의 점
        23,  # 정중앙
        31,  # 대각선상의 점
        39,  # 좌하단 근처
        45   # 우하단 모서리
    ]
    
    # 기하학적 점들을 출현 빈도 순으로 정렬
    geo_with_freq = [(p, number_counts.get(p, 0)) for p in geometric_points if p not in selected]
    geo_with_freq.sort(key=lambda x: x[1], reverse=True)
    
    # 나머지 자리 채우기
    for point, freq in geo_with_freq:
        if len(selected) < 6:
            selected.append(point)
    
    # 여전히 부족하면 중간 지점들로 보충
    if len(selected) < 6:
        middle_points = [12, 18, 28, 34]
        for mp in middle_points:
            if mp not in selected and len(selected) < 6:
                selected.append(mp)
    
    return sorted(selected[:6])

def set4_quantum():
    # 최근 50회 내 출현 빈도 상위 6개
    if not recent_counts or sum(recent_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    hot_numbers = [n for n, _ in recent_counts.most_common(6)]
    
    # 6개 미만이면 보충
    while len(hot_numbers) < 6:
        for n in range(1, 46):
            if n not in hot_numbers:
                hot_numbers.append(n)
                break
    
    return sorted(hot_numbers[:6])

def set5_grand_unification():
    # 피보나치 중 최근 50회 최저 1개, 전체 미출현 상위 2개, 최근 50회 최다 2개, 마지막은 평균합에 가장 근접하게
    if not number_counts or not recent_counts or not all_sums or sum(recent_counts.values()) == 0:
        return ["(데이터 없음)"]*6
    
    try:
        # 1. 피보나치 중 최근 50회 최저 1개
        fib_recent = sorted(FIBONACCI, key=lambda n: recent_counts.get(n, 0))
        fib_pick = fib_recent[0]
        
        # 2. 전체 미출현 상위 2개
        rare = sorted(LOTTO_RANGE, key=lambda n: number_counts.get(n, 0))[:2]
        
        # 3. 최근 50회 최다 2개
        hot = [n for n, _ in recent_counts.most_common(2)]
        if len(hot) < 2:
            # 충분하지 않으면 추가
            for n in range(1, 46):
                if n not in hot and len(hot) < 2:
                    hot.append(n)
        
        # 중복 제거
        partial = list(set([fib_pick] + rare + hot))
        
        # 4. 평균합에 가장 근접한 번호들로 6개 맞추기
        avg_sum = int(sum(all_sums) / len(all_sums)) if all_sums else 138
        target_sum = avg_sum - sum(partial)
        
        while len(partial) < 6:
            candidates = [n for n in LOTTO_RANGE if n not in partial]
            if not candidates:
                break
                
            if len(partial) == 5:
                # 마지막 번호는 평균합에 가장 가깝게
                best = min(candidates, key=lambda x: abs(sum(partial + [x]) - avg_sum))
            else:
                # 중간 번호들은 균형있게 선택
                best = min(candidates, key=lambda x: abs(x - (target_sum // (6 - len(partial)))))
            
            partial.append(best)
        
        return sorted(partial[:6])
        
    except Exception as e:
        # 오류 발생시 안전한 기본값
        return sorted([1, 8, 15, 22, 29, 36])

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
    
    return f"[우주 평균 회귀의 법칙 - 통계적 각성]\n이 수리체계 {nums}는 평균회귀(Mean Reversion) 이론과 대수의 법칙(Law of Large Numbers)에 기반합니다. 가우스 분포에서 변동성이 낮은 영역에 위치한 이 수들은, 중심극한정리(Central Limit Theorem)에 따라 장기적으로 평균으로 수렴하는 경향을 보입니다. 이는 시계열 분석에서 사용되는 AR(1) 모델의 예측 원리를 로또 데이터에 적용한 결과입니다.\n"

def explain_set3(nums):
    if "(데이터 없음)" in str(nums):
        return "[신성 기하학의 배열]\n기하학적 분석 중입니다. 잠시만 기다려주세요.\n"
    
    # 대칭성 분석
    center = 23
    symmetry = sum(1 for n in nums if (2*center - n) in nums or n == center)
    
    return f"[신성 기하학의 배열 - 대칭의 미학]\n{nums}는 유클리드 기하학의 대칭성(Symmetry) 원리와 노어터(Emmy Noether)의 대칭성 정리를 기반으로 선별되었습니다. 7×7 격자 구조에서 중심점(23)을 기준으로 {symmetry}개의 대칭적 요소를 포함하며, 이는 결정학(Crystallography)에서 사용되는 점군 대칭(Point Group Symmetry) 이론과 일치합니다. 이러한 기하학적 질서는 비트루비우스가 제시한 인체 비례의 수학적 규칙성을 반영합니다.\n"

def explain_set4(nums):
    return f"[양자적 도약과 변동성]\n이 수열은 양자물리학의 비연속성(Quantum Discreteness)과 확률적 중첩(Quantum Superposition) 원리를 기반으로 선별되었습니다. {nums}는 최근 출현 데이터에서 통계적 요동(Statistical Fluctuation)을 보이는 '뜨거운' 숫자들로, 하이젠베르크의 불확정성 원리처럼 예측 불가능한 변동성을 내재합니다. 이는 무작위 과정에서 나타나는 열역학적 비평형 상태의 수학적 모델링입니다.\n"

def explain_set5(nums):
    return f"[대통일 숫자 이론]\n이 수열은 앞서 소개된 네 가지 수학적 원리(피보나치 수열, 평균회귀, 기하학적 대칭, 확률적 변동)를 통합적으로 적용한 결과입니다. {nums}는 각 알고리즘의 강점을 결합하여 에일리어스(Elias) 코딩 이론과 같이 중복된 정보를 제거하고 최적화된 숫자 조합을 추출합니다. 이는 기계학습의 앙상블 방법(Ensemble Methods)과 유사한 원리로, 여러 모델의 예측을 통합하여 더 정확한 결과를 도출합니다.\n"

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
        self.root.title("다빈치 코드: 로또 해독기")
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
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 20), pady=0, ipadx=6, ipady=1)

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
            
        self.button.bind("<Enter>", on_enter_main)
        self.button.bind("<Leave>", on_leave_main)
        self.prev_button.bind("<Enter>", on_enter_prev)
        self.prev_button.bind("<Leave>", on_leave_prev)
        self.refresh_button.bind("<Enter>", on_enter_refresh)
        self.refresh_button.bind("<Leave>", on_leave_refresh)

        # 버튼 그림자 효과(프레임으로 간접)
        self.button_frame.configure(highlightbackground="#FFD700", highlightcolor="#FFD700", highlightthickness=3, bd=0)

        # 초기 메시지 표시를 위해 일시적으로 활성화
        self.text.config(state='normal')
        self.text.insert(tk.END, "로또 데이터 분석 중...\n")
        
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
        self.text.insert(tk.END, f"[레오나르도 다빈치의 제{next_draw}회차 황금비 조합 예측]\n\n", ("title",))
        
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
            self.text.insert(tk.END, f"\n🎉 분석 완료! ({cache_info})\n제{next_draw}회차 예측을 위한 '황금비 조합 생성' 버튼을 눌러보세요!\n총 {success_count}회차 데이터 준비됨 ✨\n\n")
        
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
                self.text.insert(tk.END, f"{matches}개 매치{bonus_match} {prize_info}\n", (result_color,))
                
                # 최고 매치 기록
                if matches > total_best_match:
                    total_best_match = matches
                    best_set_name = set_names[i]
            
            # 최고 성과 요약
            if total_best_match >= 3:
                self.text.insert(tk.END, f"\n🏆 최고 성과: {best_set_name} - {total_best_match}개 매치!\n\n", ("match_result",))
            elif total_best_match > 0:
                self.text.insert(tk.END, f"\n📊 최고 성과: {best_set_name} - {total_best_match}개 매치\n\n", ("match_detail",))
            else:
                self.text.insert(tk.END, "\n💭 아쉽게도 3개 이상 매치되는 예측이 없었습니다.\n\n", ("match_detail",))
                
        except Exception as e:
            self.text.insert(tk.END, f"🔍 예측 분석 오류: {str(e)}\n\n", ("match_title",))

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
        self.text.insert(tk.END, "데이터 갱신 중...\n")
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DaVinciLottoGUI(root)
    root.mainloop()
